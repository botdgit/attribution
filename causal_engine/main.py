import argparse
import json
from causal_engine.models.did import DifferenceInDifferencesModel


def main():
    parser = argparse.ArgumentParser(description="Run causal engine models")
    parser.add_argument("--client-id", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--params", default="{}", help="JSON string of model params")
    args = parser.parse_args()
    params = json.loads(args.params)

    if args.model == "did":
        model = DifferenceInDifferencesModel(args.client_id, params)
    else:
        raise SystemExit(f"Unknown model: {args.model}")

    model.run()


if __name__ == "__main__":
    main()
