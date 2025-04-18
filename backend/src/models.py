import uuid
from datetime import datetime
from typing import Annotated

from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import DateTime, UUID, func

# Types
uuid_type = Annotated[uuid.UUID, mapped_column(UUID(as_uuid=True), default=uuid.uuid4, unique=True)]

# Mixins
class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )