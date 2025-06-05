import sys
import json
import os
import logging
import argparse # For formal command-line argument parsing
# Set up basic logging configuration
# # This ensures logs from all modules (loader, hooks, executor, state_tracker) are captured
logging.basicConfig(level=logging.INFO, # Default logging level
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import components from your pipeline package
from pipeline.loader import load_pipeline_definition, load_dataset
from pipeline.executor import PipelineExecutor
 # Ensure state_tracker is imported, although its function is called by Executor
from pipeline.state_tracker import record_state_transition 

def run_pipeline(pipeline_path: str, dataset_path: str, output_path: str, script_dir: str):
        """
        Orchestrates the entire pipeline execution process.

        Args:
            pipeline_path (str): Path to the JSON file defining the pipeline structure.
            dataset_path (str): Path to the JSON file containing the input dataset.
            output_path (str): Path to the JSON file where the final processed results (state table) will be saved.
            script_dir (str): Directory containing all transformation scripts (pre, main, post).
        """
        logger.info(f"Starting pipeline run with parameters:")
        logger.info(f"  - Pipeline Definition: {pipeline_path}")
        logger.info(f"  - Input Dataset: {dataset_path}")
        logger.info(f"  - Output Results: {output_path}")
        logger.info(f"  - Script Directory: {script_dir}")

        pipeline_definition = {}
        dataset = []
        executor = None

        try:
            # Load pipeline definition and dataset
            pipeline_definition = load_pipeline_definition(pipeline_path)
            dataset = load_dataset(dataset_path)

            # Initialize the pipeline executor
            executor = PipelineExecutor(pipeline_definition)

            # Execute the pipeline
            logger.info("Executing pipeline on dataset...")
            results = executor.execute(dataset, script_dir)
            logger.info("Pipeline execution finished.")

            # Ensure the output directory exists before writing the results
            output_directory = os.path.dirname(output_path)
            if output_directory: # Only try to create if output_path is not just a filename
                os.makedirs(output_directory, exist_ok=True)
                logger.info(f"Ensured output directory exists: {output_directory}")

            # Write the results to the output file
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2)
            logger.info(f"Pipeline results successfully saved to: {output_path}")

        except FileNotFoundError as e:
            logger.critical(f"A required file was not found: {e}")
            sys.exit(1) # Exit with an error code
        except json.JSONDecodeError as e:
            logger.critical(f"Invalid JSON format detected in a configuration or data file: {e}")
            sys.exit(1)
        except ValueError as e:
            logger.critical(f"Configuration error: {e}")
            sys.exit(1)
        except TypeError as e:
            logger.critical(f"Type mismatch error during pipeline setup or execution: {e}")
            sys.exit(1)
        except Exception as e:
            logger.critical(f"An unexpected critical error occurred during pipeline execution: {e}", exc_info=True)
            sys.exit(1) # Exit with a generic error code

if __name__ == "__main__":
        # Use argparse for robust command-line argument parsing
        parser = argparse.ArgumentParser(
            description="Run a data processing pipeline based on a defined structure."
        )
        parser.add_argument("pipeline_path", type=str,
                            help="Path to the JSON file defining the pipeline structure.")
        parser.add_argument("dataset_path", type=str,
                            help="Path to the JSON file containing the input dataset.")
        parser.add_argument("output_path", type=str,
                            help="Path to the JSON file where the final processed results (state table) will be saved.")
        parser.add_argument("script_dir", type=str,
                            help="Directory containing all transformation scripts (pre, main, post).")

        args = parser.parse_args()

        # Call the main pipeline function with parsed arguments
        run_pipeline(args.pipeline_path, args.dataset_path, args.output_path, args.script_dir)

