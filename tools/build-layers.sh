#!/bin/bash
#
# This script builds AWS lambda layers that contain the scikit-learn and joblib
# dependency for arbitrary versions of Python and scikit-learn. By default, it
# builds for Python 3.6 - 3.8 and scikit-learn versions 0.22+, and publishes to
# all US regions. The dependency size is optimized by removing some unnecessary
# files from site-packages (__pycache__, *.pyc, tests...).
#
# Prerequisities: Install the AWS cli, jq, and Docker
#
# Example 1: Build lambda layers for all combinations of scikit learn and
# Python versions and publish to all US regions.
#  ./build-layers.sh
#
# Example 2: Build lambda layer for Python 3.7 and scikit-learn 0.23.0, publish
# to us-west-2.
#  ./build-layers.sh --python=3.7 --scikit-learn==0.23.0 --region=us-west-2

set -e
set -o pipefail

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
BUILD_CACHE_DIR="${SCRIPT_DIR}/build"
OUTPUT_CSV="layers.csv"

for arg in "$@"
do
    case $arg in
        --python=*) declare -a PYTHON_VERSIONS=("${arg#*=}") shift;;
        --scikit-learn=*) declare -a SKLEARN_VERSIONS=("${arg#*=}") shift;;
        --region=*) declare -a REGIONS=("${arg#*=}") shift;;
        --output-csv=*) declare OUTPUT_CSV="${arg#*=}" shift;;
        --public) declare PUBLIC=true shift;;
        *) echo "ERROR: Invalid argument ${arg}" && exit 1;;
    esac
done

if [ -f ${OUTPUT_CSV} ]; then
   echo "Warning: output CSV file ${OUTPUT_CSV} will be overwritten!"
    read -p "Are you sure (y/n)? " choice
    case "$choice" in
      y|Y ) echo "yes";;
      n|N ) exit 1;;
      * ) exit 1;;
    esac
fi
OUTPUT_CSV=$(realpath ${OUTPUT_CSV})

if [ -z "$SKLEARN_VERSIONS" ]
then
    declare -a SKLEARN_VERSIONS=("0.22.0" "0.22.1" "0.22.2.post1" "0.23.0" "0.23.1")
fi
echo "Using scikit-learn version(s) $SKLEARN_VERSIONS"

if [ -z "$PYTHON_VERSIONS" ]
then
    declare -a PYTHON_VERSIONS=("3.6" "3.7" "3.8")
fi
echo "Using Python version(s) $PYTHON_VERSIONS"

if [ -z "$REGIONS" ]
then
    declare -a REGIONS=("us-east-1" "us-east-2" "us-west-1" "us-west-2")
fi
echo "Publishing to region(s) $REGIONS"

mkdir -p ${BUILD_CACHE_DIR}
rm -rf ${BUILD_CACHE_DIR}/*
echo "Python version,scikit-learn version,region,arn" > "${OUTPUT_CSV}"

for s in "${SKLEARN_VERSIONS[@]}"
do
    for p in "${PYTHON_VERSIONS[@]}"
    do
        echo "Building layer for python $p and scikit-learn $s..."
        docker run \
            -v ${SCRIPT_DIR}:/var/task \
            "lambci/lambda:build-python$p" \
            /var/task/install-pip-packages.sh "scikit-learn==${s} joblib" /var/task/build/python/lib/python${p}/site-packages

        layer_name=$(echo "python-${p}-scikit-learn-${s}" | tr '.' '-')
        zip_name="scikit-learn-${sklearn_version}.zip"
        cd ${BUILD_CACHE_DIR} && zip -r9 ${zip_name} python && cd ..

        for r in "${REGIONS[@]}";
        do
            layer_version_info=$(aws lambda publish-layer-version \
                --region "${r}" \
                --layer-name "${layer_name}" \
                --zip-file "fileb://${BUILD_CACHE_DIR}/${zip_name}" \
                --compatible-runtimes "python${p}" \
                --license-info MIT)
            layer_arn=$(echo ${layer_version_info} | jq -r ".LayerArn")

            echo "Created layer: ${layer_version_info}"
            if [ "${PUBLIC}" = true ]; then
                layer_version_number=$(echo ${layer_version_info} | jq -r ".Version")
                layer_version_policy=$(aws lambda add-layer-version-permission \
                    --region "${r}" \
                    --layer-name ${layer_name} \
                    --statement-id public-statement \
                    --action lambda:GetLayerVersion \
                    --principal "*" \
                    --version-number "${layer_version_number}" | jq)
                echo "Added layer version policy: ${layer_version_policy}"
            fi

            echo "${p},${s},${r},${layer_arn}:${layer_version_number}" >> "${OUTPUT_CSV}"
        done

        # Clean out cache for the next layer.
        rm -rf ${BUILD_CACHE_DIR}/*
    done
done
