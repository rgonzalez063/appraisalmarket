import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Function to process the data and calculate adjustments
def calculate_adjustments(df):
    # Convert date columns to datetime format
    date_columns = ["List Date", "Close Date", "Withdrawn Date", "Expiration Date"]
    for col in date_columns:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')

    # Calculate Days on Market (DOM)
    df["Days on Market"] = (df["Close Date"] - df["List Date"]).dt.days
    df["Days Until Withdrawn"] = (df["Withdrawn Date"] - df["List Date"]).dt.days
    df["Days Until Expired"] = (df["Expiration Date"] - df["List Date"]).dt.days

    # Calculate price change percentage using SP/LP Ratio
    if "SP/LP Ratio" in df.columns:
        df["Price Change (%)"] = (df["SP/LP Ratio"] - 1) * 100
    else:
        df["Price Change (%)"] = 0  # Default if no SP/LP data

    # Calculate market condition adjustments
    if "Market Trend (%)" in df.columns:
        df["Adjustment (%)"] = df["Market Trend (%)"] - df["Price Change (%)"]
        df["Adjustment Type"] = df["Adjustment (%)"].apply(
            lambda x: "Upward" if x > 0 else "Downward" if x < 0 else "None"
        )
    else:
        df["Adjustment (%)"] = 0
        df["Adjustment Type"] = "None"

    # Calculate Final Adjusted Price
    df["Final Adjusted Price"] = df["Close Price"] * (1 + df["Adjustment (%)"] / 100)

    # Identify Withdrawn/Expired Listings for Market Trend Analysis
    df["Listing Outcome"] = df.apply(lambda row:
                                     "Expired" if pd.notna(row["Expiration Date"]) else
                                     "Withdrawn" if pd.notna(row["Withdrawn Date"]) else
                                     "Closed", axis=1)

    return df

# Streamlit UI
st.title("Real Estate Market Condition Adjustment Tool")
st.write("Upload a CSV file containing comparable sales data to analyze market trends and adjustments.")

# File uploader
uploaded_file = st.file_uploader("Upload CSV File", type=["csv"])
if uploaded_file:
    df = pd.read_csv(uploaded_file)

    # Process Data
    df_adjusted = calculate_adjustments(df)

    # Display Data
    st.subheader("Preview of Adjusted Data")
    st.dataframe(df_adjusted.head())

    # Download Button
    st.download_button(label="Download Adjusted CSV",
                       data=df_adjusted.to_csv(index=False),
                       file_name="adjusted_comparables.csv",
                       mime="text/csv")

    # Graphs
    st.subheader("Market Trends & Adjustments")

    # Days on Market Distribution
    fig, ax = plt.subplots()
    sns.histplot(df_adjusted["Days on Market"].dropna(), bins=20, kde=True, ax=ax)
    ax.set_title("Distribution of Days on Market")
    st.pyplot(fig)

    # Sale Price Adjustments
    fig, ax = plt.subplots()
    sns.boxplot(x="Listing Outcome", y="Final Adjusted Price", data=df_adjusted, ax=ax)
    ax.set_title("Final Adjusted Price by Listing Outcome")
    st.pyplot(fig)

    # Price Change vs Market Trend
    fig, ax = plt.subplots()
    sns.scatterplot(x=df_adjusted["Price Change (%)"], y=df_adjusted["Market Trend (%)"], hue=df_adjusted["Adjustment Type"], ax=ax)
    ax.set_title("Price Change vs Market Trend")
    st.pyplot(fig)
