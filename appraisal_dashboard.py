import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Property characteristic adjustment values (Modify based on market data)
ADJUSTMENTS = {
    "Lot Size (SF)": 1.50,  # $1.50 per sq ft
    "Living Area (SF)": 50, # $50 per sq ft
    "Bathroom Count": 5000, # $5000 per bathroom
    "Garage Spaces": 3000,  # $3000 per garage space
    "Pool": 10000,          # $10,000 for having a pool
    "Basement": 8000,       # $8,000 for having a basement
    "View": {"Good": 15000, "Fair": 5000, "Poor": 0}  # Adjust based on view quality
}

def process_data(df, subject_property):
    """
    Process the CSV data and apply both market condition & property characteristic adjustments.
    """

    # Standardize column names (strip spaces and ensure consistency)
    df.columns = df.columns.str.strip()

    # Print available columns for debugging
    st.write("Available columns in DataFrame:", df.columns.tolist())

    # Convert date columns
    date_columns = ["List Date", "Close Date", "Withdrawn Date", "Expiration Date"]
    for col in date_columns:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')

    # Ensure Market Trend (%) exists
    if "Market Trend (%)" not in df.columns:
        st.warning("⚠️ 'Market Trend (%)' column not found. Using default value of 7.0%.")
        df["Market Trend (%)"] = 7.0  # Default market trend

    # Calculate Days on Market
    df["Days on Market"] = (df["Close Date"] - df["List Date"]).dt.days

    # Calculate price change percentage using SP/LP Ratio
    if "SP/LP Ratio" in df.columns:
        df["Price Change (%)"] = (df["SP/LP Ratio"] - 1) * 100
    else:
        df["Price Change (%)"] = 0  # Default if no SP/LP data

    # Market Condition Adjustments
    df["Market Adjustment (%)"] = df["Market Trend (%)"] - df["Price Change (%)"]
    df["Market Adjustment Type"] = df["Market Adjustment (%)"].apply(
        lambda x: "Upward" if x > 0 else "Downward" if x < 0 else "None"
    )
    df["Price After Market Adjustment"] = df["Close Price"] * (1 + df["Market Adjustment (%)"] / 100)

    # Property Characteristic Adjustments
    for feature, value in ADJUSTMENTS.items():
        if feature in df.columns:
            if feature in ["View"]:  
                # View quality adjustments
                df["Adjustment for " + feature] = df[feature].apply(lambda x: ADJUSTMENTS["View"].get(x, 0)) - ADJUSTMENTS["View"].get(subject_property[feature], 0)
            else:
                df["Adjustment for " + feature] = (df[feature] - subject_property[feature]) * value

    # Sum all adjustments
    adjustment_columns = [col for col in df.columns if col.startswith("Adjustment for")]
    df["Total Adjustments"] = df[adjustment_columns].sum(axis=1)
    df["Final Adjusted Price"] = df["Price After Market Adjustment"] + df["Total Adjustments"]

    return df

# Streamlit UI
st.title("🏡 Comprehensive Real Estate Appraisal Tool")
st.write("Upload a CSV file with comparable sales, enter subject property details, and calculate adjustments.")

# File uploader
uploaded_file = st.file_uploader("Upload CSV File", type=["csv"])
if uploaded_file:
    df = pd.read_csv(uploaded_file)

    # Get Subject Property Details
    st.subheader("Enter Subject Property Characteristics")

    subject_property = {
        "Lot Size (SF)": st.number_input("Lot Size (SF)", min_value=0, value=7000),
        "Living Area (SF)": st.number_input("Living Area (SF)", min_value=500, value=2000),
        "Bathroom Count": st.number_input("Bathroom Count", min_value=1, value=2),
        "Garage Spaces": st.number_input("Garage Spaces", min_value=0, value=2),
        "Pool": st.radio("Pool", ["Yes", "No"]),
        "Basement": st.radio("Basement", ["Yes", "No"]),
        "View": st.selectbox("View Quality", ["Good", "Fair", "Poor"])
    }

    # Convert Pool/Basement Yes/No to numeric values
    subject_property["Pool"] = 1 if subject_property["Pool"] == "Yes" else 0
    subject_property["Basement"] = 1 if subject_property["Basement"] == "Yes" else 0

    # Process Data
    df_adjusted = process_data(df, subject_property)

    # Display Data
    st.subheader("📄 Adjusted Comparables Data")
    st.dataframe(df_adjusted.head())

    # Download Button
    st.download_button(label="📥 Download Adjusted CSV",
                       data=df_adjusted.to_csv(index=False),
                       file_name="combined_adjusted_comparables.csv",
                       mime="text/csv")

    # Graphs
    st.subheader("📊 Visualization of Adjustments")

    # Days on Market Distribution
    if "Days on Market" in df_adjusted.columns:
        fig, ax = plt.subplots()
        sns.histplot(df_adjusted["Days on Market"].dropna(), bins=20, kde=True, ax=ax)
        ax.set_title("Distribution of Days on Market")
        st.pyplot(fig)

    # Final Adjusted Prices
    if "Final Adjusted Price" in df_adjusted.columns:
        fig, ax = plt.subplots()
        sns.boxplot(x="Final Adjusted Price", data=df_adjusted, ax=ax)
        ax.set_title("Final Adjusted Price Distribution")
        st.pyplot(fig)

    # Market Adjustments vs Characteristic Adjustments
    if "Market Adjustment (%)" in df_adjusted.columns:
        fig, ax = plt.subplots()
        sns.scatterplot(x=df_adjusted["Market Adjustment (%)"], y=df_adjusted["Total Adjustments"], hue=df_adjusted["Market Adjustment Type"], ax=ax)
        ax.set_title("Market Adjustment vs. Property Adjustments")
        st.pyplot(fig)

