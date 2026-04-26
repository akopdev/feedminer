from pathlib import Path
from typing import Literal

from pydantic import BaseModel, model_validator


class Settings(BaseModel):
    urls_file: Path
    scraper: Literal["http", "firecrawl"] = "http"
    firecrawl_key: str | None = None
    output_dir: Path = Path("feeds")
    verbose: bool = False

    @model_validator(mode="after")
    def firecrawl_needs_key(self) -> "Settings":
        if self.scraper == "firecrawl" and not self.firecrawl_key:
            raise ValueError("--firecrawl-key is required when using --scraper=firecrawl")
        return self
