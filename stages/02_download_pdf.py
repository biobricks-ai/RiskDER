import os, tqdm, time, pyarrow, hashlib
import requests
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

def scrape(scrape_url, autoparse=False, binary=False, ultra_premium=False, timeout=20):
    scraperapi_key = os.getenv('SCRAPERAPI_KEY')
    params = {
        'api_key': scraperapi_key,
        'url': scrape_url,
        'autoparse': autoparse,
        'binary_target': binary,
        'ultra_premium': ultra_premium
    }
    return requests.get('http://api.scraperapi.com', params=params, timeout=timeout)


df = pd.read_parquet('download/search_results.parquet')
df['pdf_path'] = ''


# Loop through the URLs and download PDFs
os.makedirs('brick/riskder.pdf', exist_ok=True)
for index, row in tqdm.tqdm(df.iterrows(), total=len(df), desc="Downloading PDFs"):
    url = row['url']
    md5_hash = get_md5(url)
    pdf_path = f'brick/riskder.pdf/{md5_hash}.pdf'
    
    # Skip if the file already exists
    if os.path.exists(pdf_path):
        df.at[index, 'pdf_path'] = pdf_path
        continue
    
    try:
        # Make a request to download the PDF
        response = scrape(url, binary=True, timeout=30)
        
        # Check if the request was successful and the content is likely a PDF
        if response.status_code == 200 and response.headers.get('Content-Type', '').lower().startswith('application/pdf'):
            # Save the PDF
            with open(pdf_path, 'wb') as f:
                _ = f.write(response.content)
            df.at[index, 'pdf_path'] = pdf_path
        else:
            print(f"Failed to download PDF from {url}. Status code: {response.status_code}")
    
    except Exception as e:
        print(f"Error downloading PDF from {url}: {str(e)}")
    
    # Add a small delay to avoid overwhelming the server
    time.sleep(0.5)

# Save the DataFrame to brick/riskder.parquet
df.to_parquet('brick/riskder.parquet', index=False)
print("DataFrame successfully saved to brick/riskder.parquet")
