# Keithley Instrument Connections

This document contains the instrument connection details extracted from the legacy system.

## GPIB Addresses

### Keithley 2182A (Voltage Measurement)
- **Address**: `GPIB0::7::INSTR`
- **Purpose**: Measures voltage (TEMF - Thermoelectric Motive Force)
- **Configuration**:
  - Command: `*RST` (Reset)
  - Command: `:CONF:VOLT` (Configure for voltage)
  - Command: `:VOLT:DIGITS 8` (8 digits precision)
  - Command: `:VOLT:NPLC 5` (5 power line cycles)
  - Read: `:READ?` (Returns voltage value)

### Keithley 2700 (Temperature Measurement)
- **Address**: `GPIB0::16::INSTR`
- **Purpose**: Measures temperature via thermocouples
- **Default Channels**: 
  - Channel 102: Temperature 1 (Temp1)
  - Channel 104: Temperature 2 (Temp2)
- **Configuration**:
  - Command: `*RST` (Reset)
  - Command: `:ROUT:CLOS (@{channel})` (Close channel)
  - Command: `:CONF:TEMP` (Configure for temperature)
  - Command: `:UNIT:TEMP C` (Celsius units)
  - Command: `:TEMP:TRAN TC` (Thermocouple type)
  - Command: `:TEMP:TC:TYPE K` (K-type thermocouple)
  - Command: `:TEMP:TC:RJUN:RSEL EXT` (External reference junction)
  - Command: `:TEMP:NPLC {nplc}` (Power line cycles, default 1.0)
  - Read: `:READ?` (Returns temperature value)

### PK160 (Current Control / Power Supply)
- **Address**: `GPIB0::15::INSTR`
- **Purpose**: Controls current for Seebeck measurements
- **Initialization Commands**:
  - `#1 REN` (Remote enable)
  - `#1 VCN 100` (Voltage control, 100V)
  - `#1 OCP 100` (Overcurrent protection, 100A)
  - `#1 SW1` (Switch on)
- **Control Commands**:
  - `#1 ISET{value}` (Set current value)
  - `#1 SW0` (Switch off / Output off)

## Connection Flow

1. **Initialize PyVISA ResourceManager**
   ```python
   rm = pyvisa.ResourceManager()
   ```

2. **Connect to all instruments**
   - Keithley 2182A: `rm.open_resource("GPIB0::7::INSTR")`
   - Keithley 2700: `rm.open_resource("GPIB0::16::INSTR")`
   - PK160: `rm.open_resource("GPIB0::15::INSTR")`

3. **Configure instruments**
   - Configure 2182A for voltage measurement
   - Configure 2700 for temperature measurement (channels 102, 104)
   - Initialize PK160 power supply

4. **Measurement Sequence**
   - Set current via PK160: `#1 ISET{value}`
   - Read voltage from 2182A: `:READ?`
   - Read temperatures from 2700: `:READ?` (channels 102, 104)

5. **Cleanup**
   - Turn off PK160 output: `#1 SW0`
   - Close all instrument connections

## Dependencies

- **PyVISA**: For GPIB communication
- **NI-VISA** or **pyvisa-py**: Backend for PyVISA

## Notes

- All instruments use GPIB interface
- Timeout is set to 20000ms (20 seconds)
- Temperature channels are configurable (default: 102, 104)
- Current values are in the format expected by PK160 command syntax

