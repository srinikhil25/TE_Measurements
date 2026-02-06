"""
Keithley Instrument Connection and Measurement Module

This module adapts the proven logic from the seebeck_system backend
for use inside the TE Measurements desktop application.

Responsibilities:
- Low-level connection to Keithley / PK160 instruments via VISA
- High-level Seebeck measurement loop (with phases)
- High-level resistivity / I-V measurement using 2401
- Threaded session manager for asynchronous Seebeck measurements
"""

from __future__ import annotations

import threading
import time
import logging
from dataclasses import dataclass
from typing import Optional, Dict, Any, List

import pyvisa  # type: ignore

from src.utils import Config
from src.models import MeasurementType


logger = logging.getLogger(__name__)


@dataclass
class InstrumentStatus:
    name: str
    connected: bool
    resource_name: Optional[str] = None
    error: Optional[str] = None


class Keithley2182A:
    """Nanovoltmeter (TEMF)"""

    def __init__(self, resource_name: str):
        self.resource_name = resource_name
        self.instrument = None
        self.connected = False

    def connect(self, rm: Optional[pyvisa.ResourceManager] = None) -> bool:
        if self.connected and self.instrument:
            try:
                self.disconnect()
            except Exception:
                pass

        try:
            if rm is None:
                rm = pyvisa.ResourceManager()
            self.instrument = rm.open_resource(self.resource_name)
            self.instrument.timeout = 20000
            self.connected = True
            logger.info("Connected to Keithley 2182A at %s", self.resource_name)
            return True
        except Exception as e:  # pragma: no cover - hardware specific
            error_str = str(e)
            logger.error("Failed to connect to Keithley 2182A: %s", error_str)
            if "VI_ERROR_ALLOC" in error_str or "-1073807300" in error_str:
                logger.error(
                    "VI_ERROR_ALLOC: Resource allocation failed. "
                    "Check for other processes using this instrument."
                )
            self.connected = False
            self.instrument = None
            return False

    def disconnect(self) -> None:
        if self.instrument:
            try:
                self.instrument.close()
            except Exception as e:  # pragma: no cover - best effort
                logger.warning("Error closing 2182A connection: %s", e)
            finally:
                self.instrument = None
                self.connected = False
                logger.info("Disconnected Keithley 2182A")

    def configure(self) -> bool:
        if not self.connected:
            return False
        self.instrument.write("*RST")
        self.instrument.write(":CONF:VOLT")
        self.instrument.write(":VOLT:DIGITS 8")
        self.instrument.write(":VOLT:NPLC 5")
        logger.info("Configured Keithley 2182A")
        return True

    def read_voltage(self) -> Optional[float]:
        if not self.connected:
            return None
        try:
            response = self.instrument.query(":READ?")
            value_str = response.split(",")[0].split("_")[0].strip()
            value = float(value_str)
            logger.info("2182A Voltage: %s", value)
            return value
        except Exception as e:  # pragma: no cover - hardware specific
            logger.error("Failed to read voltage from 2182A: %s", e)
            return None


class PK160:
    """Current source for Seebeck heating profile"""

    def __init__(self, resource_name: str):
        self.resource_name = resource_name
        self.instrument = None
        self.connected = False

    def connect(self, rm: Optional[pyvisa.ResourceManager] = None) -> bool:
        if self.connected and self.instrument:
            try:
                self.disconnect()
            except Exception:
                pass

        try:
            if rm is None:
                rm = pyvisa.ResourceManager()
            self.instrument = rm.open_resource(self.resource_name)
            self.instrument.timeout = 20000
            self.connected = True
            logger.info("Connected to PK160 at %s", self.resource_name)
            return True
        except Exception as e:  # pragma: no cover
            error_str = str(e)
            logger.error("Failed to connect to PK160: %s", error_str)
            if "VI_ERROR_ALLOC" in error_str or "-1073807300" in error_str:
                logger.error(
                    "VI_ERROR_ALLOC: Resource allocation failed. "
                    "Check for other processes using this instrument."
                )
            self.connected = False
            self.instrument = None
            return False

    def disconnect(self) -> None:
        if self.instrument:
            try:
                self.instrument.close()
            except Exception as e:  # pragma: no cover
                logger.warning("Error closing PK160 connection: %s", e)
            finally:
                self.instrument = None
                self.connected = False
                logger.info("Disconnected PK160")

    def initialize(self) -> bool:
        if not self.connected:
            return False
        # Initialization sequence as in legacy code
        self.instrument.write("#1 REN")
        self.instrument.write("#1 VCN 100")
        self.instrument.write("#1 OCP 100")
        self.instrument.write("#1 SW1")
        logger.info("Initialized PK160")
        return True

    def set_current(self, value: float) -> bool:
        if not self.connected:
            return False
        self.instrument.write(f"#1 ISET{value}")
        logger.info("PK160 set current: %s", value)
        return True

    def output_off(self) -> bool:
        if not self.connected:
            return False
        self.instrument.write("#1 SW0")
        logger.info("PK160 output off")
        return True


