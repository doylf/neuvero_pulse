import requests
import json
import os
from pprint import pprint

# Environment variables from Secrets
AIRTABLE_API_KEY = os.environ['AIRTABLE_API_KEY']
AIRTABLE_BASE_ID = os.environ['AIRTABLE_BASE_ID']

BASE_URL = f"https://api.airtable.com/v0/meta/bases/{AIRTABLE_BASE_ID}/tables"
HEADERS = {
    "Authorization": f"Bearer {AIRTABLE_API_KEY}",
    "Content-Type": "application/json"
}

def get_all_tables_metadata():
  """
  Fetch metadata (schema) for all tables in the specified Airtable base.
  Returns the full JSON structure.
  """
  print("Fetching all tables metadata from Airtable...\n")

  try:
      response = requests.get(BASE_URL, headers=HEADERS)

      if response.status_code == 200:
          data = response.json()
          tables = data.get('tables', [])

          if not tables:
              print("No tables found in this base.")
              return None

          print(f"Found {len(tables)} table(s) in base {AIRTABLE_BASE_ID}\n")

          # Pretty print the full response
          print("Full metadata JSON structure:\n")
          pprint(data, indent=2, width=120)

          return data

      else:
          print(f"Error {response.status_code}: {response.text}")
          if response.status_code == 401:
              print("→ Check your API key / Personal Access Token")
          elif response.status_code == 404:
              print("→ Base ID might be incorrect")
          elif response.status_code == 403:
              print("→ Your token doesn't have access to metadata (needs 'schema' scope)")
          return None

  except Exception as e:
      print(f"Request failed: {str(e)}")
      return None


def save_to_file(data, filename="airtable_schema.json"):
  """Save the full metadata to a JSON file for easier inspection"""
  if data:
      with open(filename, 'w', encoding='utf-8') as f:
          json.dump(data, f, indent=2, ensure_ascii=False)
      print(f"\nSaved full schema to: {filename}")
  else:
      print("Nothing to save.")


if __name__ == "__main__":
  print("=" * 60)
  print("Airtable Base Tables Metadata Retriever")
  print("=" * 60)

  if not AIRTABLE_API_KEY or not AIRTABLE_BASE_ID:
      print("ERROR: Missing AIRTABLE_API_KEY or AIRTABLE_BASE_ID")
      print("Set them as environment variables or hardcode them in the script.")
      exit(1)

  metadata = get_all_tables_metadata()

  # Optional: save to file
  if metadata:
      save_to_file(metadata)

  print("\nDone.")