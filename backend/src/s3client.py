from contextlib import asynccontextmanager
from fastapi import UploadFile
from aiobotocore.session import get_session
from botocore.exceptions import ClientError

from src.settings import S3_BUCKET, S3_ENDPOINT, MINIO_ROOT_PASSWORD, MINIO_ROOT_USER

class S3Client:
    def __init__(
        self,
        access_key: str,
        secret_key: str,
        endpoint_url: str,
        bucket_name: str,
    ):
        self.config = {
            "aws_access_key_id": access_key,
            "aws_secret_access_key": secret_key,
            "endpoint_url": endpoint_url,
            "region_name": "us-east-1",
        }
        self.bucket_name = bucket_name
        self.session = get_session()

    @asynccontextmanager
    async def get_client(self):
        async with self.session.create_client("s3", **self.config) as client:
            yield client

    async def ensure_bucket_exists(self):
        async with self.get_client() as client:
            try:
                await client.head_bucket(Bucket=self.bucket_name)
            except ClientError:
                await client.create_bucket(Bucket=self.bucket_name)

    async def upload_file(
        self,
        file: UploadFile,
        object_name: str,
    ) -> str:
        await self.ensure_bucket_exists()

        async with self.get_client() as client:
            await client.put_object(
                Bucket=self.bucket_name,
                Key=object_name,
                Body=await file.read(),
                ContentType=file.content_type,
            )

        return f"{S3_ENDPOINT}/{self.bucket_name}/{object_name}"


s3 = S3Client(
    access_key=MINIO_ROOT_USER,
    secret_key=MINIO_ROOT_PASSWORD,
    endpoint_url=S3_ENDPOINT,
    bucket_name=S3_BUCKET,
)