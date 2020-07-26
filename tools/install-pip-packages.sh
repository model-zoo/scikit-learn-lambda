#!/bin/bash
#
# Expects two arguments: a pip package and a target directory. Installs the pip
# package and removes unnecessary build artifacts from the resulting package.
#
# See documentation on ./build-layers.sh for more information.

set -e
set -x

PIP_PACKAGE=$1
TARGET_DIR=$2

pip install $PIP_PACKAGE -t $TARGET_DIR
find $TARGET_DIR -type f -name "*.so" | xargs -r strip
find $TARGET_DIR -type f -name "*.pyc" | xargs -r rm
find $TARGET_DIR -type d -name "__pycache__" | xargs -r rm -r
find $TARGET_DIR -type d -name "*.dist-info" | xargs -r rm -r
find $TARGET_DIR -type d -name "tests" | xargs -r rm -r
