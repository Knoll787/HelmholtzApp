import csv
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

df = pd.read_csv('../data/test.csv', header=None)
df.columns = ['Time', 'Axis', 'Position', 'Set Point', 'Control Output', 'Error', 'Kp', 'Ki', 'Kd']
print(df)
x_time_0 = df.iat[0,0]
y_time_0 = df.iat[1,0]

df.iloc[::2, 0] -= x_time_0 
df.iloc[1::2, 0] -= y_time_0 
print(df)


# Example steady-state value
steady_state_value_x =  df.at[0,'Set Point']
steady_state_value_y =  df.at[1,'Set Point']
print(steady_state_value_x, steady_state_value_y)

plt.figure(figsize=(5, 5))


# Plotting
# Plot position vs. time
plt.scatter(df['Time'][::2], df['Position'][::2], label='x axis')
plt.scatter(df['Time'][1::2], df['Position'][1::2], label='y axis')

# Add horizontal line for steady-state
plt.axhline(y=steady_state_value_x, color='black', linestyle='--', label='Target')
#plt.axhline(y=steady_state_value_y, color='black', linestyle=':', label='Set Point: y')

# Labels and title
plt.xlabel('Time [s]')
plt.ylabel('Position [pixels]')
plt.title('System Response')
plt.legend()
plt.grid(True)

plt.show()
