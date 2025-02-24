import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
from fpdf import FPDF
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split

# Load and clean data
def load_data(file_path):
    data = pd.read_csv(file_path)
    return data

def clean_data(data):
    data.dropna(subset=['Close Price', 'SqFt', 'Bedrooms', 'Baths Total'], inplace=True)
    data['Close Date'] = pd.to_datetime(data['Close Date'])
    data['List Date'] = pd.to_datetime(data['List Date'])
    data['Year Built'] = pd.to_numeric(data['Year Built'], errors='coerce')
    data['PricePerSqFt'] = data['Close Price'] / data['SqFt']
    data['DOM'] = pd.to_numeric(data['DOM'], errors='coerce')
    data['SP/LP Ratio'] = data['Close Price'] / data['List Price']
    return data

# Analyze data
def analyze_data(data):
    analysis = {}
    analysis['avg_close_price'] = data['Close Price'].mean()
    analysis['median_close_price'] = data['Close Price'].median()
    analysis['avg_price_per_sqft'] = data['PricePerSqFt'].mean()
    analysis['median_dom'] = data['DOM'].median()
    data['Close Month'] = data['Close Date'].dt.to_period('M')
    monthly_trends = data.groupby('Close Month')['Close Price'].mean().reset_index()
    property_type_dist = data['Property Type'].value_counts().reset_index()
    property_type_dist.columns = ['Property Type', 'Count']
    return analysis, monthly_trends, property_type_dist

# Create charts
def create_charts(data, monthly_trends, property_type_dist):
    plt.figure(figsize=(10, 6))
    sns.histplot(data['Close Price'], bins=30, kde=True)
    plt.title('Distribution of Close Prices')
    plt.xlabel('Close Price')
    plt.ylabel('Frequency')
    st.pyplot(plt)
    
    plt.figure(figsize=(10, 6))
    sns.lineplot(x=monthly_trends['Close Month'].astype(str), y=monthly_trends['Close Price'])
    plt.title('Monthly Average Close Price')
    plt.xlabel('Month')
    plt.ylabel('Average Close Price')
    plt.xticks(rotation=45)
    st.pyplot(plt)
    
    plt.figure(figsize=(10, 6))
    sns.barplot(x='Property Type', y='Count', data=property_type_dist)
    plt.title('Property Type Distribution')
    plt.xlabel('Property Type')
    plt.ylabel('Count')
    plt.xticks(rotation=45)
    st.pyplot(plt)

# Generate commentary
def generate_commentary(analysis):
    commentary = f"""
    Market Analysis Report:
    - The average close price in the area is ${analysis['avg_close_price']:,.2f}.
    - The median close price is ${analysis['median_close_price']:,.2f}.
    - The average price per square foot is ${analysis['avg_price_per_sqft']:,.2f}.
    - The median days on market (DOM) is {analysis['median_dom']:.0f} days.
    """
    return commentary

# Export report
def export_report(analysis, data, monthly_trends, property_type_dist):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Market Analysis Report", ln=True, align="C")
    pdf.multi_cell(0, 10, txt=generate_commentary(analysis))
    pdf.cell(200, 10, txt="Filtered Data", ln=True, align="C")
    pdf.multi_cell(0, 10, txt=data.head().to_string())
    create_charts(data, monthly_trends, property_type_dist)
    plt.savefig('charts.png')
    pdf.image('charts.png', x=10, y=None, w=180)
    pdf.output("market_analysis_report.pdf")

# Regression model
def predict_price(data):
    features = ['SqFt', 'Bedrooms', 'Baths Total']
    X = data[features]
    y = data['Close Price']
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    model = LinearRegression()
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    return model, y_pred, y_test

# Streamlit app
st.title('Real Estate Market Analysis App')
uploaded_file = st.file_uploader("Upload MLS Data (CSV)", type="csv")

if uploaded_file is not None:
    data = load_data(uploaded_file)
    data = clean_data(data)
    
    # Filters
    st.sidebar.subheader('Filters')
    city_filter = st.sidebar.selectbox('City/Location', ['All'] + list(data['City/Location'].unique()))
    if city_filter != 'All':
        data = data[data['City/Location'] == city_filter]
    bedrooms_filter = st.sidebar.slider('Bedrooms', min_value=int(data['Bedrooms'].min()), max_value=int(data['Bedrooms'].max()))
    data = data[data['Bedrooms'] >= bedrooms_filter]
    baths_filter = st.sidebar.slider('Baths Total', min_value=int(data['Baths Total'].min()), max_value=int(data['Baths Total'].max()))
    data = data[data['Baths Total'] >= baths_filter]
    year_filter = st.sidebar.slider('Year Built', min_value=int(data['Year Built'].min()), max_value=int(data['Year Built'].max()))
    data = data[data['Year Built'] >= year_filter]
    
    # Analyze data
    analysis, monthly_trends, property_type_dist = analyze_data(data)
    
    # Display analysis
    st.subheader('Market Analysis')
    st.write(generate_commentary(analysis))
    
    # Display filtered data
    st.subheader('Filtered Data')
    st.write(data.head())
    
    # Display charts
    st.subheader('Charts')
    create_charts(data, monthly_trends, property_type_dist)
    
    # Comparisons
    st.sidebar.subheader('Comparisons')
    subdivision_comparison = st.sidebar.multiselect('Compare by Subdivision', data['Subdivision'].unique())
    if subdivision_comparison:
        comparison_data = data[data['Subdivision'].isin(subdivision_comparison)]
        st.subheader('Comparison by Subdivision')
        st.write(comparison_data.groupby('Subdivision')['Close Price'].mean().reset_index())
    
    school_comparison = st.sidebar.multiselect('Compare by School District', data['School District'].unique())
    if school_comparison:
        comparison_data = data[data['School District'].isin(school_comparison)]
        st.subheader('Comparison by School District')
        st.write(comparison_data.groupby('School District')['Close Price'].mean().reset_index())
    
    property_type_comparison = st.sidebar.multiselect('Compare by Property Type', data['Property Type'].unique())
    if property_type_comparison:
        comparison_data = data[data['Property Type'].isin(property_type_comparison)]
        st.subheader('Comparison by Property Type')
        st.write(comparison_data.groupby('Property Type')['Close Price'].mean().reset_index())
    
    # Export report
    if st.button('Export Report as PDF'):
        export_report(analysis, data, monthly_trends, property_type_dist)
        st.success('Report exported as PDF!')
    
    # Advanced analysis
    if st.checkbox('Show Advanced Analysis (Regression Model)'):
        model, y_pred, y_test = predict_price(data)
        st.subheader('Regression Model Results')
        st.write(f"Model R-squared: {model.score(X_test, y_test):.2f}")
        plt.figure(figsize=(10, 6))
        sns.scatterplot(x=y_test, y=y_pred)
        plt.xlabel('Actual Prices')
        plt.ylabel('Predicted Prices')
        plt.title('Actual vs Predicted Prices')
        st.pyplot(plt)