class Keithley2700:
    """DMM / scanner for temperature channels"""

    def __init__(self, resource_name: str):
        self.resource_name = resource_name
        self.instrument = None
        self.connected = False

    def connect(self, rm: Optional[pyvisa.ResourceManager] = None) -> bool:
        if self.connected and self.instrument:
            try:
                self.disconnect()
            except Exception:
                pass

        try:
            if rm is None:
                rm = pyvisa.ResourceManager()
            self.instrument = rm.open_resource(self.resource_name)
            self.instrument.timeout = 20000
            self.connected = True
            logger.info("Connected to Keithley 2700 at %s", self.resource_name)
            return True
        except Exception as e:  # pragma: no cover
            error_str = str(e)
            logger.error("Failed to connect to Keithley 2700: %s", error_str)
            if "VI_ERROR_ALLOC" in error_str or "-1073807300" in error_str:
                logger.error(
                    "VI_ERROR_ALLOC: Resource allocation failed. "
                    "Check for other processes using this instrument."
                )
            self.connected = False
            self.instrument = None
            return False

    def disconnect(self) -> None:
        if self.instrument:
            try:
                self.instrument.close()
            except Exception as e:  # pragma: no cover
                logger.warning("Error closing 2700 connection: %s", e)
            finally:
                self.instrument = None
                self.connected = False
                logger.info("Disconnected Keithley 2700")

    def configure_temperature(self, channel: int = 101, nplc: float = 1.0) -> bool:
        if not self.connected:
            return False
        self.instrument.write("*RST")
        time.sleep(0.1)
        self.instrument.write(f":ROUT:CLOS (@{channel})")
        self.instrument.write(":CONF:TEMP")
        self.instrument.write(":UNIT:TEMP C")
        self.instrument.write(":TEMP:TRAN TC")
        self.instrument.write(":TEMP:TC:TYPE K")
        self.instrument.write(":TEMP:TC:RJUN:RSEL EXT")
        self.instrument.write(f":TEMP:NPLC {nplc}")
        logger.info("Configured Keithley 2700 for temperature on channel %s", channel)
        return True

    def read_temperature(self, channel: int = 101) -> Optional[float]:
        if not self.connected:
            return None
        try:
            self.instrument.write(f":ROUT:CLOS (@{channel})")
            time.sleep(0.1)
            response = self.instrument.query(":READ?")
            value_str = response.split(",")[0].split("_")[0].strip()
            value = float(value_str)
            logger.info("2700 Measurement on channel %s: %s", channel, value)
            return value
        except Exception as e:  # pragma: no cover
            logger.error("Failed to take measurement on 2700: %s", e)
            return None


