import os
import tempfile
import json

import boto3
import moto
import pytest

from scikit_learn_lambda import cache, handler


def apigw_event(input_data, return_prediction=True, return_probabilities=False):
    """ Generates a minimal API GW Event"""

    return {
        "body": json.dumps(
            {
                "input": input_data,
                "return_prediction": return_prediction,
                "return_probabilities": return_probabilities,
            }
        )
    }


@pytest.fixture(scope="function")
def clear_cache():
    """ Clears the singleton cache instance in between tests. """
    yield
    cache.Cache.clear()


def test_invalid_s3_model_path(monkeypatch, clear_cache):
    monkeypatch.setenv("SKLEARN_MODEL_PATH", "s3://invalid-bucket/invalid-model-path")

    with moto.mock_s3():
        ret = handler(apigw_event([0]), None)

    assert json.loads(ret["body"])["error"]
    assert ret["statusCode"] == 500


def test_invalid_local_path(monkeypatch, clear_cache):
    monkeypatch.setenv("SKLEARN_MODEL_PATH", "file/doesnt/exist")
    ret = handler(apigw_event([0]), None)

    assert json.loads(ret["body"])["error"]
    assert ret["statusCode"] == 500


def test_invalid_file(monkeypatch, clear_cache):
    with tempfile.TemporaryDirectory() as td:
        filepath = os.path.join(td, "model.joblib")

        monkeypatch.setenv("SKLEARN_MODEL_PATH", filepath)
        with open(os.path.join(td, "model.joblib"), "wb") as f:
            f.write(b"invalid file")

        ret = handler(apigw_event([0]), None)

    assert json.loads(ret["body"])["error"]
    assert ret["statusCode"] == 500


def _get_testdata_path(filename):
    return os.path.join(os.path.dirname(__file__), "..", "..", "testdata", filename)


def test_invalid_request(monkeypatch, clear_cache):
    monkeypatch.setenv("SKLEARN_MODEL_PATH", _get_testdata_path("mlp.joblib"))
    ret = handler({"body": json.dumps({"bad": "request"})}, None)
    response = json.loads(ret["body"])
    assert ret["statusCode"] == 400, response["error"]


def test_svm(monkeypatch, clear_cache):
    monkeypatch.setenv("SKLEARN_MODEL_PATH", _get_testdata_path("svm.joblib"))
    ret = handler(apigw_event([[0, 0, 0, 0]]), None)
    response = json.loads(ret["body"])
    assert ret["statusCode"] == 200, response["error"]
    assert len(response["prediction"]) == 1
    assert isinstance(response["prediction"][0], int)


def test_svm_probabilities(monkeypatch, clear_cache):
    monkeypatch.setenv("SKLEARN_MODEL_PATH", _get_testdata_path("svm.joblib"))
    ret = handler(apigw_event([[0, 0, 0, 0]], return_probabilities=True), None)
    response = json.loads(ret["body"])
    assert ret["statusCode"] == 200, response["error"]
    assert len(response["prediction"]) == 1
    assert isinstance(response["prediction"][0], int)
    assert len(response["probabilities"]) == 1
    assert list(response["probabilities"][0].keys()) == ["0", "1", "2"]


def test_svm_s3(monkeypatch, clear_cache):
    monkeypatch.setenv("SKLEARN_MODEL_PATH", "s3://test-bucket/svm.joblib")

    with moto.mock_s3():
        s3_client = boto3.client("s3")
        s3_client.create_bucket(Bucket="test-bucket")
        s3_client.upload_file(
            _get_testdata_path("svm.joblib"), "test-bucket", "svm.joblib"
        )
        ret = handler(apigw_event([[0, 0, 0, 0]]), None)

    response = json.loads(ret["body"])
    assert ret["statusCode"] == 200, response["error"]
    assert len(response["prediction"]) == 1
    assert isinstance(response["prediction"][0], int)


def test_mlp(monkeypatch, clear_cache):
    monkeypatch.setenv("SKLEARN_MODEL_PATH", _get_testdata_path("mlp.joblib"))
    ret = handler(apigw_event([[0] * 4]), None)
    response = json.loads(ret["body"])
    assert ret["statusCode"] == 200, response["error"]
    assert len(response["prediction"]) == 1
    assert isinstance(response["prediction"][0], int)


def test_mlp_return_probablilities(monkeypatch, clear_cache):
    monkeypatch.setenv("SKLEARN_MODEL_PATH", _get_testdata_path("mlp.joblib"))
    ret = handler(apigw_event(input_data=[[0] * 4], return_probabilities=True), None)
    response = json.loads(ret["body"])
    assert ret["statusCode"] == 200, response["error"]
    assert len(response["probabilities"]) == 1
    assert list(response["probabilities"][0].keys()) == ["0", "1", "2"]


def test_mlp_pickle(monkeypatch, clear_cache):
    monkeypatch.setenv("SKLEARN_MODEL_PATH", _get_testdata_path("mlp.pickle"))
    ret = handler(apigw_event([[0] * 4]), None)
    response = json.loads(ret["body"])
    assert ret["statusCode"] == 200, response["error"]
    assert len(response["prediction"]) == 1
    assert isinstance(response["prediction"][0], int)
