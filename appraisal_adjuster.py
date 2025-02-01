import pandas as pd

def calculate_adjustments(input_file, output_file):
    """
    Reads a CSV file with comparable sales data, analyzes market trends (including expired/withdrawn listings),
    calculates market condition adjustments, and saves the adjusted data to a new CSV file.
    """

    # Load CSV data
    try:
        df = pd.read_csv(input_file)
    except Exception as e:
        print(f"Error loading file: {e}")
        return

    # Ensure required columns exist
    required_columns = [
        "Comparable ID", "List Date", "Close Date", "Close Price",
        "Market Trend (%)", "CDOM", "Status", "Withdrawn Date", "Expiration Date", "SP/LP Ratio"
    ]
    
    for col in required_columns:
        if col not in df.columns:
            print(f"Missing required column: {col}")
            return

    # Convert dates to datetime format
    df["List Date"] = pd.to_datetime(df["List Date"], errors='coerce')
    df["Close Date"] = pd.to_datetime(df["Close Date"], errors='coerce')
    df["Withdrawn Date"] = pd.to_datetime(df["Withdrawn Date"], errors='coerce')
    df["Expiration Date"] = pd.to_datetime(df["Expiration Date"], errors='coerce')

    # Calculate days from list date to close/withdrawn/expired
    df["Days on Market"] = (df["Close Date"] - df["List Date"]).dt.days
    df["Days Until Withdrawn"] = (df["Withdrawn Date"] - df["List Date"]).dt.days
    df["Days Until Expired"] = (df["Expiration Date"] - df["List Date"]).dt.days

    # Determine if the property sold above or below list price using SP/LP Ratio
    df["Price Change (%)"] = (df["SP/LP Ratio"] - 1) * 100

    # Calculate adjustment percentage
    df["Adjustment (%)"] = df["Market Trend (%)"] - df["Price Change (%)"]

    # Determine adjustment type
    df["Adjustment Type"] = df["Adjustment (%)"].apply(
        lambda x: "Upward" if x > 0 else "Downward" if x < 0 else "None"
    )

    # Calculate final adjusted price
    df["Final Adjusted Price"] = df["Close Price"] * (1 + df["Adjustment (%)"
