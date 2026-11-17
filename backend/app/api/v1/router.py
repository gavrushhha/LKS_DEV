"""Сборка роутеров версии v1."""

from fastapi import APIRouter

from app.api.v1 import dictionaries, journal, schedule, statements, system

api_router = APIRouter()
api_router.include_router(schedule.router)
api_router.include_router(journal.router)
api_router.include_router(statements.router)
api_router.include_router(dictionaries.router)
api_router.include_router(system.router)
