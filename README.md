# 🧠 Data Pipeline Framework (Dockerized + AI-Validated)

A modular, Dockerized data pipeline framework that allows users to define, submit, and validate data pipelines using OpenAI for transformation accuracy. Includes REST API for dynamic pipeline submissions.

---

## 🚀 Features

- ✅ Modular pre-hook, transform, and post-hook logic
- 🐳 Docker-based batch processing (parallel per 100 records)
- 🧾 OpenAI integration for data validation
- 🛠️ REST API (FastAPI) to submit and fetch pipeline results
- 📂 Auto-generated Swagger docs at `/docs`
- 📦 Git-friendly structure with test coverage

---

## 📁 Project Structure

```
data_pipeline_framework/
├── api/
│   └── main.py                # FastAPI entrypoint
├── batches/                   # Auto-generated data batches
├── pipeline/
│   ├── engine.py              # Core pipeline execution
│   └── loader.py              # Loads pipeline definitions & datasets
├── scripts/sample_pipeline/
│   ├── capital_pre_hook.py
│   ├── capital_transform.py
│   └── capital_post_hook.py
├── datasets/
│   └── sample_dataset.json
├── storage/
│   └── pipeline_definitions/
│       └── pipeline_definition.json
├── output/
│   └── aggregated_results/    # Final results per request_id
├── Dockerfile
├── requirements.txt
├── batch_runner.py
└── README.md
```

---

## 🧪 Example Record Format

### ✅ Valid
```json
{"id": "100", "country": "India", "capital": "Delhi"}
```

### ❌ Invalid
```json
{"id": "101", "country": "UK", "capital": "Islamabad"}
```

---

## ⚙️ Setup

### ▶️ Local Setup

```bash
# 1. Clone the repo
git clone https://github.com/your-username/data_pipeline_framework.git
cd data_pipeline_framework

# 2. Set up virtualenv
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# 3. Run API
uvicorn api.main:app --reload
```

### 🐳 Docker Setup

```bash
# Build the Docker image
docker build -t data-pipeline:latest .

# Run pipeline using Docker
python batch_runner.py
```

---

## 🔑 Environment Variables

Set your OpenAI key locally or via Docker:

### Local
```bash
export OPENAI_API_KEY=your-key
```

### Docker
Pass as environment variable:
```bash
docker run -e OPENAI_API_KEY=your-key ...
```

---

## 🌐 API Endpoints

### 📤 `POST /submit_pipeline`

Submit your dataset and pipeline for processing.

- `pipeline_file`: JSON file
- `dataset_file`: JSON file

✅ Response:
```json
{ "request_id": "abc123" }
```

---

### 📥 `GET /get_result/{request_id}`

Returns the aggregated result for a given request ID.

✅ Response:
```json
{
  "results": [
    { "id": "100", "result": "valid work" },
    ...
  ]
}
```

---

## 🧠 Powered By

- [FastAPI](https://fastapi.tiangolo.com/)
- [Docker](https://www.docker.com/)
- [OpenAI Python SDK](https://github.com/openai/openai-python)
- [Uvicorn](https://www.uvicorn.org/)

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Submit a PR 🙌

---

## 📄 License

MIT License — feel free to use with attribution.

---

## 📬 Questions?

Ping `aditya.palagummi@yourdomain.com` or open an issue.
