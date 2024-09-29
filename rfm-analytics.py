import pandas as pd
import datetime as dt

# Display settings for DataFrame output
pd.set_option('display.max_columns', None)
# pd.set_option('display.max_rows', None)  # Uncomment if you want to display all rows
pd.set_option('display.float_format', lambda x: '%.3f' % x)

# Load the dataset and create a copy for analysis
df_ = pd.read_excel("datasets/online_retail_II.xlsx")
df = df_.copy()

# Check the shape and missing values of the dataset
df.shape
df.isnull().sum()

# Find the number of unique product descriptions
df["Description"].nunique()

# Remove rows with missing values
df.dropna(inplace=True)

# Display summary statistics of the dataset
df.describe().T

# Remove rows where the invoice starts with 'C' (indicating cancellations)
df = df[~df["Invoice"].str.contains("C", na=False)]

# Create a new column for the total price
df["Total Price"] = df["Quantity"] * df["Price"]

# Find the most recent date in the dataset
df["InvoiceDate"].max()

# Define a reference date for RFM analysis
today_date = dt.datetime(2010, 12, 11)

# Calculate Recency, Frequency, and Monetary metrics for each customer
rfm = df.groupby("Customer ID").agg({
    "InvoiceDate": lambda InvoiceDate: (today_date - InvoiceDate.max()).days,
    "Invoice": lambda Invoice: Invoice.nunique(),
    "Total Price": lambda TotalPrice: TotalPrice.sum()
})

rfm.head()

# Rename the columns for clarity
rfm.columns = ["recency", "frequency", "monetary value"]

# Reset the index to make 'Customer ID' a column
rfm = rfm.reset_index()

# Display summary statistics for the RFM table
rfm.describe().T

# Filter out customers with non-positive monetary value
rfm = rfm[rfm["monetary value"] > 0]

# Create Recency, Frequency, and Monetary scores based on quantiles
rfm['recency_score'] = pd.qcut(rfm['recency'], 5, labels=[5, 4, 3, 2, 1])
rfm['frequency_score'] = pd.qcut(rfm['frequency'].rank(method="first"), 5, labels=[1, 2, 3, 4, 5])
rfm['monetary_score'] = pd.qcut(rfm['monetary value'], 5, labels=[1, 2, 3, 4, 5])

# Combine Recency and Frequency scores to create the RFM score
rfm["RFM_SCORE"] = rfm["recency_score"].astype("str") + rfm["frequency_score"].astype("str")

# Display summary statistics for RFM_SCORE
rfm.describe().T

# Find customers with the lowest (11) and highest (55) RFM scores
rfm[rfm["RFM_SCORE"] == "11"]
rfm[rfm["RFM_SCORE"] == "55"]

# Define segments based on RFM scores using regex
seg_map = {
    r'[1-2][1-2]': 'hibernating',
    r'[1-2][3-4]': 'at_Risk',
    r'[1-2]5': 'cant_loose',
    r'3[1-2]': 'about_to_sleep',
    r'33': 'need_attention',
    r'[3-4][4-5]': 'loyal_customers',
    r'41': 'promising',
    r'51': 'new_customers',
    r'[4-5][2-3]': 'potential_loyalists',
    r'5[4-5]': 'champions'
}

# Assign segments to customers based on their RFM scores
rfm["segment"] = rfm["RFM_SCORE"].replace(seg_map, regex=True)

# Analyze each segment's recency, frequency, and monetary statistics
rfm.groupby("segment").agg({
    "recency": ["mean", "median", "min", "max"],
    "frequency": ["mean", "median", "min", "max"],
    "monetary value": ["mean", "median", "min", "max"]
})

# Create a new DataFrame for new customers
new_df = pd.DataFrame()
new_df["new_customer_id"] = rfm[rfm["segment"] == "new_customers"].index

# Convert the 'new_customer_id' column to integers
new_df["new_customer_id"] = new_df["new_customer_id"].astype(int)

# Export the new customers' data to a CSV file
new_df.to_csv("new_customers.csv", index=False)

# Functionalize whole process
def create_rfm_segments(df, csv=False):
    # Preparing the data
    df["Total Price"] = df["Quantity"] * df["Price"]
    df.dropna(inplace=True)
    df = df[~df["Invoice"].str.contains("C", na=False)]

    # Calculating the rfm metrics
    today_date = dt.datetime(2011, 12, 11)

    rfm = df.groupby("Customer ID").agg({
        "InvoiceDate": lambda InvoiceDate: (today_date - InvoiceDate.max()).days,
        "Invoice": lambda Invoice: Invoice.nunique(),
        "Total Price": lambda TotalPrice: TotalPrice.sum()
    })

    rfm.columns = ["recency", "frequency", "monetary value"]
    rfm = rfm.reset_index()
    rfm['recency_score'] = pd.qcut(rfm['recency'], 5, labels=[5, 4, 3, 2, 1])
    rfm['frequency_score'] = pd.qcut(rfm['frequency'].rank(method="first"), 5, labels=[1, 2, 3, 4, 5])
    rfm['monetary_score'] = pd.qcut(rfm['monetary value'], 5, labels=[1, 2, 3, 4, 5])
    rfm["RFM_SCORE"] = rfm["recency_score"].astype("str") + rfm["frequency_score"].astype("str")
    # Segmentation map to use
    seg_map = {
        r'[1-2][1-2]': 'hibernating',
        r'[1-2][3-4]': 'at_risk',
        r'[1-2]5': 'cant_loose',
        r'3[1-2]': 'about_to_sleep',
        r'33': 'need_attention',
        r'[3-4][4-5]': 'loyal_customers',
        r'41': 'promising',
        r'51': 'new_customers',
        r'[4-5][2-3]': 'potential_loyalists',
        r'5[4-5]': 'champions'
    }
    # Assigning segments to customers based on their RFM scores
    rfm["segment"] = rfm["RFM_SCORE"].replace(seg_map, regex=True)
    rfm = rfm[["recency", "frequency", "monetary value", "segment"]]
    rfm.index = rfm.index.astype(int)

    if csv:
        rfm.to_csv("rfm.csv")

    return rfm


create_rfm_segments(df, csv=True)