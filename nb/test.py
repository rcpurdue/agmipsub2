import pandas as pd

# Create a DataFrame with missing values
df = pd.DataFrame({'A': [1, 2, 4], 'B': [6, 7, 8], 'C': [9, 10, 11, 12]})

# Count the missing values in each column
missing_values = df.isnull().sum()
print(missing_values)
