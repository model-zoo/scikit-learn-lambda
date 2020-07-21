# scikit-lambda

scikit-lambda is a toolkit for deploying scikit-learn models to an HTTP
endpoint for realtime inference on AWS Lambda using
[Serverless](https://github.com/serverless/serverless) or [AWS
SAM](https://github.com/awslabs/serverless-application-model).

## Why should I use scikit-lambda?

* **Get started quickly** - `scikit-lambda` handles the boilerplate code for you,
  simply drop in a `joblib` or `pickle` model file and deploy.
* **Cost efficient** - The equivalent architecture on [AWS
  SageMaker](https://aws.amazon.com/sagemaker/) will cost you ~$50 per endpoint.
  Deploying on AWS lambda allows you to pay-per-request and not worry about
  the number of models you're deploying to production.
* **Built-in autoscaling** - Deploying on [Elastic Container
  Service](https://aws.amazon.com/ecs/) or [Kubernetes](https://kubernetes.io/)
  requires configuring and maintaining autoscaling groups. AWS Lambda abstracts
  this complexity away for you.

## Overview

scikit-lambda provides three components that can

1) `scikit-lambda`: A Python package that includes a handler for AWS Lambda
   that loads a `scikit-learn` model into memory and returns predictions.
2) A repository of Lambda layers for varous combinations of Python (3.6 - 3.8)
   and `scikit-learn` (0.20 - 0.23).
3) Example template configurations for deploying a model to an HTTP endpoint.

## Quickstart (Serverless)

You have two options for deploying a model with Serverless framework.

A) Package your model as part of the deployment package upload to AWS Lambda.
This option will require your model file to be under ~50 MB, but achieve the best
cold-start latency.

B) Store your model into Amazon S3 and load it from there on AWS Lambda
initialization. This option has no model size constraints.

#### Prerequisites

* [Install Serverless](https://www.serverless.com/framework/docs/providers/aws/guide/installation/)
* [Configure your AWS credentials](https://www.serverless.com/framework/docs/providers/aws/guide/credentials/)

#### Option A: Package the model together with your code (50 MB limit)

1) Clone the repository:

    git clone <git url> && cd <repo>

2) Copy your model pickle or joblib file to `sklearn-lambda/`, the same
directory that `serverless.yaml` is in. For testing purposes, we've included
some example models in `testdata/`

    cp testdata/svm.joblib sklearn-lambda/

3) Edit the `SKLEARN_MODEL_PATH` environment variable in `serverless.yaml` to
specify the path of your model file, relative to the `sklearn-lambda/` directory.

    environment:
      SKLEARN_MODEL_PATH: "svm.joblib"

4) Deploy your model.

    $ serverless deploy

5) Test the your endpoint with some example data:

    $ curl --header "Content-Type: application/json" \
      --request POST \
      --data '{"input":[[0, 0, 0, 0]]}' \
      https://<insert your api here>.execute-api.us-west-2.amazonaws.com/dev/predict
    $ {"prediction": [0]}

#### Option B: Load your model from Amazon S3

1) Clone the repository:

    git clone <git url> && cd <repo>

2) Upload your model to Amazon S3. For testing purposes, we've included some
example models in `testdata/`

    aws s3 cp testdata/svm.joblib s3://my-test-bucket/svm.joblib

3) Edit the `SKLEARN_MODEL_PATH` environment variable in `serverless.yaml` to
specify the location of your model file using an `s3://` scheme.

    environment:
      SKLEARN_MODEL_PATH: "s3://my-test-bucket/svm.joblib"

4) Deploy your model.

    $ serverless deploy

5) Test the your endpoint with some example data:

    $ curl --header "Content-Type: application/json" \
      --request POST \
      --data '{"input":[[0, 0, 0, 0]]}' \
      https://<insert your api here>.execute-api.us-west-2.amazonaws.com/dev/predict
    $ {"prediction": [0]}

## Layers

To get around a the [50 MB (zipped) deployment package
limit](https://docs.aws.amazon.com/lambda/latest/dg/gettingstarted-limits.html),
it is useful to create a distinct layer for the `scikit-learn` dependency. This
frees up more room in your deployment package for your model or other
dependencies.

`sklearn-lambda` comes with a pre-built set of AWS Lambda layers that include
`scikit-learn` and `joblib` that you can use out of the box on `us-west-2`.
These layers are hosted on the Model Zoo AWS account  with public permissions
for any AWS account to use. We also provide a script `tools/build-layers.sh`
that allows you to build and upload layers owned by your own AWS account.

#### Available Layers

#### Build your own layers

`tools/build-layers.sh` is a bash script that can be used to build one or more
AWS Lambda Layers with the `scikit-learn` and `joblib` dependencies.

_This script assumes you have Docker and the AWS cli installed on your machine._

_Example_: Build lambda layer for Python 3.7 and scikit-learn 0.23.0.

    ./build-layers.sh 0.23.0 3.7

_Example_: Build lambda layers for all combinations of Python 3.6 ~ 3.8 and
scikit-learn libraries.

    ./build-layers.sh


1)
See `tools/build-layers.sh`

## Expected HTTP Schema

Input:

* `input`: The input array-like value. Will be fed into `model.predict`
* `return_prediction` (default: `True`): Will return `prediction` in output if true.
* `return_probabilities` (default: `False`): Will return `probabilities` in output if true.

Output:

* `prediction`: Array-like prediction from `model.predict()`
* `probabilities`: Dictionary of class names to probabilities, from `model.predict_proba()`
