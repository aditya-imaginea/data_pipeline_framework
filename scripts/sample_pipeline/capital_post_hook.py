def transform(record):
    if record.get("is_factually_correct"):
        record["validation_status"] = "valid work"
    else:
        record["validation_status"] = "invalid work"
    return record
