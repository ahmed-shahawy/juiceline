# Juiceline Development Environment Configuration

# Application Settings
APP_NAME = "Juiceline"
VERSION = "1.0.0"
DEBUG = True

# Geidea API Configuration
GEIDEA_API_BASE_URL = "https://api.geidea.net"
GEIDEA_API_KEY = ""  # To be configured during deployment
GEIDEA_MERCHANT_ID = ""  # To be configured during deployment

# Database Configuration (if needed)
DATABASE_CONFIG = {
    "engine": "sqlite3",
    "name": "juiceline.db",
    "user": "",
    "password": "",
    "host": "localhost",
    "port": 5432
}

# Logging Configuration
LOG_LEVEL = "DEBUG"
LOG_FILE = "logs/juiceline.log"

# Security Settings
SECRET_KEY = "your-secret-key-here"  # Change in production
ENCRYPTION_ALGORITHM = "AES-256"

# Device Connection Settings
DEVICE_TIMEOUT = 30
MAX_RETRY_ATTEMPTS = 3
CONNECTION_POOL_SIZE = 10