import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


def compute_performance(time, pos, control, steady_state_value, tolerance=0.02):
    # Steady-state error
    Ess = abs(pos.iloc[-1] - steady_state_value)

    # Peak time & overshoot
    peak_idx = pos.idxmax()
    Tp = time.iloc[peak_idx]
    peak_value = pos.iloc[peak_idx]
    overshoot = ((peak_value - steady_state_value) / steady_state_value * 100
                 if steady_state_value != 0 else np.nan)

    # Settling time
    settling_mask = (abs(pos - steady_state_value) <= tolerance * abs(steady_state_value))
    Ts = time[settling_mask.idxmax()] if settling_mask.any() else np.nan

    # Actuator effort
    actuator_effort = np.mean(abs(control))

    return {
        "Steady-State Error (Ess)": Ess,
        "Peak Time (Tp)": Tp,
        "Overshoot (%)": overshoot,
        "Settling Time (Ts)": Ts,
        "Actuator Effort": actuator_effort
    }


def plot_response(time, pos, control, steady_state_value, metrics, axis="x"):
    fig, ax = plt.subplots(figsize=(12, 5))

    # --- Plot curves ---
    ax.plot(time, pos, label=f'{axis}-axis Position')
    ax.plot(time, control, linestyle='--', label=f'Actuator Effort ({axis}-axis)')
    ax.axhline(y=steady_state_value, color='black', linestyle='--', label='Target')

    # Labels & title
    ax.set_xlabel('Time [s]')
    ax.set_ylabel('Position [pixels]')
    ax.set_title(f'System Response ({axis.upper()} axis)')
    ax.grid(True)

    # --- Legend (anchored to right) ---
    legend = ax.legend(
        bbox_to_anchor=(1.05, 1),   # place outside
        loc="upper left",
        borderaxespad=0.,
        frameon=True
    )

    # --- Performance metrics text box ---
    textstr = '\n'.join((
        f'Settling Time (Ts): {metrics["Settling Time (Ts)"]:.2f} s',
        f'Steady-State Error (Ess): {metrics["Steady-State Error (Ess)"]:.2f} px',
        f'Peak Time (Tp): {metrics["Peak Time (Tp)"]:.2f} s',
        f'Overshoot: {metrics["Overshoot (%)"]:.2f} %',
        f'Actuator Effort: {metrics["Actuator Effort"]:.2f}'
    ))

    # Place box just below the legend, same x-position
    ax.text(
        1.05, 0.5, textstr,
        transform=ax.transAxes,
        fontsize=10,
        va='center', ha='left',
        bbox=dict(facecolor='white', edgecolor='black', alpha=0.7)
    )

    # --- Adjust layout so nothing overlaps ---
    plt.tight_layout(rect=[0, 0, 0.75, 1])

    plt.show()



def load_axis_data(file_path, axis="x"):
    df = pd.read_csv(file_path, header=None)
    df.columns = ['Time', 'Axis', 'Position', 'Set Point',
                  'Control Output', 'Error', 'Kp', 'Ki', 'Kd']

    # Time offset correction
    x_time_0 = df.iat[0, 0]
    y_time_0 = df.iat[1, 0]
    df.iloc[::2, 0] -= x_time_0
    df.iloc[1::2, 0] -= y_time_0

    if axis.lower() == "x":
        time = df['Time'][::2].reset_index(drop=True)
        pos = df['Position'][::2].reset_index(drop=True)
        control = df['Control Output'][::2].reset_index(drop=True)
        steady_state_value = df['Set Point'][::2].iloc[-1]
    elif axis.lower() == "y":
        time = df['Time'][1::2].reset_index(drop=True)
        pos = df['Position'][1::2].reset_index(drop=True)
        control = df['Control Output'][1::2].reset_index(drop=True)
        steady_state_value = df['Set Point'][1::2].iloc[-1]
    else:
        raise ValueError("Axis must be 'x' or 'y'")

    return time, pos, control, steady_state_value

"""
# Load X-axis data
time_x, pos_x, control_x, sp_x = load_axis_data("../data/test.csv", axis="x")
time_y, pos_y, control_y, sp_y = load_axis_data("../data/test.csv", axis="y")

# Compute metrics
metrics_x = compute_performance(time_x, pos_x, control_x, sp_x)
metrics_y = compute_performance(time_y, pos_y, control_y, sp_y)

# Plot response
plot_response(time_x, pos_x, control_x, sp_x, metrics_x, axis="x")
plot_response(time_y, pos_y, control_y, sp_y, metrics_y, axis="y")
"""

time_x6, pos_x6, control_x6, sp_x6 = load_axis_data("../data/openloop_x6_max.csv", axis="x")
time_x5, pos_x5, control_x5, sp_x5 = load_axis_data("../data/openloop_x5_max.csv", axis="x")
time_y4, pos_y4, control_y4, sp_y4 = load_axis_data("../data/openloop_y4_max.csv", axis="y")
time_y3, pos_y3, control_y3, sp_y3 = load_axis_data("../data/openloop_y3_max.csv", axis="y")

"""
# Create a tiled layout with 2 rows, 1 column (stacked plots)
fig, axs = plt.subplots(2, 1, figsize=(10, 6), sharex=True)

# Plot X data
axs[0].plot(time_x, pos_x, color='tab:blue')
axs[0].set_title("X Axis")
axs[0].set_xlabel("Time [s]")
axs[0].set_ylabel("Position x [pixels]")
axs[0].grid(True)

# Plot Y data
axs[1].plot(time_y, pos_y, color='tab:orange')
axs[1].set_title("Y Axis")
axs[1].set_xlabel("Time [s]")
axs[1].set_ylabel("Position y [pixels]")
axs[1].grid(True)

# Adjust layout so titles/labels don’t overlap
plt.tight_layout()
plt.show()
"""
fig, axs = plt.subplots(2, 2, figsize=(10, 6), sharex=True)
fig.suptitle("Open Loop Step Response - Max Current")
# Top-left: X data (line plot)
axs[0, 0].plot(time_x6, pos_x6, color='tab:blue')
axs[0, 0].set_title("X Axis - Coil 6")
axs[0, 0].set_ylabel("Position (x)")
axs[0, 0].grid(True)

# Top-right: X data (scatter plot for variety)
axs[0, 1].plot(time_x5, pos_x5, color='tab:blue')
axs[0, 1].set_title("X Axis - Coil 5")
axs[0, 1].grid(True)

# Bottom-right: Y data (scatter plot for variety)
axs[1, 1].plot(time_y3, pos_y3, color='tab:orange')
axs[1, 1].set_title("Y Axis - Coil 3")
axs[1, 1].set_xlabel("Time (s)")
axs[1, 1].grid(True)

# Bottom-left: Y data (line plot)
axs[1, 0].plot(time_y4, pos_y4, color='tab:orange')
axs[1, 0].set_title("Y Axis - Coil 4")
axs[1, 0].set_xlabel("Time (s)")
axs[1, 0].set_ylabel("Position (y)")
axs[1, 0].grid(True)


# Adjust layout
plt.tight_layout()
plt.show()