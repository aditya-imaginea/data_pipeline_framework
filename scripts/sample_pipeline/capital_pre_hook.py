def transform(record):
    country = record.get("country", "")
    capital = record.get("capital", "")
    record["statement"] = f"The capital of {country} is {capital}."
    return record
