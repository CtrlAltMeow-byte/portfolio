# Project for real-time Data Capture
# Summer, 2026

import requests  # Milestone 1
import pandas as pd  # Milestone 2

URL = "https://data.kcmo.org/resource/d4px-6rwg.json"



def main():
    print("Building test project")

    
    #Milestone 1: Fetch 311 Call Center Issues data from the API and print the first 2 records.
    data = fetch_311_requests(limit=2)
    if not data:
        print("❌ No data returned from API. Aborting pipeline steps.") 
        return
    print(f"Successfully fetched {len(data)} records:")
    print(data)

    
      
    
        
    # Milestone 2, Step 1: Load JSON into a DataFrame and inspect its shape/dtypes
    df = pd.DataFrame(fetch_311_requests())
    if df.empty:
        print("❌ No data returned from API. Aborting pipeline steps.")
        return  
    print()
    print("---------- Columns in the DataFrame ----------")
    print(df.columns)
    print("----------------------------------------------")
    print()
    print("---------- Shape of the DataFrame ----------")
    print(df.shape)
    print("----------------------------------------------")
    print()
    print("---------- Types of the DataFrame ----------")
    print(df.dtypes)
    print("----------------------------------------------")
    print()
    print("----------isnull of the DataFrame ----------")
    print(df.isnull().sum())
    print("----------------------------------------------")
    print()

   # Milestone 2, Step 2: Clean deliberately - narrate why for each line, not just how
    # ---------- Clean deliberately ----------

    # Drop nested (dict) columns before deduping — lat_long is a dict, and
    # pandas can't compare/hash dicts, so drop_duplicates() would crash on it
    nested_cols = [col for col in df.columns if df[col].apply(lambda x: isinstance(x, dict)).any()]
    if nested_cols:
        print(f"Dropping nested columns before dedup: {nested_cols}")
        df = df.drop(columns=nested_cols)

    df = df.drop_duplicates()
    print(f"Rows after dropping duplicates: {df.shape[0]}")

    # Only drop rows missing the two fields this analysis actually depends on —
    # a null in some unrelated column (e.g. resolved_date) shouldn't cost us a row
    df = df.dropna(subset=["issue_type", "open_date_time"])
    print(f"Rows after dropping nulls in issue_type/open_date_time: {df.shape[0]}")

    # Convert to real datetime objects; unparseable strings become NaT instead of raising
    df["open_date_time"] = pd.to_datetime(df["open_date_time"], errors="coerce")

    # to_datetime can silently turn a malformed (but non-null) string into NaT —
    # this second dropna catches those, since the first dropna ran before conversion
    df = df.dropna(subset=["open_date_time"])
    print(f"Rows after dropping unparseable dates: {df.shape[0]}")

    # Extract a street name from the full address (incident_address has no dedicated
    # street-only column) by stripping a leading house number, e.g. "123 Main St" -> "Main St"
    df["street_name"] = df["incident_address"].str.replace(r"^\d+\s+", "", regex=True)

    # ---------- Answer real questions with groupby ----------

    peak_hours = df.groupby(df["open_date_time"].dt.hour)["issue_type"].size()
    busiest_streets = df.groupby("street_name")["issue_type"].size().sort_values(ascending=False)

    print("---------- Peak Request Hours ----------")
    print(peak_hours)
    print()

    print("---------- Busiest Streets (top 10) ----------")
    print(busiest_streets.head(10))
    print()
    
    top_issue_per_street = (
    df.groupby("street_name")["issue_type"]
    .agg(lambda x: x.value_counts().idxmax())
)

    busiest_streets_with_top_issue = pd.DataFrame({
    "total_issues": busiest_streets,
    "most_common_issue": top_issue_per_street
}).sort_values("total_issues", ascending=False)
    print("---------- Busiest Streets with Top Issues (top 10) ----------")
    print(busiest_streets_with_top_issue.head(10))
    print()

    print("---------- Final DataFrame Overview ----------")
    print(df.head())
    print(f"Final shape of the DataFrame: {df.shape}")

    # Milestone 2, Step 3: Use groupby 
  

def fetch_311_requests(limit=1000):
    try:
        response = requests.get(URL, params={"$limit": limit}, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.Timeout:
        print("Request timed out — the API may be slow or down.")
    except requests.exceptions.HTTPError as e:
        print(f"HTTP error: {e}")
    except requests.exceptions.RequestException as e:
        print(f"Something went wrong: {e}")
    return []



main()