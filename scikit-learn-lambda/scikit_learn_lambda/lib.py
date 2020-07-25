import json

import numpy as np

from . import cache


def handler_response(status_code, response):
    body = json.dumps(response, sort_keys=True, default=str)
    return {
        "isBase64Encoded": False,
        "statusCode": status_code,
        "body": body,
    }


def convert_bytes_to_str(arr):
    # If the model response is a numpy byte-string, it cannot be serialized to
    # JSON as bytes. Assume a unicode encoding in this case.
    if isinstance(arr, np.ndarray) and arr.dtype.kind == "S":
        arr = arr.astype("U")
    return arr


def get_probabilities(model, input_):
    probabilities = model.predict_proba(input_)
    probabilities = convert_bytes_to_str(probabilities)
    classes = [str(c) for c in model.classes_]
    return [dict(zip(classes, p)) for p in probabilities]


def get_prediction(model, input_):
    prediction = model.predict(input_)
    prediction = convert_bytes_to_str(prediction)
    return prediction.tolist()


def handler(event, _):
    try:
        model = cache.Cache.get()
    except Exception as e:
        return handler_response(500, {"error": "Failed to load model: {}".format(e)})

    try:
        body = json.loads(event["body"])
    except Exception as e:
        return handler_response(
            400, {"error": "Failed to parse request body as JSON: {}".format(str(e))},
        )

    if "input" not in body:
        return handler_response(
            400,
            {"error": "Failed to find an 'input' key in request body: {}".format(body)},
        )

    return_prediction = body.get("return_prediction", True)
    return_probabilities = body.get("return_probabilities", False)

    if not (return_prediction or return_probabilities):
        return handler_response(
            400,
            {
                "error": "Must either specify return_prediction: True or "
                "return_probabilities: True"
            },
        )

    response = {}
    if return_prediction:
        try:
            response["prediction"] = get_prediction(model, body["input"])
        except Exception as e:
            return handler_response(
                500, {"error": "Failed to get model prediction: {}".format(str(e))},
            )

    if return_probabilities:
        try:
            response["probabilities"] = get_probabilities(model, body["input"])
        except Exception as e:
            return handler_response(
                500, {"error": "Failed to get model probabilities: {}".format(str(e))},
            )

    return handler_response(200, response)