class Keithley2401:
    """SourceMeter for I-V and resistivity measurements."""

    def __init__(self, resource_name: str):
        self.resource_name = resource_name
        self.instrument = None
        self.connected = False

    def connect(self, rm: Optional[pyvisa.ResourceManager] = None) -> bool:
        if self.connected and self.instrument:
            try:
                self.disconnect()
            except Exception:
                pass
        try:
            if rm is None:
                rm = pyvisa.ResourceManager()
            self.instrument = rm.open_resource(self.resource_name)
            self.instrument.timeout = 20000
            self.connected = True
            logger.info("Connected to Keithley 2401 at %s", self.resource_name)
            return True
        except Exception as e:  # pragma: no cover
            error_str = str(e)
            logger.error("Failed to connect to Keithley 2401: %s", error_str)
            if "VI_ERROR_ALLOC" in error_str or "-1073807300" in error_str:
                logger.error(
                    "VI_ERROR_ALLOC: Resource allocation failed. "
                    "Check for other processes using this instrument."
                )
            self.connected = False
            self.instrument = None
            return False

    def disconnect(self) -> None:
        if self.instrument:
            try:
                self.instrument.close()
            except Exception as e:  # pragma: no cover
                logger.warning("Error closing 2401 connection: %s", e)
            finally:
                self.instrument = None
                self.connected = False
                logger.info("Disconnected Keithley 2401")

    def configure_voltage_source(self, voltage_limit: float = 1.0, current_limit: float = 0.1) -> bool:
        if not self.connected:
            return False
        try:
            self.instrument.write("*RST")
            time.sleep(0.5)
            self.instrument.write(":SOUR:FUNC VOLT")
            self.instrument.write(":SOUR:VOLT:LEV 0")
            self.instrument.write(f":SOUR:VOLT:RANG {abs(voltage_limit)}")
            self.instrument.write(f":SENS:CURR:PROT {abs(current_limit)}")
            self.instrument.write(":SENS:FUNC 'CURR'")
            self.instrument.write(":SENS:CURR:RANG:AUTO ON")
            self.instrument.write(":FORM:ELEM CURR, VOLT")
            logger.info(
                "Configured 2401 as voltage source (V_limit=%s, I_limit=%s)",
                voltage_limit,
                current_limit,
            )
            return True
        except Exception as e:  # pragma: no cover
            logger.error("Failed to configure 2401: %s", e)
            return False

    def output_on(self) -> bool:
        if not self.connected:
            return False
        try:
            self.instrument.write(":OUTP ON")
            logger.info("2401 output ON")
            return True
        except Exception as e:  # pragma: no cover
            logger.error("Failed to turn on 2401 output: %s", e)
            return False

    def output_off(self) -> bool:
        if not self.connected:
            return False
        try:
            self.instrument.write(":OUTP OFF")
            logger.info("2401 output OFF")
            return True
        except Exception as e:  # pragma: no cover
            logger.error("Failed to turn off 2401 output: %s", e)
            return False

    def set_voltage(self, voltage: float) -> bool:
        """Set the output voltage level"""
        if not self.connected:
            return False
        try:
            self.instrument.write(f":SOUR:VOLT:LEV {voltage}")
            logger.info("2401 set voltage: %s V", voltage)
            return True
        except Exception as e:  # pragma: no cover
            logger.error("Failed to set voltage on 2401: %s", e)
            return False

    def read_measurement(self) -> Optional[Dict[str, float]]:
        if not self.connected:
            return None
        try:
            self.instrument.write(":INIT")
            time.sleep(0.1)
            response = self.instrument.query(":FETCH?")
            values = response.strip().split(",")
            if len(values) < 2:
                return None
            val1 = float(values[0])
            val2 = float(values[1])
            # Heuristic: larger magnitude is treated as voltage
            if abs(val1) > abs(val2) or abs(val1) < 0.001:
                voltage = val1
                current = val2
            else:
                current = val1
                voltage = val2
            resistance = voltage / current if abs(current) > 1e-12 else None
            return {"voltage": voltage, "current": current, "resistance": resistance}
        except Exception as e:  # pragma: no cover
            logger.error("Failed to read measurement from 2401: %s", e)
            return None


