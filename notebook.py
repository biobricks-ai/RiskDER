import pandas as pd

results = pd.read_parquet('brick/riskder.parquet')
extraction = pd.read_parquet('brick/extraction.parquet')