"""Входная точка НСИ; обработчики сообщений пока не реализованы."""

import secrets
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel, ConfigDict, Field

from app.core.config import settings

router = APIRouter(tags=["NSI"])
basic_auth = HTTPBasic(auto_error=False)


class RoutingHeader(BaseModel):
    """Минимальный заголовок сообщения НСИ."""

    model_config = ConfigDict(extra="allow")
    operationType: str = Field(min_length=1, max_length=64)
    sourceId: str = Field(min_length=1, max_length=128)
    destinationId: str = Field(min_length=1, max_length=128)
    messageId: str | None = Field(default=None, max_length=128)


class NsiRequest(BaseModel):
    """Конверт сообщения НСИ; содержимое датаграммы пока не обрабатывается."""

    routingHeader: RoutingHeader
    datagram: dict[str, Any]


def verify_nsi_auth(credentials: Annotated[HTTPBasicCredentials | None, Depends(basic_auth)]) -> None:
    """Проверить настройки и Basic Auth, не раскрывая содержимое учётных данных."""
    username = settings.nsi_basic_username
    password = settings.nsi_basic_password.get_secret_value()
    if not username or not password:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="НСИ не настроена")
    supplied_username = credentials.username if credentials else ""
    supplied_password = credentials.password if credentials else ""
    valid_user = secrets.compare_digest(supplied_username.encode("utf-8"), username.encode("utf-8"))
    valid_password = secrets.compare_digest(supplied_password.encode("utf-8"), password.encode("utf-8"))
    if not (valid_user and valid_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Ошибка авторизации",
            headers={"WWW-Authenticate": "Basic"},
        )


@router.post("/nsirest/", dependencies=[Depends(verify_nsi_auth)])
async def receive_nsi_message(message: NsiRequest) -> dict[str, Any]:
    """Отклонить сообщение, пока обработчики операций и сохранение не готовы."""
    header = message.routingHeader
    if header.destinationId != settings.nsi_destination_id:
        raise HTTPException(status_code=400, detail="Неверный получатель")
    response_header: dict[str, str] = {
        "sourceId": settings.nsi_destination_id,
        "destinationId": header.sourceId,
    }
    if header.messageId:
        response_header["correlationId"] = header.messageId
    return {
        "callCC": 2,
        "callRC": "Операция пока не реализована",
        "routingHeader": response_header,
        "datagram": {"x-datagram": {}},
    }