class SeebeckSystem:
    """Aggregates all instruments used for Seebeck + resistivity measurement."""

    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()
        self.rm = pyvisa.ResourceManager()
        self.k2182a = Keithley2182A(self.config.addr_2182a)
        self.k2700 = Keithley2700(self.config.addr_2700)
        self.pk160 = PK160(self.config.addr_pk160)
        self.k2401 = Keithley2401(self.config.addr_2401)
        self.connected = False

    def connect_all(self) -> Dict[str, InstrumentStatus]:
        """Connect to all instruments used for Seebeck / resistivity."""
        statuses: Dict[str, InstrumentStatus] = {}

        def _wrap(name: str, ok: bool, resource: str, error: Optional[str] = None):
            statuses[name] = InstrumentStatus(
                name=name, connected=ok, resource_name=resource, error=error
            )

        # 2182A
        ok_2182a = self.k2182a.connect(self.rm)
        _wrap("2182A", ok_2182a, self.config.addr_2182a, None if ok_2182a else "connect failed")

        # 2700
        ok_2700 = self.k2700.connect(self.rm)
        _wrap("2700", ok_2700, self.config.addr_2700, None if ok_2700 else "connect failed")

        # PK160
        ok_pk160 = self.pk160.connect(self.rm)
        _wrap("PK160", ok_pk160, self.config.addr_pk160, None if ok_pk160 else "connect failed")

        # 2401
        ok_2401 = self.k2401.connect(self.rm)
        _wrap("2401", ok_2401, self.config.addr_2401, None if ok_2401 else "connect failed")

        self.connected = all(s.connected for s in statuses.values())
        if not self.connected:
            logger.error("Not all instruments connected successfully: %s", statuses)
        return statuses

    def disconnect_all(self) -> None:
        self.k2182a.disconnect()
        self.k2700.disconnect()
        self.pk160.disconnect()
        self.k2401.disconnect()
        self.connected = False

    def initialize_seebeck_instruments(self) -> None:
        """Configure instruments for Seebeck measurement (voltage + temperatures + current source)."""
        self.k2182a.configure()
        # Configure two temperature channels; exact IDs may be adjusted as needed
        self.k2700.configure_temperature(channel=102)
        self.k2700.configure_temperature(channel=104)
        self.pk160.initialize()

    def set_heater_current(self, value: float) -> None:
        self.pk160.set_current(value)

    def heater_off(self) -> None:
        self.pk160.output_off()

    def measure_seebeck_point(self, temp1_channel: int = 102, temp2_channel: int = 104) -> Dict[str, Optional[float]]:
        """Read one Seebeck data point (TEMF + two temperatures)."""
        temf = self.k2182a.read_voltage()
        temp1 = self.k2700.read_temperature(channel=temp1_channel)
        temp2 = self.k2700.read_temperature(channel=temp2_channel)
        return {
            "TEMF [mV]": temf * 1000.0 if temf is not None else None,
            "Temp1 [oC]": temp1,
            "Temp2 [oC]": temp2,
        }

    def measure_resistivity_single(
        self,
        length: float,
        width: float,
        thickness: float,
        voltage: Optional[float] = None,
        current: Optional[float] = None,
    ) -> Dict[str, Optional[float]]:
        """
        Single-point resistivity measurement using 2401.
        Mirrors the algorithm in seebeck_system.
        """
        if not self.k2401.connected:
            logger.error("Keithley 2401 not connected")
            return {
                "voltage": None,
                "current": None,
                "resistance": None,
                "resistivity": None,
                "conductivity": None,
                "error": "Keithley 2401 not connected",
            }

        try:
            if voltage is not None:
                self.k2401.configure_voltage_source(
                    voltage_limit=abs(voltage) * 1.2, current_limit=0.1
                )
                # In a full implementation we would set the source level here
            else:
                applied_current = current if current is not None else 0.01
                # For now, we only configure as in legacy; current-level setting can be added.
                self.k2401.configure_voltage_source(
                    voltage_limit=1.0, current_limit=abs(applied_current) * 1.2
                )

            self.k2401.output_on()
            time.sleep(0.5)
            measurement = self.k2401.read_measurement()
            self.k2401.output_off()

            if measurement is None:
                return {
                    "voltage": None,
                    "current": None,
                    "resistance": None,
                    "resistivity": None,
                    "conductivity": None,
                    "error": "Failed to read measurement",
                }

            v = measurement.get("voltage")
            i = measurement.get("current")
            r = measurement.get("resistance")

            resistivity = None
            conductivity = None
            if r is not None and r > 0:
                area = width * thickness
                if area > 0 and length > 0:
                    # Original: resistivity in Ω·m
                    # resistivity = r * area / length
                    # if resistivity > 0:
                    #     conductivity = 1.0 / resistivity
                    resistivity_Ohm_m = r * area / length
                    resistivity = resistivity_Ohm_m * 100 if resistivity_Ohm_m and resistivity_Ohm_m > 0 else None  # Ω·cm (1 Ω·m = 100 Ω·cm)
                    if resistivity and resistivity > 0:
                        conductivity = 1.0 / resistivity

            return {
                "voltage": v,
                "current": i,
                "resistance": r,
                "resistivity": resistivity,  # now in Ω·cm
                "conductivity": conductivity,
                "length": length,
                "width": width,
                "thickness": thickness,
            }
        except Exception as e:  # pragma: no cover
            logger.error("Failed to measure resistivity: %s", e)
            self.k2401.output_off()
            return {
                "voltage": None,
                "current": None,
                "resistance": None,
                "resistivity": None,
                "conductivity": None,
                "error": str(e),
            }


