import pandas as pd

# Load training data
df = pd.read_excel('training_data.xlsx')
print(f"Training data shape: {df.shape}")
print(f"Columns: {df.columns.tolist()}")
print("\nSample training examples:")

for i in range(min(5, len(df))):
    query = df.iloc[i]['Query']
    url = df.iloc[i]['Assessment_url']
    print(f"\nQuery {i+1}: {query}")
    print(f"Expected URL {i+1}: {url}")

print(f"\nTotal training examples: {len(df)}")

# Check for sales-related queries
sales_queries = df[df['Query'].str.contains('sales', case=False, na=False)]
print(f"\nSales-related queries: {len(sales_queries)}")

if len(sales_queries) > 0:
    print("\nSales query examples:")
    for i in range(min(3, len(sales_queries))):
        query = sales_queries.iloc[i]['Query']
        url = sales_queries.iloc[i]['Assessment_url']
        print(f"Sales Query: {query}")
        print(f"Expected URL: {url}")
        print()