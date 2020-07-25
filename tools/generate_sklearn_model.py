import argparse
import os

import joblib
from sklearn.datasets import load_iris
from sklearn.neural_network import MLPClassifier


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--hidden-size", type=str, required=True)
    parser.add_argument("--output-dir", type=str, default=os.getcwd())
    args = parser.parse_args()

    hidden_layer_sizes = [int(s) for s in args.hidden_size.split(",")]

    X, y = load_iris(return_X_y=True)
    clf = MLPClassifier(hidden_layer_sizes=hidden_layer_sizes, max_iter=1)
    clf.fit(X, y)

    model_file_name = "mlp-{}.joblib".format("-".join(args.hidden_size.split(",")))
    joblib.dump(clf, os.path.join(args.output_dir, model_file_name))

