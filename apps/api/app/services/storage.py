from __future__ import annotations

import mimetypes
import re
import uuid
from dataclasses import dataclass
from pathlib import Path

from app.core.config import get_settings

KEY_PATTERN = re.compile(r"^docs/[0-9a-f-]{36}/[A-Za-z0-9._-]+$")
MAX_UPLOAD_BYTES = 20 * 1024 * 1024


class StorageError(Exception):
    def __init__(self, message: str, status_code: int = 400) -> None:
        super().__init__(message)
        self.status_code = status_code


@dataclass
class PresignResult:
    upload_url: str
    method: str
    headers: dict[str, str]
    storage_key: str
    expires_in: int


_EXTRA_TYPES = {
    ".md": "text/markdown",
    ".markdown": "text/markdown",
    ".csv": "text/csv",
    ".json": "application/json",
    ".webp": "image/webp",
    ".svg": "image/svg+xml",
}


def media_type_for(filename: str) -> str:
    suffix = Path(filename).suffix.lower()
    if suffix in _EXTRA_TYPES:
        return _EXTRA_TYPES[suffix]
    guessed, _ = mimetypes.guess_type(filename)
    return guessed or "application/octet-stream"


def safe_filename(name: str) -> str:
    base = Path(name).name
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "-", base).strip(".-") or "file"
    return cleaned[:180]


def new_storage_key(filename: str) -> str:
    return f"docs/{uuid.uuid4()}/{safe_filename(filename)}"


def assert_storage_key(key: str) -> str:
    if not KEY_PATTERN.fullmatch(key):
        raise StorageError("Invalid storage_key")
    return key


def local_root() -> Path:
    return get_settings().resolved_upload_dir


def uses_s3() -> bool:
    return bool(get_settings().s3_bucket.strip())


def local_path_for(key: str) -> Path:
    root = local_root()
    path = (root / assert_storage_key(key)).resolve()
    if not str(path).startswith(str(root)):
        raise StorageError("Invalid storage_key")
    return path


def presign_put(filename: str, content_type: str) -> PresignResult:
    key = new_storage_key(filename)
    settings = get_settings()
    headers = {"Content-Type": content_type or "application/octet-stream"}
    if uses_s3():
        import boto3

        client = boto3.client("s3", region_name=settings.aws_region)
        url = client.generate_presigned_url(
            "put_object",
            Params={
                "Bucket": settings.s3_bucket,
                "Key": key,
                "ContentType": headers["Content-Type"],
            },
            ExpiresIn=900,
        )
        return PresignResult(
            upload_url=url,
            method="PUT",
            headers=headers,
            storage_key=key,
            expires_in=900,
        )
    public = settings.api_public_url.rstrip("/")
    return PresignResult(
        upload_url=f"{public}/api/v1/uploads/{key}",
        method="PUT",
        headers=headers,
        storage_key=key,
        expires_in=900,
    )


def presign_get(key: str) -> str:
    settings = get_settings()
    if uses_s3():
        import boto3

        client = boto3.client("s3", region_name=settings.aws_region)
        filename = key.rsplit("/", 1)[-1]
        return client.generate_presigned_url(
            "get_object",
            Params={
                "Bucket": settings.s3_bucket,
                "Key": assert_storage_key(key),
                "ResponseContentDisposition": f'inline; filename="{filename}"',
                "ResponseContentType": media_type_for(filename),
            },
            ExpiresIn=900,
        )
    public = settings.api_public_url.rstrip("/")
    return f"{public}/api/v1/uploads/{assert_storage_key(key)}"


def object_exists(key: str) -> bool:
    if uses_s3():
        import boto3
        from botocore.exceptions import ClientError

        client = boto3.client("s3", region_name=get_settings().aws_region)
        try:
            client.head_object(Bucket=get_settings().s3_bucket, Key=assert_storage_key(key))
            return True
        except ClientError:
            return False
    return local_path_for(key).is_file()


def save_local(key: str, payload: bytes) -> None:
    if uses_s3():
        raise StorageError("Direct upload is only available without S3_BUCKET", 400)
    if len(payload) > MAX_UPLOAD_BYTES:
        raise StorageError("File too large", 413)
    path = local_path_for(key)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)


def read_local(key: str) -> bytes:
    path = local_path_for(key)
    if not path.is_file():
        raise StorageError("File not found", 404)
    return path.read_bytes()
