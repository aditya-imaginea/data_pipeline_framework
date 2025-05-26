# 🛠️ Data Pipeline Framework

This project is a flexible and extensible data pipeline framework designed to support batch processing of data using pre-hooks, main transformations, and post-hooks. It supports concurrent execution using Docker and includes OpenAI-based validation for intelligent transformation steps.

---

## 🚀 Features

- 🔄 Modular pipeline with configurable `pre`, `main`, and `post` hooks
- 📦 Batch processing: processes data in 100-record chunks
- 🐳 Docker-based isolation for parallel execution
- 🤖 OpenAI integration for semantic validation
- ✅ Unit and integration test support
- 📁 Simple JSON-based pipeline definitions and datasets

---

## 📂 Project Structure

```
data_pipeline_framework/
│
├── pipeline/                      # Core pipeline engine
│   ├── engine.py                  # Main execution logic
│   ├── executor.py                # Executes steps for each record
│   ├── loader.py                  # Loads datasets and pipeline definitions
│   └── state_tracker.py          # Logs transformation states
│
├── scripts/                       # Scripts used in pipeline steps
│   └── sample_pipeline/
│       ├── capital_pre_hook.py
│       ├── capital_transform.py
│       └── capital_post_hook.py
│
├── datasets/
│   └── sample_dataset.json       # Input dataset with correct/incorrect records
│
├── storage/
│   └── pipeline_definitions/
│       └── pipeline_definition.json
│
├── state_logs/                   # Output from pipeline steps
│
├── tests/
│   └── test_pipeline_execution.py
│
├── batch_runner.py               # Orchestrates batch-wise processing in Docker
├── Dockerfile                    # Builds image for processing batches
├── requirements.txt              # Python dependencies
└── README.md
```

---

## 🧪 Running Tests

To run tests using `pytest`:

```bash
pytest tests/
```

---

## 🐳 Docker Usage

### Build Docker Image

```bash
docker build -t data-pipeline:latest .
```

### Run Batch Processing

```bash
python batch_runner.py
```

Each batch spawns a separate Docker container, and the logs are stored in `state_logs/`.

---

## 🔑 Environment Variables

Set the OpenAI API key before running:

### Locally:
```bash
export OPENAI_API_KEY=your_openai_key
```

### In Docker (e.g. in `batch_runner.py`):

Add to the `cmd` block:
```python
"-e", "OPENAI_API_KEY"
```

---

## 🧠 OpenAI Integration

The framework uses OpenAI for:

- Validating the factual accuracy of input data (`capital_transform.py`)
- Assessing correctness of transformations (`capital_post_hook.py`)

Ensure you have proper access to a valid OpenAI model (`gpt-3.5-turbo`, `gpt-4`, etc.).

---

## 📝 Sample Dataset Format

```json
[
  {"id": "100", "country": "India", "capital": "Delhi"},
  {"id": "101", "country": "UK", "capital": "Islamabad"} // Incorrect capital
]
```

---

## 🔧 Pipeline Definition

```json
{
  "steps": [
    {
      "name": "capital_step",
      "pre_script": "scripts/sample_pipeline/capital_pre_hook.py",
      "main_script": "scripts/sample_pipeline/capital_transform.py",
      "post_script": "scripts/sample_pipeline/capital_post_hook.py"
    }
  ]
}
```

---

## 📌 Notes

- Ensure all scripts have a `transform(record)` function.
- Output is logged per batch in the `state_logs/` folder.
- Update `requirements.txt` with necessary packages like `openai`.

---

## 📄 License

MIT License. See `LICENSE` file.
