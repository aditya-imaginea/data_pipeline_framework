import json
import os
import logging
from typing import Dict, List, Any

# Set up logging for this module
logger = logging.getLogger(__name__)

def load_pipeline_definition(pipeline_path: str) -> Dict[str, Any]:
    """
    Loads a pipeline definition from a specified JSON file.

    Args:
        pipeline_path (str): The path to the JSON file containing the pipeline definition.

    Returns:
        Dict[str, Any]: The loaded pipeline definition as a dictionary.

    Raises:
        FileNotFoundError: If the specified pipeline_path does not exist.
        json.JSONDecodeError: If the file content is not valid JSON.
        Exception: For any other unexpected errors during file loading.
    """
    if not os.path.exists(pipeline_path):
        logger.error(f"Pipeline definition file not found: {pipeline_path}")
        raise FileNotFoundError(f"Pipeline definition file not found: {pipeline_path}")
    
    try:
        with open(pipeline_path, 'r', encoding='utf-8') as f:
            pipeline_def = json.load(f)
        logger.info(f"Successfully loaded pipeline definition from: {pipeline_path}")
        return pipeline_def
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON format in pipeline definition file '{pipeline_path}': {e}")
        raise
    except Exception as e:
        logger.error(f"An unexpected error occurred while loading pipeline definition from '{pipeline_path}': {e}")
        raise

def load_dataset(dataset_path: str) -> List[Dict[str, Any]]:
    """
    Loads a dataset from a specified JSON file.
    Assumes the dataset is a JSON array of objects.

    Args:
        dataset_path (str): The path to the JSON file containing the dataset.

    Returns:
        List[Dict[str, Any]]: The loaded dataset as a list of dictionaries.

    Raises:
        FileNotFoundError: If the specified dataset_path does not exist.
        json.JSONDecodeError: If the file content is not valid JSON.
        Exception: For any other unexpected errors during file loading.
    """
    if not os.path.exists(dataset_path):
        logger.error(f"Dataset file not found: {dataset_path}")
        raise FileNotFoundError(f"Dataset file not found: {dataset_path}")

    try:
        with open(dataset_path, 'r', encoding='utf-8') as f:
            dataset = json.load(f)
        if not isinstance(dataset, list):
            logger.warning(f"Dataset file '{dataset_path}' did not load as a list. Assuming a single record.")
            dataset = [dataset] # Wrap single dict in a list for consistent processing
        logger.info(f"Successfully loaded dataset from: {dataset_path} with {len(dataset)} records.")
        return dataset
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON format in dataset file '{dataset_path}': {e}")
        raise
    except Exception as e:
        logger.error(f"An unexpected error occurred while loading dataset from '{dataset_path}': {e}")
        raise

