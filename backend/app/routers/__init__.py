# Routers Package
from .auth import router as auth_router
from .users import router as users_router
from .wallets import router as wallets_router
from .tournaments import router as tournaments_router
from .payments import router as payments_router
from .whatsapp import router as whatsapp_router
from .admin import router as admin_router

__all__ = [
    "auth_router",
    "users_router", 
    "wallets_router",
    "tournaments_router",
    "payments_router",
    "whatsapp_router",
    "admin_router"
]
