from fastapi import APIRouter

from app.api.v1 import (
    activity,
    clients,
    credentials,
    dashboard,
    documents,
    ideas,
    inbox,
    notes,
    projects,
    tasks,
    uploads,
)

api_router = APIRouter()
api_router.include_router(dashboard.router)
api_router.include_router(projects.router)
api_router.include_router(clients.router)
api_router.include_router(tasks.router)
api_router.include_router(ideas.router)
api_router.include_router(inbox.router)
api_router.include_router(notes.router)
api_router.include_router(documents.router)
api_router.include_router(uploads.router)
api_router.include_router(credentials.router)
api_router.include_router(activity.router)
