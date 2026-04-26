import os
from pathlib import Path

from pydantic import BaseModel


class Settings(BaseModel):
    urls_file: Path
    output_dir: Path = Path("feeds")
    verbose: bool = False

    @property
    def firecrawl_key(self) -> str | None:
        return os.environ.get("FIRECRAWL_API_KEY")
