from minio import Minio
from app.core.config import settings
import io

class StorageService:
    def __init__(self):
        self.client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE
        )
        self._ensure_bucket()

    def _ensure_bucket(self):
        if not self.client.bucket_exists(settings.MINIO_BUCKET):
            self.client.make_bucket(settings.MINIO_BUCKET)

    async def upload_file(self, filename: str, data: bytes, content_type: str = "application/octet-stream") -> str:
        # TODO: Make this async compatible if needed, standard MinIO client is sync
        # Usually wrapping in asyncio.to_thread is good for blocking IO
        import asyncio
        
        def _upload():
            self.client.put_object(
                settings.MINIO_BUCKET,
                filename,
                io.BytesIO(data),
                len(data),
                content_type=content_type
            )
        
        await asyncio.to_thread(_upload)
        
        # Return URL
        # For local dev, we might need a presigned URL or public URL
        # strict production use would use presigned
        return f"http://{settings.MINIO_ENDPOINT}/{settings.MINIO_BUCKET}/{filename}"

    async def get_presigned_url(self, filename: str) -> str:
        return self.client.presigned_get_object(settings.MINIO_BUCKET, filename)

storage_service = StorageService()
