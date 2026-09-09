from fastapi import APIRouter
from . import (
    admin,
    admin_hierarchy,
    bulk,
    audit,
    core, 
    node, 
    subscription, 
    system, 
    user_template, 
    user,
    user_summary,
    home,
    device_limit,
    branding,
    backup,
)

api_router = APIRouter()

routers = [
    admin.router,
    admin_hierarchy.router,
    bulk.router,
    audit.router,
    core.router,
    node.router,
    subscription.router,
    system.router,
    user_template.router,
    user.router,
    user_summary.router,
    home.router,
    device_limit.router,
    branding.router,
    backup.router,
]

for router in routers:
    api_router.include_router(router)

__all__ = ["api_router"]
