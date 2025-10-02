from .ota import router as ota
from .reports import router as reports
from .closing import router as closing
from .users import router as users
from .menu import router as menu
from .upload import router as upload
from .audit import router as audit

__all__ = ["ota", "reports", "users", "closing", "menu", "upload", "audit"]
