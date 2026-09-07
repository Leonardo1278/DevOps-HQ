from fastapi import APIRouter, HTTPException, Request, Response

from app.services.storage import StorageError, media_type_for, read_local, save_local

router = APIRouter(prefix="/uploads", tags=["uploads"])


@router.put("/{storage_key:path}", status_code=204)
async def put_upload(storage_key: str, request: Request) -> Response:
    try:
        save_local(storage_key, await request.body())
    except StorageError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc
    return Response(status_code=204)


@router.get("/{storage_key:path}")
def get_upload(storage_key: str) -> Response:
    try:
        payload = read_local(storage_key)
    except StorageError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc
    filename = storage_key.rsplit("/", 1)[-1].replace('"', "")
    return Response(
        content=payload,
        media_type=media_type_for(filename),
        headers={
            "Content-Disposition": f'inline; filename="{filename}"',
            "X-Content-Type-Options": "nosniff",
        },
    )
