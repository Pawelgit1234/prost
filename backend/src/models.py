from datetime import datetime, timezone
import uuid
from typing import Annotated

from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import DateTime, UUID

# Types
uuid_type = Annotated[uuid.UUID, mapped_column(UUID(as_uuid=True), default=uuid.uuid4, unique=True)]

# Mixins
class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )