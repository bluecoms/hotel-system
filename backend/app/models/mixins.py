# app/models/mixins.py
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import DateTime, String
from datetime import datetime
from typing import Optional

class SoftDeleteMixin:
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, index=True)
    deleted_by: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)

    def soft_delete(self, by: str):
        self.deleted_at = datetime.utcnow()
        self.deleted_by = by

    def restore(self):
        self.deleted_at = None
        self.deleted_by = None

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None