class SeebeckSessionManager:
    """
    Threaded Seebeck measurement session, adapted from seebeck_system.

    This is designed to be used by the GUI layer:
    - start_session(params) launches a background thread
    - get_data() returns accumulated rows
    - get_status() reports high-level state
    """

    def __init__(self, system: Optional[SeebeckSystem] = None):
        self.system = system or SeebeckSystem()
        self.session_active = False
        self.session_thread: Optional[threading.Thread] = None
        self.session_data: List[Dict[str, Any]] = []
        self.session_status: str = "idle"
        self.session_params: Optional[Dict[str, Any]] = None
        self.session_start_time: Optional[float] = None
        self.lock = threading.Lock()

    # --- Public API ---

    def start_session(self, params: Dict[str, Any]) -> bool:
        if self.session_active:
            return False
        self.session_active = True
        self.session_data = []
        self.session_status = "running"
        self.session_params = params
        self.session_start_time = time.time()
        self.session_thread = threading.Thread(
            target=self._run_session, args=(params,), daemon=True
        )
        self.session_thread.start()
        return True

    def stop_session(self) -> None:
        self.session_active = False
        self.session_status = "stopped"
        if self.session_thread and self.session_thread.is_alive():
            self.session_thread.join(timeout=2.0)
        try:
            self.system.heater_off()
        finally:
            self.system.disconnect_all()

    def get_data(self) -> List[Dict[str, Any]]:
        with self.lock:
            return list(self.session_data)

    def get_status(self) -> Dict[str, Any]:
        return {
            "active": self.session_active,
            "status": self.session_status,
            "params": self.session_params,
            "start_time": self.session_start_time,
            "data_count": len(self.session_data),
        }

    # --- Internal worker logic ---

    def _run_session(self, params: Dict[str, Any]) -> None:
        try:
            statuses = self.system.connect_all()
            if not all(s.connected for s in statuses.values()):
                self.session_status = "error: Failed to connect to one or more instruments."
                self.session_active = False
                return

            try:
                self.system.initialize_seebeck_instruments()
            except Exception as e:  # pragma: no cover
                self.session_status = f"error: Failed to initialize instruments: {e}"
                self.session_active = False
                self.system.disconnect_all()
                return

            interval = float(params["interval"])
            pre_time = float(params["pre_time"])
            start_volt = float(params["start_volt"])
            stop_volt = float(params["stop_volt"])
            inc_rate = float(params["inc_rate"])
            dec_rate = float(params["dec_rate"])
            hold_time = float(params["hold_time"])

            # Phase counts (same logic as legacy MeasurementSessionManager)
            k1 = int(pre_time // interval) if pre_time % interval == 0 else int(
                pre_time // interval + 1
            )
            k2 = int(((stop_volt - start_volt) / inc_rate) // interval) if (
                (stop_volt - start_volt) / inc_rate
            ) % interval == 0 else int(
                ((stop_volt - start_volt) / inc_rate) // interval + 1
            )
            k3 = int(hold_time // interval) if hold_time % interval == 0 else int(
                hold_time // interval + 1
            )
            k4 = int(((stop_volt - start_volt) / dec_rate) // interval) if (
                (stop_volt - start_volt) / dec_rate
            ) % interval == 0 else int(
                ((stop_volt - start_volt) / dec_rate) // interval + 1
            )

            while stop_volt - inc_rate * k2 * interval < 0:
                k2 -= 1
            while stop_volt - dec_rate * k4 * interval < 0:
                k4 -= 1

            volt = start_volt
            step = 1
            start_time = time.time()

            while self.session_active:
                loop_start = time.time()
                elapsed_time = int(time.time() - start_time)

                if 1 <= step <= k1:
                    volt = start_volt
                elif k1 + 1 <= step <= k1 + k2:
                    volt += inc_rate * interval
                elif k1 + k2 + 1 <= step <= k1 + k2 + k3:
                    volt = stop_volt
                elif k1 + k2 + k3 + 1 <= step <= k1 + k2 + k3 + k4:
                    volt -= dec_rate * interval
                else:
                    volt = start_volt

                self.system.set_heater_current(volt)
                point = self.system.measure_seebeck_point()
                row = {
                    "Time [s]": elapsed_time,
                    "TEMF [mV]": point["TEMF [mV]"],
                    "Temp1 [oC]": point["Temp1 [oC]"],
                    "Temp2 [oC]": point["Temp2 [oC]"],
                    "Delta Temp [oC]": (
                        (point["Temp1 [oC]"] or 0.0) - (point["Temp2 [oC]"] or 0.0)
                    ),
                }
                with self.lock:
                    self.session_data.append(row)

                step += 1
                if step > (k1 + k2 + k3 + k4):
                    break

                elapsed = time.time() - loop_start
                remaining = max(0.0, interval - elapsed)
                # Sleep in small chunks to allow responsive stop
                t = 0.0
                while t < remaining and self.session_active:
                    time.sleep(0.1)
                    t += 0.1

            self.system.heater_off()
            self.system.disconnect_all()
            self.session_status = "finished"
            self.session_active = False
        except Exception as e:  # pragma: no cover
            logger.exception("Seebeck session failed: %s", e)
            self.session_status = f"error: {e}"
            self.session_active = False
            try:
                self.system.heater_off()
            finally:
                self.system.disconnect_all()


class IVSweepSessionManager:
    """
    Threaded I-V sweep session for resistivity measurements.
    
    Performs voltage sweep and collects I-V data points.
    """

    def __init__(self, system: Optional[SeebeckSystem] = None):
        self.system = system or SeebeckSystem()
        self.session_active = False
        self.session_thread: Optional[threading.Thread] = None
        self.session_data: List[Dict[str, Any]] = []
        self.session_status: str = "idle"
        self.session_params: Optional[Dict[str, Any]] = None
        self.session_start_time: Optional[float] = None
        self.lock = threading.Lock()

    def start_session(self, params: Dict[str, Any]) -> bool:
        """Start I-V sweep session"""
        if self.session_active:
            return False
        self.session_active = True
        self.session_data = []
        self.session_status = "running"
        self.session_params = params
        self.session_start_time = time.time()
        self.session_thread = threading.Thread(
            target=self._run_sweep, args=(params,), daemon=True
        )
        self.session_thread.start()
        return True

    def stop_session(self) -> None:
        """Stop I-V sweep session"""
        self.session_active = False
        self.session_status = "stopped"
        if self.session_thread and self.session_thread.is_alive():
            self.session_thread.join(timeout=2.0)
        try:
            if self.system.k2401.connected:
                self.system.k2401.output_off()
        finally:
            # Don't disconnect all - other instruments might be in use
            pass

    def get_data(self) -> List[Dict[str, Any]]:
        """Get collected I-V data"""
        with self.lock:
            return list(self.session_data)

    def get_status(self) -> Dict[str, Any]:
        """Get session status"""
        return {
            "active": self.session_active,
            "status": self.session_status,
            "params": self.session_params,
            "start_time": self.session_start_time,
            "data_count": len(self.session_data),
        }

    def _run_sweep(self, params: Dict[str, Any]) -> None:
        """Run I-V sweep in background thread"""
        try:
            # Connect to 2401 if not already connected
            if not self.system.k2401.connected:
                statuses = self.system.connect_all()
                if not self.system.k2401.connected:
                    self.session_status = "error: Failed to connect to Keithley 2401"
                    self.session_active = False
                    return

            start_voltage = float(params["start_voltage"])
            stop_voltage = float(params["stop_voltage"])
            points = int(params["points"])
            delay_ms = float(params.get("delay_ms", 50.0))
            current_limit = float(params.get("current_limit", 0.1))
            voltage_limit = float(params.get("voltage_limit", 21.0))
            length = params.get("length")
            width = params.get("width")
            thickness = params.get("thickness")

            if points < 2:
                self.session_status = "error: points must be >= 2"
                self.session_active = False
                return

            # Calculate voltage steps
            step = (stop_voltage - start_voltage) / (points - 1)
            voltages = [start_voltage + i * step for i in range(points)]

            # Configure 2401
            vmax = max(abs(start_voltage), abs(stop_voltage), abs(voltage_limit))
            if not self.system.k2401.configure_voltage_source(
                voltage_limit=vmax, current_limit=current_limit
            ):
                self.session_status = "error: Failed to configure 2401"
                self.session_active = False
                return

            self.system.k2401.output_on()

            # Perform sweep
            for idx, voltage in enumerate(voltages):
                if not self.session_active:
                    break

                # Set voltage
                self.system.k2401.set_voltage(voltage)
                time.sleep(delay_ms / 1000.0)

                # Read measurement
                meas = self.system.k2401.read_measurement()
                
                if meas is None:
                    row = {
                        "Index": idx + 1,
                        "Voltage [V]": voltage,
                        "Current [A]": None,
                        "Resistance [Ohm]": None,
                        "Resistivity [Ohm·cm]": None,
                    }
                else:
                    v = meas.get("voltage", voltage)
                    i = meas.get("current")
                    r = meas.get("resistance")

                    # Calculate resistivity if dimensions provided
                    resistivity = None
                    if r is not None and r > 0 and length and width and thickness:
                        area = width * thickness
                        if area > 0 and length > 0:
                            # Original: resistivity in Ω·m
                            # resistivity = r * area / length
                            resistivity_Ohm_m = r * area / length
                            resistivity = resistivity_Ohm_m * 100 if resistivity_Ohm_m else None  # Ω·cm (1 Ω·m = 100 Ω·cm)

                    row = {
                        "Index": idx + 1,
                        "Voltage [V]": v,
                        "Current [A]": i,
                        "Resistance [Ohm]": r,
                        "Resistivity [Ohm·cm]": resistivity,
                    }

                with self.lock:
                    self.session_data.append(row)

            self.system.k2401.output_off()
            self.session_status = "finished"
            self.session_active = False

        except Exception as e:  # pragma: no cover
            logger.exception("I-V sweep failed: %s", e)
            self.session_status = f"error: {e}"
            self.session_active = False
            try:
                if self.system.k2401.connected:
                    self.system.k2401.output_off()
            except:
                pass


