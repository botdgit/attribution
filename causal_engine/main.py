"""Main entry point for causal engine models."""
import argparse
import json
import logging
import sys
from typing import Dict, Any

from causal_engine.base import model_registry


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def main():
    """Main function to run causal engine models."""
    parser = argparse.ArgumentParser(description="Run causal engine models")
    parser.add_argument("--client-id", required=True, help="Client identifier")
    parser.add_argument("--model", required=True, help="Model name to run")
    parser.add_argument("--params", default="{}", help="JSON string of model params")
    
    args = parser.parse_args()
    
    try:
        # Parse parameters
        params = json.loads(args.params)
        
        # Get model class from registry
        model_class = model_registry.get_model(args.model)
        if not model_class:
            available_models = model_registry.list_models()
            logger.error(f"Unknown model: {args.model}. Available models: {available_models}")
            sys.exit(1)
        
        # Initialize and run model
        logger.info(f"Starting {args.model} model for client {args.client_id}")
        model = model_class(args.client_id, params)
        result = model.run()
        
        # Log result
        if result["status"] == "success":
            logger.info(f"Model completed successfully: {result}")
            sys.exit(0)
        else:
            logger.error(f"Model failed: {result}")
            sys.exit(1)
            
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in params: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()