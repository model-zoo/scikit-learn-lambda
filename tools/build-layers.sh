#!/bin/bash
#
# This script builds AWS lambda layers that contain the scikit-learn and joblib
# dependency. It supports building layers for Python versions 3.6 - 3.8, and
# scikit-learn versions 0.20 - 0.24. The dependency size is optimized by
# removing some unnecessary files from site-packages (__pycache__, *.pyc,
# tests...).
#
# Example 1: Build lambda layers for all combinations of scikit learn and
# Python versions.
#  ./build-layers.sh
#
# Example 2: Build lambda layer for Python 3.7 and scikit-learn 0.23.0.
#  ./build-layers.sh 0.23.0 3.7


set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
BUILD_CACHE_DIR="build"
INSTALL_SCRIPT="install-pip-package.sh"

mkdir -p ${SCRIPT_DIR}/${BUILD_CACHE_DIR}
rm -rf ${SCRIPT_DIR}/${BUILD_CACHE_DIR}/*

build_layer () {
    echo "Building layer for python $2 and scikit-learn $1..."
    docker run \
        -v ${SCRIPT_DIR}:/var/task \
        "lambci/lambda:build-python$2" \
        /var/task/${INSTALL_SCRIPT} "scikit-learn==${1} joblib" /var/task/build/python/lib/python${2}/site-packages
}

if [ -z "$1" ]
then
    declare -a SKLEARN_VERSIONS=("0.20.1" "0.20.2" "0.20.3" "0.20.4" "0.21.0" "0.21.1" "0.21.2" "0.21.3" "0.22.0" "0.22.1" "0.22.2.post1" "0.23.0" "0.23.1")
else
    declare -a SKLEARN_VERSIONS=("$1")
fi
echo "Using scikit-learn version(s) $SKLEARN_VERSIONS"

if [ -z "$2" ]
then
    declare -a PYTHON_VERSIONS=("3.6" "3.7" "3.8")
else
    declare -a PYTHON_VERSIONS=("$2")
fi
echo "Using Python version(s) $PYTHON_VERSIONS"

for sklearn_version in "${SKLEARN_VERSIONS[@]}"
do
    for python_version in "${PYTHON_VERSIONS[@]}"
    do
        build_layer ${sklearn_version} ${python_version}

        layer_name=$(echo "python-${python_version}-scikit-learn-${sklearn_version}" | tr '.' '-')
        zip_name="scikit-learn-${sklearn_version}.zip"
        cd ${SCRIPT_DIR}/${BUILD_CACHE_DIR} && \
            zip -r9 ${zip_name} python

        layer_version_info=$(aws lambda publish-layer-version \
            --layer-name "${layer_name}" \
            --zip-file "fileb://${SCRIPT_DIR}/${BUILD_CACHE_DIR}/${zip_name}" \
            --compatible-runtimes "python${python_version}" \
            --license-info MIT)

        echo "Created layer: ${layer_version_info}"

        # Clean out cache for the next layer.
        rm -rf ${SCRIPT_DIR}/${BUILD_CACHE_DIR}/*
    done
done
