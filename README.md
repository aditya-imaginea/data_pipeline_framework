# Data Pipeline Framework

This project enables users to build and execute custom data pipelines with stepwise scripts using a web-based form interface. It supports uploading dataset files, defining pipeline steps (with optional pre-hook and post-hook scripts), and processing data in batches using Docker containers.

---

## Features

* 📄 Upload datasets (JSON format)
* 🧩 Define pipeline steps with:

  * **Main Transformation Script** (required)
  * **Pre-Hook Script** (optional)
  * **Post-Hook Script** (optional)
* 🔄 Batch-based processing
* 🐳 Dockerized execution for each batch
* 📥 Aggregated results stored per request ID
* 🧠 Compatible with OpenAI API hooks

---

## Project Structure

```
project-root/
│
├── app/
│   ├── main.py               # FastAPI backend
│   ├── templates/index.html  # HTML UI
│   ├── static/script.js      # Form logic and submission
│   └── pipeline/
│       ├── engine.py         # Executes a pipeline on a dataset
│       ├── executor.py       # Runs pipeline logic stepwise
│       ├── loader.py         # Loads pipeline definition and dataset
├── batch_runner.py           # Splits dataset and runs pipeline per batch in Docker
├── Dockerfile
├── requirements.txt
└── README.md
```

---

## Setup Instructions

### Prerequisites

* Python 3.8+
* Docker
* Node.js (optional, if using build tools for frontend)

### Installation

```bash
git clone <repo-url>
cd data_pipeline_framework
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Build Docker Image

```bash
docker build -t data-pipeline-framework .
```

> This builds the Docker image used to run pipeline batches in isolated containers.

### Running the App

```bash
uvicorn app.main:app --reload
```

Then navigate to `http://localhost:8000` to use the form.

---

## Using the Form Interface

1. Fill out the pipeline form:

   * Upload your dataset (JSON file)
   * Add steps (Main script required, Pre/Post optional)
   * Specify batch size (e.g., 50)
2. Click **Submit** to send the pipeline definition and files.
3. Backend:

   * Saves scripts & files under a request UUID
   * Runs `batch_runner.py` in background using Docker per batch
   * Aggregates outputs

---

## File Upload Format

* **Dataset**: JSON list of objects
* **Pipeline JSON** (auto-generated from UI):

```json
{
  "name": "example_pipeline",
  "steps": [
    {
      "name": "validation_step",
      "pre_script": "pre_hook.py",
      "main_script": "main_transform.py",
      "post_script": "post_hook.py"
    }
  ]
}
```

---

## Developer Notes

### Submit Endpoint (`/submit_pipeline`)

* Accepts a `FormData` payload:

  * `pipeline`: JSON file
  * `dataset`: JSON file
  * `batch_size`: Integer
  * Script files with keys like `main_0`, `pre_0`, `post_0`

### Batch Runner

* Splits dataset into batch files
* Calls `engine.py` inside a Docker container:

```bash
docker run --rm -v "$PWD:/app" data-pipeline:latest \
  python pipeline/engine.py pipeline.json batch.json output.json scripts/
```

### Engine Script

* Loads the pipeline
* Applies step logic using the `PipelineExecutor`
* Saves a `state_table` JSON for each batch

---

## TODO / Enhancements

* Progress tracking UI
* Auth for upload endpoint
* Validation for uploaded scripts
* Support for multiple pipeline templates

---

## License

MIT License

---

## Author

Built by \[Aditya Palagummi] – PRs welcome!
