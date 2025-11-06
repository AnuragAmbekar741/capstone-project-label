import os, tempfile, boto3, shutil, hashlib
from botocore.client import Config
from botocore.exceptions import ClientError
from tenacity import retry, wait_exponential, stop_after_attempt
from .config import settings

def _b(s: str) -> bytes: return s.encode("utf-8")

class StorageClient:
    """
    For +bucket_per_user: bucket == user_id, prefix == ""
    For +single_bucket:   bucket == ADAPTER_BUCKET, prefix == f"{user_id}/"
    Provides:
      - remote_version(user_id): stable version string derived from keys+etags
      - download_adapter_folder(user_id): downloads all objects into /tmp/<uid>_<ver>_<rand>
    """
    def __init__(self):
        self.impl = settings.object_store_impl
        self.layout = os.getenv("LORA_LAYOUT", "single_bucket").lower()
        self.adapter_bucket = settings.adapter_bucket
        self.object_store_url = settings.object_store_url

        if self.impl in ("s3", "minio"):
            use_path_style = os.getenv("MINIO_PATH_STYLE", "true").lower() in ("1","true","yes")
            verify_ssl = os.getenv("S3_VERIFY_SSL", "true").lower() in ("1","true","yes")
            self.s3 = boto3.client(
                "s3",
                endpoint_url=self.object_store_url,
                config=Config(signature_version="s3v4", s3={"addressing_style": "path"} if use_path_style else None),
                verify=verify_ssl,
            )
        else:
            self.s3 = None

    def _bucket_prefix(self, user_id: str):
        if self.layout == "bucket_per_user":
            return user_id, ""
        return self.adapter_bucket, f"{user_id}/"

    @retry(wait=wait_exponential(min=1, max=8), stop=stop_after_attempt(3))
    def remote_version(self, user_id: str) -> str:
        """
        Returns a stable version string (hex) for user's adapter by hashing key+etag for all objects.
        Local mode: hash filenames + mtimes.
        """
        h = hashlib.sha256()
        if self.impl == "local":
            if self.layout == "bucket_per_user":
                base = os.path.join(os.getenv("LOCAL_BUCKETS_DIR", "."), user_id)
            else:
                base = os.path.join(settings.adapter_bucket, user_id)
            if not os.path.isdir(base):
                raise FileNotFoundError(f"Adapter directory not found: {base}")
            for root, _, files in os.walk(base):
                for f in sorted(files):
                    p = os.path.join(root, f)
                    st = os.stat(p)
                    h.update(_b(f"{f}:{int(st.st_mtime)}:{st.st_size}"))
            return h.hexdigest()

        # S3/MinIO
        bucket, prefix = self._bucket_prefix(user_id)
        resp = self.s3.list_objects_v2(Bucket=bucket, Prefix=prefix)
        if "Contents" not in resp:
            raise FileNotFoundError(f"No adapter files in {bucket}/{prefix}")
        for obj in sorted(resp["Contents"], key=lambda x: x["Key"]):
            key = obj["Key"]
            # ETag is usually quoted md5; include size to be safe
            etag = obj.get("ETag", "").strip('"')
            size = obj.get("Size", 0)
            h.update(_b(f"{key}:{etag}:{size}"))
        return h.hexdigest()

    @retry(wait=wait_exponential(min=1, max=8), stop=stop_after_attempt(3))
    def download_adapter_folder(self, user_id: str, remote_ver: str) -> str:
        """
        Downloads all adapter files into /tmp/<user>_<ver>_<rand> and returns that dir.
        """
        tmp_dir = tempfile.mkdtemp(prefix=f"{user_id}_{remote_ver[:8]}_")
        if self.impl == "local":
            if self.layout == "bucket_per_user":
                src = os.path.join(os.getenv("LOCAL_BUCKETS_DIR", "."), user_id)
            else:
                src = os.path.join(settings.adapter_bucket, user_id)
            if not os.path.isdir(src):
                raise FileNotFoundError(f"Adapter directory not found: {src}")
            for root, _, files in os.walk(src):
                for f in files:
                    shutil.copy(os.path.join(root, f), os.path.join(tmp_dir, f))
            return tmp_dir

        bucket, prefix = self._bucket_prefix(user_id)
        resp = self.s3.list_objects_v2(Bucket=bucket, Prefix=prefix)
        if "Contents" not in resp:
            raise FileNotFoundError(f"No adapter files in {bucket}/{prefix}")
        for obj in resp["Contents"]:
            key = obj["Key"]
            if key.endswith("/"): continue
            fname = key.split("/")[-1]
            dst = os.path.join(tmp_dir, fname)
            self.s3.download_file(bucket, key, dst)
        return tmp_dir
