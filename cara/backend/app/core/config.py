import os

class Settings:
    PROJECT_NAME: str = "Cara Postnatal Follow-Up Coordination Platform"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Security
    JWT_SECRET: str = os.getenv("JWT_SECRET", "super-secret-key-cara-healthathon-2026")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 # 24 hours
    
    # Database (Defaults to SQLite for instant out-of-the-box local execution)
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./cara.db")
    
    # External Integrations (Twilio Sandbox & LLM)
    TWILIO_ACCOUNT_SID: str = os.getenv("TWILIO_ACCOUNT_SID", "AC_mock_twilio_account_sid")
    TWILIO_AUTH_TOKEN: str = os.getenv("TWILIO_AUTH_TOKEN", "mock_twilio_auth_token")
    TWILIO_WHATSAPP_NUMBER: str = os.getenv("TWILIO_WHATSAPP_NUMBER", "whatsapp:+14155238886")
    TWILIO_SMS_NUMBER: str = os.getenv("TWILIO_SMS_NUMBER", "+14155238886")
    LLM_API_KEY: str = os.getenv("LLM_API_KEY", "")

settings = Settings()
