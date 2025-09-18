import csv
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

# Load data
df = pd.read_csv('../data/test.csv', header=None)
df.columns = ['Time', 'Axis', 'Position', 'Set Point', 'Control Output', 'Error', 'Kp', 'Ki', 'Kd']

# Time offset correction
x_time_0 = df.iat[0,0]
y_time_0 = df.iat[1,0]
df.iloc[::2, 0] -= x_time_0 
df.iloc[1::2, 0] -= y_time_0 

# Steady-state values (assume final setpoint)
steady_state_value_x = df['Set Point'][::2].iloc[-1]
steady_state_value_y = df['Set Point'][1::2].iloc[-1]

# Extract axes
time_x = df['Time'][::2]
pos_x = df['Position'][::2]
control_x = df['Control Output'][::2]

time_y = df['Time'][1::2]
pos_y = df['Position'][1::2]
control_y = df['Control Output'][1::2]

# --- Compute system characteristics for x axis ---

# Steady-state error
Ess_x = abs(pos_x.iloc[-1] - steady_state_value_x)

# Peak time and overshoot
peak_idx = pos_x.idxmax()
Tp_x = df.at[peak_idx, 'Time']
peak_value_x = df.at[peak_idx, 'Position']

# Settling time (within 2% of steady-state)
settling_mask = (abs(pos_x - steady_state_value_x) <= 0.02 * steady_state_value_x)
if any(settling_mask):
    Ts_x = df['Time'][settling_mask.idxmax()]
else:
    Ts_x = np.nan

# Approximate actuator effort (average absolute control output)
actuator_effort_x = np.mean(abs(control_x))

# --- Plotting ---
plt.figure(figsize=(7, 5))

# Position vs. time
plt.plot(time_x, pos_x, label='x axis')
plt.plot(time_x, control_x, linestyle='--', label='Actuator Effort (x axis)')
#plt.plot(time_y, pos_y, label='y axis')

# Target line
plt.axhline(y=steady_state_value_x, color='black', linestyle='--', label='Target')

# Labels
plt.xlabel('Time [s]')
plt.ylabel('Position [pixels]')
plt.title('System Response')
plt.grid(True)
plt.legend()

# Add a text box for system characteristics
textstr = '\n'.join((
    f'Settling Time (Ts): {Ts_x:.2f} s',
    f'Steady-State Error (Ess): {Ess_x:.2f} px',
    f'Peak Time (Tp): {Tp_x:.2f} s',
    f'Actuator Effort: {actuator_effort_x:.2f}'))

plt.gcf().text(0.65, 0.6, textstr, fontsize=10,
               bbox=dict(facecolor='white', edgecolor='black', alpha=0.7))

plt.show()
