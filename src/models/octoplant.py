"""Pydantic models voor OctoPlant / versiondog API responses."""

from typing import Any, Optional
from pydantic import BaseModel


class TokenResponse(BaseModel):
    """OAuth2 token response van de OctoPlant authenticatie-endpoint."""

    access_token: str
    token_type: str
    expires_in: Optional[int] = None
    refresh_token: Optional[str] = None


class OrderMetadata(BaseModel):
    """Metadata van een export order."""

    state: str  # STATE_UNSPECIFIED | STATE_PENDING | STATE_RUNNING | STATE_SUCCEEDED | STATE_FAILED


class OrderState(BaseModel):
    """Status-response van een export order (GET /v1/order/{name})."""

    name: str
    metadata: Optional[OrderMetadata] = None
    done: bool = False
    error: Optional[dict[str, Any]] = None


class CheckoutResult(BaseModel):
    """Resultaat van een VDogAutoCheckOut.exe aanroep."""

    returncode: int
    status: str
    stdout: str
    stderr: str

    @property
    def success(self) -> bool:
        return self.returncode == 0


class ExportCliResult(BaseModel):
    """Resultaat van een VDogAutoExport.exe aanroep."""

    returncode: int
    success: bool
    stdout: str
    stderr: str
