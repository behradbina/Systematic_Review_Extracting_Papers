import pandas as pd
import matplotlib.pyplot as plt

# Load the CSV file
df = pd.read_csv('STZ.csv')  # Replace with your actual CSV filename

# Count repetitions of each username
username_counts = df['Username'].value_counts()

# Plotting the bar chart
plt.figure(figsize=(10, 6))
username_counts.plot(kind='bar', color='skyblue')
plt.title('Username Frequency')
plt.xlabel('Username')
plt.ylabel('Count')
plt.xticks(rotation=45, ha='right')
plt.tight_layout()
plt.show()
