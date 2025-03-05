# TODO This is pretty far from complete, this committed version and it's output was shared at a client meeting.
import os, json, hashlib
import PyPDF2
import pathlib
from joblib import Memory, Parallel, delayed
from tqdm import tqdm
import pandas as pd
import hashlib
import dotenv
import openai

dotenv.load_dotenv()
client = openai.OpenAI()

# Set up cache directory
cachedir = pathlib.Path('cache/03_data_extractor')
cachedir.mkdir(parents=True, exist_ok=True)

(cachedir / 'memo_search_pdf_for_thyroid').mkdir(parents=True, exist_ok=True)
memory = Memory(cachedir / 'memo_search_pdf_for_thyroid', verbose=0)

# region FIND THYROID MENTIONS ==================================================================
@memory.cache(ignore=["pdf_path"])  # Ignore the actual file path, use the hashed version
def search_pdf_for_thyroid(pdf_path_hashed, pdf_path):
    mentions = 0
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            for page in reader.pages:
                try:
                    text = page.extract_text().lower()
                    mentions += text.count('thyroid')
                except Exception as e:
                    print(f"Error processing page in {pdf_path}: {e}")
                    continue  # Skip the problematic page
    except Exception as e:
        print(f"Error processing file {pdf_path}: {e}")
    return mentions

# Function to process a single PDF and update the DataFrame
def process_pdf(row):
    pdf_path = row['pdf_path']
    mentions = 0
    if pd.notna(pdf_path) and os.path.exists(pdf_path):
        pdf_path_hashed = hashlib.md5(pdf_path.encode()).hexdigest()  # Get the unique hash for this file
        mentions = search_pdf_for_thyroid(pdf_path_hashed, pdf_path)
    return mentions

# Load the DataFrame with PDF information
df = pd.read_parquet('brick/riskder.parquet')
df['thyroid_mentions'] = 0

# Parallelize the PDF search using joblib's Parallel
results = Parallel(n_jobs=30)(delayed(process_pdf)(row) for _, row in tqdm(df.iterrows(), total=len(df), desc="Searching PDFs"))

# Update the DataFrame with the results
df['thyroid_mentions'] = results
total_mentions = sum(results)

thyroid_df = df[df['thyroid_mentions'] > 0].sort_values('thyroid_mentions', ascending=False)
print(f"Total thyroid mentions across all PDFs: {total_mentions}")
# endregion

# region openai data extraction from pdfs ==================================================================

json_schema = {
    "name": "testing_results",
    "schema": {
        "type": "object",
        "properties": {
            "table": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "substance": {"type": "string"},
                        "guideline": {"type": "string"},
                        "test_description": {"type": "string"},
                        "metric": {"type": "string"},
                        "value": {"type": "number"},
                        "units": {"type": "string"}
                    },
                    "required": ["substance", "guideline", "test_description", "metric", "value", "units"],
                    "additionalProperties": False
                }
            }
        },
        "required": ["table"],
        "additionalProperties": False
    },
    "strict": True
}

(cachedir / 'memo_extract_testing_results').mkdir(parents=True, exist_ok=True)
memo_extract = Memory(cachedir / 'memo_extract_testing_results', verbose=0)
@memo_extract.cache
def extract_testing_results(pdf_path):

    reader = PyPDF2.PdfReader(pdf_path)
    pdf_content = "\n\n".join([page.extract_text() for page in reader.pages])

    prompt = f"{HUMAN_PROMPT}Review this PDF and extract a table with the following columns: substance (the substance being tested), guideline (an identifier for the test being performed, if available, e.g., an OECD guideline number), test_description (a description of the test being performed), metric (could be LOAEL, NOAEL, or some other measurement of the substance in the test), value (the numeric outcome), and units (the units used in the metric). Format your response as a JSON object that conforms to the following schema:\n\n{json.dumps(json_schema, indent=2)}\n\nHere's the PDF content:\n\n{pdf_content}\n\n{AI_PROMPT}"
    completion = client.chat.completions.create(
        model="gpt-4o-2024-08-06",
        messages=[
            {"role": "system", "content": "Extract the testing results information."},
            {"role": "user", "content": prompt},
        ],
    response_format={
        "type": "json_schema",
        "json_schema": json_schema
            }
        )
    return completion
    

aggdf = pd.DataFrame()
pdf_paths = thyroid_df['pdf_path'].tolist()
for path in tqdm(pdf_paths, total=len(pdf_paths), desc="Extracting testing results"):
    try:
        completion = extract_testing_results(path)
        df = pd.DataFrame(json.loads(completion.choices[0].message.content)['table'])
        aggdf = pd.concat([aggdf, df], ignore_index=True)
    except Exception as e:
        print(f"Skipping broken PDF: {path}. Error: {str(e)}")
        continue


aggdf.to_parquet('brick/extraction.parquet')
# endregion