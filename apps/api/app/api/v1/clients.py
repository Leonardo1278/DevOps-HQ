from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from app.api.v1.deps import db_session, pagination, raise_not_found
from app.models.enums import ClientStatus
from app.schemas.core import ClientCreate, ClientOut, ClientUpdate, Page
from app.services.clients import ClientService
from app.services.core import NotFoundError

router = APIRouter(prefix="/clients", tags=["clients"])


@router.get("", response_model=Page[ClientOut])
def list_clients(
    q: str | None = Query(default=None),
    status: ClientStatus | None = None,
    sync: bool = False,
    page: tuple[int, int] = Depends(pagination),
    db: Session = Depends(db_session),
) -> Page[ClientOut]:
    service = ClientService(db)
    if sync:
        service.sync_from_projects()
    items, total = service.list(
        q=q,
        status=status.value if status else None,
        limit=page[0],
        offset=page[1],
    )
    if total == 0:
        items = service.sync_from_projects()
        items, total = service.list(
            q=q,
            status=status.value if status else None,
            limit=page[0],
            offset=page[1],
        )
    return Page(items=items, total=total, limit=page[0], offset=page[1])


@router.post("/sync-from-projects", response_model=Page[ClientOut])
def sync_clients(db: Session = Depends(db_session)) -> Page[ClientOut]:
    items = ClientService(db).sync_from_projects()
    return Page(items=items, total=len(items), limit=len(items), offset=0)


@router.post("", response_model=ClientOut, status_code=201)
def create_client(payload: ClientCreate, db: Session = Depends(db_session)) -> ClientOut:
    try:
        return ClientService(db).create(payload)
    except NotFoundError as exc:
        raise_not_found(exc)
        raise


@router.get("/{client_id}", response_model=ClientOut)
def get_client(client_id: UUID, db: Session = Depends(db_session)) -> ClientOut:
    try:
        return ClientService(db).get(client_id)
    except NotFoundError as exc:
        raise_not_found(exc)
        raise


@router.patch("/{client_id}", response_model=ClientOut)
def update_client(
    client_id: UUID, payload: ClientUpdate, db: Session = Depends(db_session)
) -> ClientOut:
    try:
        return ClientService(db).update(client_id, payload)
    except NotFoundError as exc:
        raise_not_found(exc)
        raise


@router.delete("/{client_id}", status_code=204)
def delete_client(client_id: UUID, db: Session = Depends(db_session)) -> Response:
    try:
        ClientService(db).delete(client_id)
    except NotFoundError as exc:
        raise_not_found(exc)
        raise
    return Response(status_code=204)
