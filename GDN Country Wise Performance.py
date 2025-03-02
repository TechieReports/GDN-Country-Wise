import streamlit as st
import pandas as pd
import re

# 📌 Hardcoded Country Code Mapping
COUNTRY_CODE_MAPPING = {
    "United States": "US", "United Kingdom": "GB", "South Korea": "KR", "Taiwan": "TW",
    "Russia": "RU", "Turkey": "TR", "Iran": "IR", "Vietnam": "VN", "Syria": "SY",
    "Czechia": "CZ", "Caribbean Netherlands": "BQ", "French Polynesia": "PF",
    "Saint Kitts and Nevis": "KN", "Saint Lucia": "LC", "Saint Vincent and the Grenadines": "VC",
    "U.S. Virgin Islands": "VI", "Sao Tome and Principe": "ST", "Puerto Rico": "PR",
    "Guam": "GU", "Micronesia": "FM", "Eritrea": "ER", "Fiji": "FJ", "Comoros": "KM",
    "Mauritius": "MU", "Seychelles": "SC", "Sudan": "SD", "Vanuatu": "VU",
    "Argentina": "AR", "Australia": "AU", "Austria": "AT", "Belgium": "BE",
    "Brazil": "BR", "Bulgaria": "BG", "Canada": "CA", "China": "CN",
    "Colombia": "CO", "Denmark": "DK", "Ecuador": "EC", "Egypt": "EG",
    "Estonia": "EE", "Finland": "FI", "France": "FR", "Germany": "DE",
    "Greece": "GR", "Hong Kong": "HK", "Hungary": "HU", "Iceland": "IS",
    "India": "IN", "Indonesia": "ID", "Ireland": "IE", "Israel": "IL",
    "Italy": "IT", "Japan": "JP", "Jordan": "JO", "Latvia": "LV",
    "Lithuania": "LT", "Malaysia": "MY", "Mexico": "MX", "Netherlands": "NL",
    "New Zealand": "NZ", "Norway": "NO", "Philippines": "PH", "Poland": "PL",
    "Portugal": "PT", "Romania": "RO", "Saudi Arabia": "SA", "Singapore": "SG",
    "Slovakia": "SK", "Slovenia": "SI", "South Africa": "ZA", "Spain": "ES",
    "Sweden": "SE", "Switzerland": "CH", "Thailand": "TH", "United Arab Emirates": "AE",
    "Uruguay": "UY", "Vietnam": "VN"
}

# 🎯 Streamlit App Title
st.title("📊 GDN Campaign Optimization - Exclude Underperforming Countries")

# 🎯 Sidebar: File Upload
st.sidebar.header("Upload Your Data")
spend_file = st.sidebar.file_uploader("Upload Spend Data (Excel)", type=["xlsx"])
revenue_file = st.sidebar.file_uploader("Upload Revenue Data (CSV)", type=["csv"])

