import sys
import os

# Add src to path
sys.path.append(os.path.join(os.getcwd(), "K-12-Sales-Toolkit", "src"))
try:
    from data_fetchers import fetch_caaspp_data, scrape_eddata_profile, fetch_esser_grants
except ImportError:
    # Try importing from local directory if running from src
    sys.path.append(os.path.join(os.getcwd(), "src"))
    from data_fetchers import fetch_caaspp_data, scrape_eddata_profile, fetch_esser_grants

def main():
    print("Starting data collection...")

    # 1. Fetch CAASPP Data
    try:
        fetch_caaspp_data()
    except Exception as e:
        print(f"Error fetching CAASPP data: {e}")

    # 2. Fetch ESSER Grants
    try:
        fetch_esser_grants()
    except Exception as e:
        print(f"Error fetching ESSER data: {e}")

    # 3. Scrape EdData (Mocked for now)
    # In a real scenario we would loop through districts.
    # We will generate a mock la_metro_districts.csv
    print("Generating LA Metro Districts data...")
    import pandas as pd
    la_metro_districts = [
        "Los Angeles Unified", "Long Beach Unified", "Pasadena Unified",
        "Glendale Unified", "Burbank Unified", "Compton Unified",
        "Inglewood Unified", "Torrance Unified", "Santa Monica-Malibu Unified",
        "Culver City Unified", "Beverly Hills Unified", "Downey Unified",
        "Montebello Unified", "Paramount Unified", "Lynwood Unified"
    ]

    data = []
    for d in la_metro_districts:
        profile = scrape_eddata_profile(d.replace(" ", "-").lower())
        data.append(profile)

    df = pd.DataFrame(data)
    output_path = os.path.join("K-12-Sales-Toolkit", "data", "processed", "la_metro_districts.csv")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"Saved LA Metro districts data to {output_path}")

    print("Data collection complete.")

if __name__ == "__main__":
    main()
