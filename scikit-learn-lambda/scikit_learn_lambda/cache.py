import pickle
import os
import tempfile

import boto3
import joblib

from . import s3_url


def load_model_from_file(model_file):
    if model_file.endswith(".pkl") or model_file.endswith(".pickle"):
        with open(model_file, "rb") as f:
            return pickle.load(f)
    elif model_file.endswith(".joblib"):
        return joblib.load(model_file)


def load_model_from_path(model_path):
    if model_path.startswith("s3://"):
        url = s3_url.S3Url(model_path)
        obj = boto3.resource("s3").Object(url.bucket, url.key)
        with tempfile.TemporaryDirectory() as td:
            local_path = os.path.join(td, url.filename)
            obj.download_file(local_path)
            return load_model_from_file(local_path)
    else:
        return load_model_from_file(model_path)


class Cache:
    __instance = None

    @staticmethod
    def get():
        if Cache.__instance is None:
            Cache.__instance = load_model_from_path(os.environ["SKLEARN_MODEL_PATH"])

        return Cache.__instance

    @staticmethod
    def clear():
        Cache.__instance = None
