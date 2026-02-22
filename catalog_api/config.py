import os
from typing import List


def load_env_file(path: str = None) -> None:
    """Lightweight .env loader for offline dev.

    Reads KEY=VALUE lines and sets them in os.environ if not already present.
    This avoids adding a runtime dependency for dotenv so the repo works offline.
    """
    if path is None:
        path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
    try:
        with open(path, "r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" not in line:
                    continue
                k, v = line.split("=", 1)
                k = k.strip()
                v = v.strip().strip('"')
                # don't overwrite existing env vars
                if k and k not in os.environ:
                    os.environ[k] = v
    except FileNotFoundError:
        # no .env present, that's fine
        return


# Load local .env automatically for offline dev
load_env_file()


class Settings:
    # Catalog DB
    CATALOG_DB_PATH: str = os.getenv("CATALOG_DB_PATH", "./catalog.db")
    # Socrata / ingest
    SOCRATA_APP_TOKEN: str = os.getenv("SOCRATA_APP_TOKEN", "")
    SOCRATA_SITES: List[str] = [s.strip() for s in os.getenv("SOCRATA_SITES", "https://data.lacity.org").split(",") if s.strip()]
    INGEST_PAGE_SIZE: int = int(os.getenv("INGEST_PAGE_SIZE", "50"))
    INGEST_SLEEP_SECONDS: float = float(os.getenv("INGEST_SLEEP_SECONDS", "0.5"))

    # Model selection
    MODEL_SELECTION: str = os.getenv("MODEL_SELECTION", "GPT5_2")
    LOCAL_MODEL_MOCK: bool = os.getenv("LOCAL_MODEL_MOCK", "0") in ("1", "true", "True")

    # GPT-5.2 / AI Imm
    GPT5_2_AZURE_ENDPOINT: str = os.getenv("GPT5_2_AZURE_ENDPOINT", "")
    GPT5_2_AZURE_KEY: str = os.getenv("GPT5_2_AZURE_KEY", "")
    GPT5_2_DEPLOYMENT: str = os.getenv("GPT5_2_DEPLOYMENT", "gpt-5.2-chat")
    GPT5_2_API_VERSION: str = os.getenv("GPT5_2_API_VERSION", "2025-04-01-preview")


settings = Settings()
