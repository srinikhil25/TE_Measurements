from configparser import ConfigParser
import os


class Config:
    """Application configuration loader"""
    
    _instance = None
    _config = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
            cls._instance._load_config()
        return cls._instance
    
    def _load_config(self):
        """Load configuration from config.ini"""
        self._config = ConfigParser()
        config_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            'config',
            'config.ini'
        )
        self._config.read(config_path)
    
    @property
    def db_type(self):
        return self._config.get('database', 'db_type', fallback='sqlite')
    
    @property
    def db_host(self):
        return self._config.get('database', 'host', fallback='localhost')
    
    @property
    def db_port(self):
        return self._config.get('database', 'port', fallback='5432')
    
    @property
    def db_database(self):
        return self._config.get('database', 'database', fallback='te_measurements')
    
    @property
    def db_username(self):
        return self._config.get('database', 'username', fallback='te_user')
    
    @property
    def db_password(self):
        return self._config.get('database', 'password', fallback='')
    
    @property
    def sqlite_path(self):
        return self._config.get('database', 'sqlite_path', fallback='data/te_measurements.db')
    
    @property
    def raw_data_path(self):
        path = self._config.get('storage', 'raw_data_path', fallback='data/raw')
        os.makedirs(path, exist_ok=True)
        return path
    
    @property
    def backup_path(self):
        path = self._config.get('storage', 'backup_path', fallback='data/backup')
        os.makedirs(path, exist_ok=True)
        return path
    
    @property
    def app_name(self):
        return self._config.get('application', 'app_name', fallback='TE Measurements')
    
    @property
    def app_version(self):
        return self._config.get('application', 'version', fallback='1.0.0')
    
    @property
    def log_level(self):
        return self._config.get('application', 'log_level', fallback='INFO')
    
    @property
    def log_file(self):
        return self._config.get('application', 'log_file', fallback='logs/app.log')
    
    @property
    def session_timeout_minutes(self):
        return self._config.getint('security', 'session_timeout_minutes', fallback=60)
    
    @property
    def password_min_length(self):
        return self._config.getint('security', 'password_min_length', fallback=8)
    
    @property
    def keithley_address(self):
        return self._config.get('instruments', 'keithley_address', fallback='GPIB0::22::INSTR')
    
    @property
    def connection_timeout(self):
        return self._config.getint('instruments', 'connection_timeout', fallback=10)
    
    @property
    def retry_attempts(self):
        return self._config.getint('instruments', 'retry_attempts', fallback=3)