# 🎯 Process when files are uploaded
if spend_file and revenue_file:
    # Load Spend Data
    xls = pd.ExcelFile(spend_file)
    spend_df = pd.read_excel(xls, sheet_name='Sheet0', skiprows=1)

    # Load Revenue Data
    revenue_df = pd.read_csv(revenue_file)

    # Rename Spend Data Columns
    spend_df.columns = [
        "Country Name", "Campaign", "Bid adj.", "Added/Excluded", "Clicks",
        "Impressions", "CTR", "Currency code", "Avg. CPC", "Cost", 
        "Conv. rate", "Conversions", "Cost per conv."
    ]
    spend_df = spend_df.iloc[1:].reset_index(drop=True)

    # Extract Campaign ID from Spend Data and Convert to Integer
    spend_df["Campid"] = spend_df["Campaign"].apply(
        lambda x: int(re.search(r"\((\d+)\)", str(x)).group(1)) if re.search(r"\((\d+)\)", str(x)) else None
    )

    # Convert Numeric Columns
    spend_df["Cost"] = pd.to_numeric(spend_df["Cost"], errors="coerce")
    spend_df["Conversions"] = pd.to_numeric(spend_df["Conversions"], errors="coerce")
    spend_df["Cost per conv."] = pd.to_numeric(spend_df["Cost per conv."], errors="coerce")

    # 🟢 Map Country Names to Country Codes
    spend_df["Country Code"] = spend_df["Country Name"].map(COUNTRY_CODE_MAPPING)

    # Aggregate Revenue Data by Campaign & Country
    revenue_aggregated = revenue_df.groupby(["Campid", "Country_Code"]).agg({"Revenue": "sum"}).reset_index()

    # Merge Spend and Revenue Data
    merged_data = spend_df.merge(
        revenue_aggregated,
        left_on=["Campid", "Country Code"],
        right_on=["Campid", "Country_Code"],
        how="left"
    )

    # Drop Redundant Columns
    merged_data.drop(columns=["Country_Code"], inplace=True)

    # Rename for Clarity
    merged_data.rename(columns={"Revenue": "Total Revenue"}, inplace=True)

    # Convert Revenue to Numeric
    merged_data["Total Revenue"] = pd.to_numeric(merged_data["Total Revenue"], errors="coerce")

    # 🟢 Filter Performing & Excluded Countries
    performing_countries = merged_data[merged_data["Total Revenue"] >= merged_data["Cost"]]
    excluded_countries = merged_data[merged_data["Total Revenue"] < merged_data["Cost"]]

    # Sort by Campaign ID and Convert to Integer for Clean Display
    performing_countries = performing_countries.sort_values(by="Campid")
    excluded_countries = excluded_countries.sort_values(by="Campid")
    performing_countries["Campid"] = performing_countries["Campid"].astype(int)
    excluded_countries["Campid"] = excluded_countries["Campid"].astype(int)

    # Select Only Required Columns
    selected_columns = ["Country Name", "Campaign", "Cost", "Conversions", "Cost per conv.", "Campid", "Country Code", "Total Revenue"]
    performing_countries = performing_countries[selected_columns]
    excluded_countries = excluded_countries[selected_columns]

    # 🎯 Sidebar: Campaign Filter (Dropdown with "Select All" & "Deselect All")
    unique_campaigns = sorted(performing_countries["Campid"].dropna().unique())

    # Default selection: all campaigns
    if "selected_campaigns" not in st.session_state:
        st.session_state.selected_campaigns = unique_campaigns

    col1, col2 = st.sidebar.columns([0.5, 0.5])
    if col1.button("Select All"):
        st.session_state.selected_campaigns = unique_campaigns
    if col2.button("Deselect All"):
        st.session_state.selected_campaigns = []

    selected_campaigns = st.sidebar.multiselect("Select Campaign(s)", unique_campaigns, default=st.session_state.selected_campaigns)

    # Apply Campaign Filter
    performing_countries = performing_countries[performing_countries["Campid"].isin(selected_campaigns)]
    excluded_countries = excluded_countries[excluded_countries["Campid"].isin(selected_campaigns)]

    # 🟢 Display Filtered Results
    st.subheader("✅ Performing Countries (Keep These)")
    st.dataframe(performing_countries)

    st.subheader("🚨 Excluded Countries (Remove These)")
    st.dataframe(excluded_countries)

    # 🎯 Sidebar: Download Processed Data
    st.sidebar.subheader("Download Data")

    # Download Excluded Countries
    excluded_csv = excluded_countries.to_csv(index=False).encode('utf-8')
    st.sidebar.download_button("Download Excluded Countries (CSV)", excluded_csv, "excluded_countries.csv", "text/csv")

    # Download Performing Countries
    performing_csv = performing_countries.to_csv(index=False).encode('utf-8')
    st.sidebar.download_button("Download Performing Countries (CSV)", performing_csv, "performing_countries.csv", "text/csv")

else:
    st.info("📂 Please upload both Spend and Revenue data to proceed.")
