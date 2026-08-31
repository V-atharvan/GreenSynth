"""
GreenSynth Analytics — Unit Tests for Storage Abstraction & Providers (Phase 9)

Tests:
  1. LocalFileStorage (CRUD, path traversal security, SHA-256 integrity, immutability)
  2. S3FileStorage (CRUD with mocked boto3 client, metadata, pre-signed URLs, error mappings)
  3. Storage Backend Factory & Fail-Closed Configuration Validation
"""

from __future__ import annotations

import hashlib
import os
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import ClientError

from app.core.config import Settings
from app.storage.base import FileStorageBackend, StoredFile
from app.storage.factory import create_storage_backend
from app.storage.local import LocalFileStorage, PathTraversalError
from app.storage.s3 import S3FileStorage, S3StorageError


# ── 1. LocalFileStorage Unit Tests ────────────────────────────


@pytest.mark.asyncio
async def test_local_storage_store_and_retrieve(tmp_path: Path) -> None:
    """Local storage stores file bytes, calculates SHA-256, and retrieves identical bytes."""
    storage = LocalFileStorage(base_dir=tmp_path)
    assert storage.backend_name == "local"

    content = b"wavelength,absorbance\n300,0.12\n350,0.45\n400,0.89\n"
    expected_hash = hashlib.sha256(content).hexdigest()
    dest_path = "projects/P1/experiments/E1/samples/S1/ch1/spectrum.csv"

    stored = await storage.store(
        content=content,
        destination_path=dest_path,
        original_filename="spectrum.csv",
        content_type="text/csv",
    )

    assert isinstance(stored, StoredFile)
    assert stored.checksum_sha256 == expected_hash
    assert stored.file_size_bytes == len(content)
    assert stored.storage_backend == "local"
    assert stored.content_type == "text/csv"
    assert await storage.exists(stored.stored_path) is True

    # Retrieve and verify bytes
    retrieved = await storage.retrieve(stored.stored_path)
    assert retrieved == content

    # Check metadata
    meta = await storage.get_metadata(stored.stored_path)
    assert meta["size_bytes"] == len(content)
    assert meta["backend"] == "local"

    # Pre-signed url returns None for local storage
    url = await storage.generate_download_url(stored.stored_path)
    assert url is None

    # Delete
    await storage.delete(stored.stored_path)
    assert await storage.exists(stored.stored_path) is False


@pytest.mark.asyncio
async def test_local_storage_immutability(tmp_path: Path) -> None:
    """Storing to an existing destination path raises FileExistsError."""
    storage = LocalFileStorage(base_dir=tmp_path)
    content = b"initial data"
    dest_path = "P1/E1/S1/ch1/file.csv"

    await storage.store(content=content, destination_path=dest_path, original_filename="file.csv")

    with pytest.raises(FileExistsError, match="Raw files are immutable"):
        await storage.store(content=b"new data", destination_path=dest_path, original_filename="file.csv")


@pytest.mark.asyncio
async def test_local_storage_path_traversal_prevention(tmp_path: Path) -> None:
    """Attempting path traversal outside root storage directory raises PathTraversalError."""
    storage = LocalFileStorage(base_dir=tmp_path)

    with pytest.raises(PathTraversalError):
        await storage.store(
            content=b"malicious content",
            destination_path="../../../etc/passwd",
            original_filename="attack.txt",
        )

    with pytest.raises(PathTraversalError):
        await storage.retrieve("../../../etc/shadow")


# ── 2. S3FileStorage Unit Tests ───────────────────────────────


