import os, tqdm, time, pyarrow
import requests
import pandas as pd
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
bing_api_key = os.getenv('BINGAPI_KEY')

def bing_search(query, offset=0):
    headers = {'Ocp-Apim-Subscription-Key': bing_api_key}
    params = {
        'q': query,
        'mkt': 'en-US',  # Specify the market or region
        'count': 50,  # 50 is the max value
        'offset': offset,  # The offset for pagination
    }
    response = requests.get('https://api.bing.microsoft.com/v7.0/search', headers=headers, params=params)
    response.raise_for_status()  # Raise an exception for HTTP errors
    results = response.json()
    urls = []
    estimated_matches = results.get('webPages',{}).get('totalEstimatedMatches',{})
    for item in results.get('webPages', {}).get('value', []):
        license_info = next((rule['license'] for rule in item.get('contractualRules', []) if rule['_type'] == 'ContractualRules/LicenseAttribution'), None)
        urls.append({
            'query' : query,
            'name': item.get('name'),
            'url': item.get('url'),
            'snippet': item.get('snippet'),
            'license_name': license_info['name'] if license_info else '',
            'license_url': license_info['url'] if license_info else ''
        })
    return urls, estimated_matches

query = "epa data evaluation record filetype:pdf"
res, estimated_total = bing_search(query)

all_results = []
offset = 0
pbar = tqdm.tqdm(total=estimated_total, desc="Fetching results")
while True:
    results, _ = bing_search(query, offset)
    if not results:
        break
    all_results.extend(results)
    offset += len(results)
    pbar.update(len(results))
    
    if offset >= estimated_total:
        break
    time.sleep(0.1)

pbar.close()

# Create a DataFrame
df = pd.DataFrame(columns=['query', 'name', 'url', 'snippet', 'license_name', 'license_url'])
if os.path.exists('download/search_results.parquet'):
    df = pd.read_parquet('download/search_results.parquet')
    

if all_results:
    new_df = pd.DataFrame(all_results)
    df = pd.concat([df, new_df]).drop_duplicates(subset='url', keep='first')
df = df.reset_index(drop=True)

# Write DataFrame to parquet file
os.makedirs('download', exist_ok=True)
df.to_parquet('download/search_results.parquet', index=False)

# Read back and compare
df_read = pd.read_parquet('brick/search_results.parquet')
assert df.shape == df_read.shape, f"Shape mismatch: Original {df.shape}, Read {df_read.shape}"
print("Parquet file successfully written and verified.")

