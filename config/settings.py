import os
from dotenv import load_dotenv
from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional

load_dotenv()

BASE_DIR: Path = Path(__file__).resolve().parent.parent
TEMPLATES_DIR: Path = BASE_DIR / "templates"


# def parse_comma_separated_list(value: Optional[str]):
#     if not value:
#         return []
#     return [item.strip() for item in value.split(",") if item.strip()]


class Settings(BaseSettings):
    """Application settings."""

    # API Config
    API_TITLE: str = "Surestrat -> Pineapple - Lead Management RESTFUL API"
    API_DESCRIPTION: str = (
        "REST API for handling Pineapple insurance quote and lead transfer"
    )
    API_VERSION: str = "1.0.1"
    API_PREFIX: str = "api/v1"
    API_SOURCE_IDENTIFIER: str = "surestrat"
    DEBUG: bool | str = os.getenv("DEBUG", False)

    # Environment configuration
    ENVIRONMENT: str = os.getenv(
        "ENVIRONMENT", "test"
    ).lower()  # 'test' or 'production'
    IS_PRODUCTION: bool = ENVIRONMENT == "production"

    # CORS settings
    ALLOWED_ORIGINS: str = os.getenv("ALLOWED_ORIGINS", "")

    # ALLOWED_ORIGINS: list[str] = Field(
    #     default_factory=lambda: parse_comma_separated_list(
    #         os.getenv("ALLOWED_ORIGIN", "http://localhost:3000")
    #     )
    # )
    # ALLOWED_METHODS: list[str] = Field(
    #     default_factory=lambda: parse_comma_separated_list(
    #         os.getenv("ALLOWED_METHODS", "GET, POST, PUT, DELETE, OPTIONS")
    #     )
    # )
    # ALLOWED_HEADERS: list[str] = Field(
    #     default_factory=lambda: parse_comma_separated_list(
    #         os.getenv(
    #             "ALLOWED_HEADERS",
    #             "Content-Type, Authorization, X-Requested-With, Accept, Origin",
    #         )
    #     )
    # )

    # Server settings
    HOST: str = "0.0.0.0"
    PORT: int = int(os.getenv("PORT", 4000))

    # Appwrite settings
    APPWRITE_ENDPOINT: str | None = os.getenv("APPWRITE_ENDPOINT")
    APPWRITE_PROJECT_ID: str | None = os.getenv("APPWRITE_PROJECT_ID")
    APPWRITE_API_KEY: str | None = os.getenv("APPWRITE_API_KEY")
    DATABASE_ID: str | None = os.getenv("APPWRITE_DATABASE_ID")
    QUOTE_COL_ID: str | None = os.getenv("APPWRITE_LEAD_QUOTE_COL_ID")
    TRANSFER_COL_ID: str | None = os.getenv("APPWRITE_LEAD_TRANSFER_COL_ID")

    # Email settings
    SMTP_SERVER: str | None = os.getenv("SMTP_SERVER")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT") or 465)
    SMTP_USERNAME: str | None = os.getenv("SMTP_USERNAME")
    SMTP_PASSWORD: str | None = os.getenv("SMTP_PASSWORD")
    USE_MAILGUN: bool = os.getenv("USE_MAILGUN", "false").lower() == "true"
    SMTP_TIMEOUT: int = int(os.getenv("SMTP_TIMEOUT") or 30)
    EMAIL_FROM: str = os.getenv("EMAIL_FROM", "")

    # Notification recipients
    ADMIN_EMAILS: str = os.getenv("ADMIN_EMAILS") or os.getenv(
        "NOTIFICATION_EMAILS", ""
    )
    NOTIFICATION_EMAILS: str = os.getenv(
        "NOTIFICATION_EMAILS", os.getenv("ADMIN_EMAILS", "")
    )
    ADMIN_CC_EMAILS: str = os.getenv("ADMIN_CC_EMAILS", "")
    ADMIN_BCC_EMAILS: str = os.getenv("ADMIN_BCC_EMAILS", "")

    # External API - Pineapple credentials {bearer_token}
    # Test credentials
    PINEAPPLE_TEST_API_KEY: str = os.getenv("PINEAPPLE_TEST_API_KEY", "")
    PINEAPPLE_TEST_API_SECRET: str = os.getenv("PINEAPPLE_TEST_API_SECRET", "")

    # Production credentials
    PINEAPPLE_PROD_API_KEY: str = os.getenv("PINEAPPLE_PROD_API_KEY", "")
    PINEAPPLE_PROD_API_SECRET: str = os.getenv("PINEAPPLE_PROD_API_SECRET", "")

    # Dynamic credential selection based on environment
    @property
    def PINEAPPLE_API_KEY(self) -> str:
        return (
            self.PINEAPPLE_PROD_API_KEY
            if self.IS_PRODUCTION
            else self.PINEAPPLE_TEST_API_KEY
        )

    @property
    def PINEAPPLE_API_SECRET(self) -> str:
        return (
            self.PINEAPPLE_PROD_API_SECRET
            if self.IS_PRODUCTION
            else self.PINEAPPLE_TEST_API_SECRET
        )

    # External API - Pineapple endpoints
    PINEAPPLE_TEST_BASE_URL: str = "http://gw-test.pineapple.co.za"
    PINEAPPLE_PROD_BASE_URL: str = "http://gw.pineapple.co.za"

    @property
    def PINEAPPLE_BASE_URL(self) -> str:
        return (
            self.PINEAPPLE_PROD_BASE_URL
            if self.IS_PRODUCTION
            else self.PINEAPPLE_TEST_BASE_URL
        )

    # URL paths
    PINEAPPLE_TRANSFER_PATH: str = "/users/motor_lead"
    PINEAPPLE_QUOTE_PATH: str = "/api/v1/quote/quick-quote"

    @property
    def PINEAPPLE_TRANSFER_API_URL(self) -> str:
        return f"{self.PINEAPPLE_BASE_URL}{self.PINEAPPLE_TRANSFER_PATH}"

    @property
    def PINEAPPLE_QUOTE_API_URL(self) -> str:
        return f"{self.PINEAPPLE_BASE_URL}{self.PINEAPPLE_QUOTE_PATH}"

    # Notification settings
    SEND_QUOTE_NOTIFICATIONS: bool = (
        os.getenv("SEND_QUOTE_NOTIFICATIONS", "true").lower() == "true"
    )
    SEND_TRANSFER_NOTIFICATIONS: bool = (
        os.getenv("SEND_TRANSFER_NOTIFICATIONS", "true").lower() == "true"
    )
    API_SOURCE_IDENTIFIER: str = os.getenv("API_SOURCE_IDENTIFIER", "surestrat")

    # Error handling settings
    IGNORE_DOCUMENT_NOT_FOUND_ERRORS: bool = (
        os.getenv("IGNORE_DOCUMENT_NOT_FOUND_ERRORS", "false").lower() == "true"
    )
    LOG_DOCUMENT_ERRORS: bool = (
        os.getenv("LOG_DOCUMENT_ERRORS", "true").lower() == "true"
    )
    DB_ERROR_NOTIFICATION_EMAIL: str = os.getenv("DB_ERROR_NOTIFICATION_EMAIL", "")

    # Debug settings
    DEBUG_MODE: bool = Field(default=True)

    class Config:
        env_file: str = ".env"
        env_file_encoding: str = "utf-8"
        case_sensitive = True
        extra = "ignore"

        # Ignore extra env vars not defined as fields


settings = Settings()