@pytest.mark.asyncio
async def test_s3_storage_store_and_retrieve() -> None:
    """S3 storage correctly calls put_object with metadata and get_object on retrieve."""
    with patch("boto3.client") as mock_boto:
        mock_s3 = MagicMock()
        mock_boto.return_value = mock_s3

        # Configure head_object to raise 404 (object does not exist initially)
        mock_s3.head_object.side_effect = ClientError(
            {"Error": {"Code": "404", "Message": "Not Found"}}, "HeadObject"
        )
        mock_s3.put_object.return_value = {"ETag": '"abcdef123456"'}

        content = b"2theta,intensity\n20,100\n30,500\n"
        expected_hash = hashlib.sha256(content).hexdigest()
        dest_key = "projects/P1/experiments/E1/samples/S1/ch1/xrd.csv"

        storage = S3FileStorage(
            bucket="test-bucket",
            region="us-east-1",
            access_key_id="test_key",
            secret_access_key="test_secret",
        )
        assert storage.backend_name == "s3"

        stored = await storage.store(
            content=content,
            destination_path=dest_key,
            original_filename="xrd.csv",
            content_type="text/csv",
        )

        assert stored.checksum_sha256 == expected_hash
        assert stored.storage_backend == "s3"
        assert stored.bucket == "test-bucket"
        assert stored.etag == "abcdef123456"

        mock_s3.put_object.assert_called_once()
        call_kwargs = mock_s3.put_object.call_args[1]
        assert call_kwargs["Bucket"] == "test-bucket"
        assert call_kwargs["Key"] == dest_key
        assert call_kwargs["ContentType"] == "text/csv"
        assert call_kwargs["Metadata"]["sha256"] == expected_hash

        # Test retrieve
        mock_s3.get_object.return_value = {
            "Body": MagicMock(read=MagicMock(return_value=content))
        }
        retrieved = await storage.retrieve(dest_key)
        assert retrieved == content

        # Test pre-signed URL
        mock_s3.generate_presigned_url.return_value = "https://s3.amazonaws.com/test-bucket/key?token=123"
        url = await storage.generate_download_url(dest_key, expiry_seconds=1800)
        assert url == "https://s3.amazonaws.com/test-bucket/key?token=123"

        # Test delete
        await storage.delete(dest_key)
        mock_s3.delete_object.assert_called_once_with(Bucket="test-bucket", Key=dest_key)


@pytest.mark.asyncio
async def test_s3_storage_immutability_and_errors() -> None:
    """S3 storage rejects overwrite if object already exists and maps NoSuchKey to FileNotFoundError."""
    with patch("boto3.client") as mock_boto:
        mock_s3 = MagicMock()
        mock_boto.return_value = mock_s3

        # When head_object succeeds, object exists
        mock_s3.head_object.return_value = {"ContentLength": 100}

        storage = S3FileStorage(
            bucket="test-bucket",
            region="us-east-1",
            access_key_id="k",
            secret_access_key="s",
        )

        with pytest.raises(FileExistsError, match="Object already exists in S3"):
            await storage.store(
                content=b"new data",
                destination_path="projects/P1/data.csv",
                original_filename="data.csv",
            )

        # Test retrieve missing key
        mock_s3.get_object.side_effect = ClientError(
            {"Error": {"Code": "NoSuchKey", "Message": "The specified key does not exist."}},
            "GetObject",
        )
        with pytest.raises(FileNotFoundError, match="Raw file not found in S3"):
            await storage.retrieve("missing/path/file.csv")


# ── 3. Factory & Validation Unit Tests ─────────────────────────


def test_storage_factory_local() -> None:
    """Factory correctly instantiates LocalFileStorage for storage_backend='local'."""
    settings = Settings(storage_backend="local", raw_data_dir="./data/raw")
    backend = create_storage_backend(settings)
    assert isinstance(backend, LocalFileStorage)
    assert backend.backend_name == "local"


def test_storage_factory_s3_success() -> None:
    """Factory instantiates S3FileStorage when valid S3 credentials are provided."""
    settings = Settings(
        storage_backend="s3",
        s3_bucket="prod-raw-bucket",
        s3_region="us-west-2",
        s3_access_key_id="test_key_id",
        s3_secret_access_key="test_secret_key",
    )
    with patch("boto3.client"):
        backend = create_storage_backend(settings)
        assert isinstance(backend, S3FileStorage)
        assert backend.backend_name == "s3"


def test_storage_factory_s3_fail_closed() -> None:
    """Factory raises ValueError if storage_backend='s3' but credentials are missing."""
    settings = Settings(
        storage_backend="s3",
        s3_bucket="prod-bucket",
        s3_access_key_id="",  # Missing credentials
        s3_secret_access_key="",
    )
    with pytest.raises(ValueError, match="STORAGE_BACKEND='s3' requires S3_ACCESS_KEY_ID"):
        create_storage_backend(settings)
