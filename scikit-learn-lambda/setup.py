from setuptools import find_packages, setup

setup(
    name="scikit-learn-lambda",
    version="0.1.0",
    author="Model Zoo, Inc.",
    install_requires=["scikit-learn", "joblib", "boto3"],
    packages=find_packages(),
    description="A handler for scikit learn models on AWS Lambda",
    author_email="contact@modelzoo.dev",
    license="Apache 2.0",
    url="https://www.modelzoo.dev",
    classifiers=[
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: Implementation :: PyPy",
    ],
    test_suite="tests",
    python_requires=">=3.6",
)