class KeithleyConnection:
    """
    High-level facade used by the rest of the application.

    - Provides connection-check APIs for UI indicators
    - Exposes Seebeck session manager for async measurements
    - Exposes I-V sweep session manager for resistivity measurements
    """

    def __init__(self):
        self.config = Config()
        self.system = SeebeckSystem(self.config)
        self.seebeck_session = SeebeckSessionManager(self.system)
        self.iv_sweep_session = IVSweepSessionManager(self.system)

    # --- Connection / status helpers for UI ---

    def connect_all(self) -> Dict[str, InstrumentStatus]:
        """Attempt to connect to all four instruments; returns per-device status."""
        return self.system.connect_all()

    def disconnect_all(self) -> None:
        self.system.disconnect_all()

    def get_connection_status(self) -> Dict[str, InstrumentStatus]:
        """
        Lightweight connection status based on current instrument objects.
        Does not attempt to reconnect; useful for 'Check Connection' button.
        """
        return {
            "2182A": InstrumentStatus(
                name="2182A",
                connected=self.system.k2182a.connected,
                resource_name=self.config.addr_2182a,
            ),
            "2700": InstrumentStatus(
                name="2700",
                connected=self.system.k2700.connected,
                resource_name=self.config.addr_2700,
            ),
            "PK160": InstrumentStatus(
                name="PK160",
                connected=self.system.pk160.connected,
                resource_name=self.config.addr_pk160,
            ),
            "2401": InstrumentStatus(
                name="2401",
                connected=self.system.k2401.connected,
                resource_name=self.config.addr_2401,
            ),
        }

    # --- Seebeck session accessors ---

    def start_seebeck_session(self, params: Dict[str, Any]) -> bool:
        return self.seebeck_session.start_session(params)

    def stop_seebeck_session(self) -> None:
        self.seebeck_session.stop_session()

    def get_seebeck_data(self) -> List[Dict[str, Any]]:
        return self.seebeck_session.get_data()

    def get_seebeck_status(self) -> Dict[str, Any]:
        return self.seebeck_session.get_status()

    # --- I-V Sweep / Resistivity session accessors ---

    def start_iv_sweep_session(self, params: Dict[str, Any]) -> bool:
        """Start I-V sweep session"""
        return self.iv_sweep_session.start_session(params)

    def stop_iv_sweep_session(self) -> None:
        """Stop I-V sweep session"""
        self.iv_sweep_session.stop_session()

    def get_iv_sweep_data(self) -> List[Dict[str, Any]]:
        """Get I-V sweep data"""
        return self.iv_sweep_session.get_data()

    def get_iv_sweep_status(self) -> Dict[str, Any]:
        """Get I-V sweep status"""
        return self.iv_sweep_session.get_status()

    # --- Resistivity helpers (single-point) ---

    def measure_resistivity_single(
        self,
        length: float,
        width: float,
        thickness: float,
        voltage: Optional[float] = None,
        current: Optional[float] = None,
    ) -> Dict[str, Optional[float]]:
        return self.system.measure_resistivity_single(
            length=length,
            width=width,
            thickness=thickness,
            voltage=voltage,
            current=current,
        )