import json
import os
import secrets
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from fastapi import FastAPI, Header, HTTPException, Request, status
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

EVENTS_FILE = Path(
    os.getenv(
        "SOC_COLLECTOR_EVENTS_FILE",
        "/var/lib/soc-collector/events.ndjson",
    )
)

MAX_EVENT_SIZE = 64 * 1024


class SensorEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    event_type: str = Field(
        min_length=1,
        max_length=64,
        pattern=r"^[a-z0-9][a-z0-9._-]*$",
    )
    sensor_id: str = Field(
        min_length=1,
        max_length=64,
        pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]*$",
    )
    network_id: str = Field(
        min_length=1,
        max_length=64,
        pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]*$",
    )
    observed_at: datetime
    source: str = Field(
        min_length=1,
        max_length=32,
        pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]*$",
    )
    data: dict[str, Any] | None = None

    @field_validator("observed_at")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("observed_at must include a timezone")
        return value


app = FastAPI(
    title="SOC Collector API",
    version="1.0.0",
    docs_url=None,
    redoc_url=None,
)


def authenticate(authorization: str | None) -> None:
    expected_token = os.getenv("SOC_COLLECTOR_TOKEN")

    if not expected_token:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Collector token is not configured",
        )

    prefix = "Bearer "

    if not authorization or not authorization.startswith(prefix):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization",
            headers={"WWW-Authenticate": "Bearer"},
        )

    supplied_token = authorization[len(prefix):]

    if not secrets.compare_digest(supplied_token, expected_token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization",
            headers={"WWW-Authenticate": "Bearer"},
        )


@app.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "soc-collector",
    }


@app.post("/events", status_code=status.HTTP_202_ACCEPTED)
async def receive_event(
    request: Request,
    authorization: str | None = Header(default=None),
) -> dict[str, str]:
    authenticate(authorization)

    content_length = request.headers.get("content-length")

    if content_length:
        try:
            if int(content_length) > MAX_EVENT_SIZE:
                raise HTTPException(
                    status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                    detail="Event exceeds 64 KiB",
                )
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid Content-Length",
            )

    raw_body = await request.body()

    if len(raw_body) > MAX_EVENT_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail="Event exceeds 64 KiB",
        )

    try:
        event = SensorEvent.model_validate_json(raw_body)
    except ValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=json.loads(exc.json()),
        )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON",
        )

    event_id = str(uuid4())
    received_at = datetime.now(timezone.utc)

    event_payload = event.model_dump(mode="json")
    event_data = event_payload.pop("data", None)

    record = {
        "event_id": event_id,
        "received_at": received_at.isoformat(),
        **event_payload,
    }

    if event_data is not None:
        message = event_data.get("message")

        if isinstance(message, str) and message:
            record["message"] = message

        record["event_data"] = json.dumps(
            event_data,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )

    EVENTS_FILE.parent.mkdir(parents=True, exist_ok=True)

    with EVENTS_FILE.open("a", encoding="utf-8") as file:
        file.write(
            json.dumps(record, ensure_ascii=False, separators=(",", ":"))
            + "\n"
        )
        file.flush()
        os.fsync(file.fileno())

    return {
        "status": "accepted",
        "event_id": event_id,
    }
