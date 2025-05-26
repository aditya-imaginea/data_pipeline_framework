from openai import OpenAI
import os

#openai.api_key = os.getenv("OPENAI_API_KEY")
#print("OPENAI_API_KEY inside container:", os.getenv("OPENAI_API_KEY"))

def transform(record):
    statement = record.get("statement", "")
    if not statement:
        record["validation_result"] = "Missing statement"
        return record

    prompt = f"Is the following statement factually correct? Answer 'yes' or 'no':\n\n{statement}"

    try:
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )
        answer = response.choices[0].message["content"].strip().lower()
        print(prompt,":",answer)
        record["is_factually_correct"] = True if "yes" in answer else False
    except Exception as e:
        record["is_factually_correct"] = False
        record["error"] = str(e)

    return record
