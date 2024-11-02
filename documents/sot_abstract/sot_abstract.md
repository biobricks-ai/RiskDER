# Automating the Extraction of Experimental Outcomes from Regulatory Guidance Documents
A large number of guidance documents exist across regulatory agencies, including the EPA and FDA, which provide essential data on chemical properties, toxicity risks, and testing protocols. These documents are valuable for regulatory, research, and risk assessment applications but remain challenging to access and utilize efficiently. In this work, we aggregated and processed 1,812 "Data Evaluation Records" for various chemicals, developing an automated pipeline for extracting core information such as substance names, test guidelines, testing metrics (e.g., Lowest Observed Adverse Effect Level (LOAEL), No Observed Adverse Effect Level (NOAEL)), and specific metric values. Our system accurately identifies and organizes these data points, creating a structured dataset that is readily usable for regulatory and safety analysis. This approach provides an on-ramp for unstructured regulatory documents, enabling scalable chemical safety monitoring and supporting data-driven decision-making in regulatory science.

<!-- generate some kind of alphanumeric pasword -->
import random
import string

# Generate a random 12-character alphanumeric password
password = ''.join(random.choices(string.ascii_letters + string.digits, k=12))
print(f"Generated password: {password}")