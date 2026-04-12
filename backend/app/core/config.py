from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Supabase
    supabase_url: str = ""
    supabase_service_role_key: str = ""

    # Stripe
    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""

    # Cloudflare R2
    cloudflare_api_token: str = ""
    cloudflare_account_id: str = ""
    r2_bucket_name: str = ""
    r2_public_url: str = ""
    r2_access_key_id: str = ""
    r2_secret_access_key: str = ""

    # AgentOps
    agentops_api_key: str = ""

    # Anthropic
    anthropic_api_key: str = ""

    # Firecrawl
    firecrawl_api_key: str = ""


settings = Settings()
