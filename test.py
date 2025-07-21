import tkinter as tk
from tkinter import ttk
from gpiozero import PWMOutputDevice, OutputDevice
from time import sleep

# Z-direction
# Define GPIO pins for Motor Driver 3 (Coils 1 and 2)
PWM_PIN1, DIR_PIN1 = 12, 16  # Coil 1
PWM_PIN2, DIR_PIN2 = 20, 21  # Coil 2

# Y-direction
# Define GPIO pins for Motor Driver 2 (Coils 3 and 4)
PWM_PIN3, DIR_PIN3 =  5,  6  # Coil 3
PWM_PIN4, DIR_PIN4 = 13, 19  # Coil 4

# X-direction
# Define GPIO pins for Motor Driver 1 (Coils 5 and 6)
PWM_PIN5, DIR_PIN5 = 17, 22  # Coil 5
PWM_PIN6, DIR_PIN6 = 27, 23  # Coil 6

# Setup the PWM and Direction pins for each coil
coil1_pwm = PWMOutputDevice(PWM_PIN1, frequency=1000)
coil1_dir = OutputDevice(DIR_PIN1)
coil2_pwm = PWMOutputDevice(PWM_PIN2, frequency=1000)
coil2_dir = OutputDevice(DIR_PIN2)


coil3_pwm = PWMOutputDevice(PWM_PIN3, frequency=1000)
coil3_dir = OutputDevice(DIR_PIN3)
coil4_pwm = PWMOutputDevice(PWM_PIN4, frequency=1000)
coil4_dir = OutputDevice(DIR_PIN4)


coil5_pwm = PWMOutputDevice(PWM_PIN5, frequency=1000)
coil5_dir = OutputDevice(DIR_PIN5)
coil6_pwm = PWMOutputDevice(PWM_PIN6, frequency=1000)
coil6_dir = OutputDevice(DIR_PIN6)

def update_state():
	valx = slider1.get()
	valy = slider2.get()
	valz = slider3.get()

	if valx >= 0:
		direction_x = True 
	else:
		direction_x = False 

	if valy >= 0:
		direction_y = True 
	else:
		direction_y = False

	if valz >= 0:
		direction_z = True 
	else:
		direction_z = False 


	# Z-Coils
	set_coil(coil1_pwm, coil1_dir, abs(valz), direction_z)
	set_coil(coil2_pwm, coil2_dir, abs(valz), direction_z)

	# Y-Coils
	set_coil(coil3_pwm, coil3_dir, abs(valy), direction_y)
	set_coil(coil4_pwm, coil4_dir, abs(valy), direction_y)

	# X-Coils
	set_coil(coil5_pwm, coil5_dir, abs(valx), direction_x)
	set_coil(coil6_pwm, coil6_dir, abs(valx), direction_x)


	print(coil1_dir.is_active)
	print(coil2_dir.is_active)
	print(coil3_dir.is_active)
	print(coil4_dir.is_active)
	print(coil5_dir.is_active)
	print(coil6_dir.is_active)
	print("\n")
	print(f"Slider Values: {valx:.2f}, {valy:.2f}, {valz:.2f}")

def reset_state():
    set_coil(coil1_pwm, coil1_dir, 0.0, True)
    set_coil(coil2_pwm, coil2_dir, 0.0, True)

    # Y-Coils
    set_coil(coil3_pwm, coil3_dir, 0.0, True)
    set_coil(coil4_pwm, coil4_dir, 0.0, True)

    # X-Coils
    set_coil(coil5_pwm, coil5_dir, 0.0, True)
    set_coil(coil6_pwm, coil6_dir, 0.0, True)



    print(f"Slider Values: 0.00, 0.00, 0.00")

def update_label(slider, label):
    label.config(text=f"{slider.get():.2f}")


# Function to set coil power and direction
def set_coil(coil_pwm, coil_dir, power, direction):
	if direction == True:
		coil_dir.on()
	else:
		coil_dir.off()
	print(coil_dir)

	coil_pwm.value = power  # Set PWM duty cycle (0.0 to 1.0)


# Create main window
root = tk.Tk()
root.title("Slider Control")
root.geometry("300x300")

# Create sliders and labels
x_label = tk.Label(root, text="X-Axis")
x_label.pack(pady=(10, 0))
slider1 = ttk.Scale(root, from_=-1.0, to=1.0, orient="horizontal", command=lambda val: update_label(slider1, label1), length=250)
slider1.pack()
label1 = tk.Label(root, text="0.00")
label1.pack()

y_label = tk.Label(root, text="Y-Axis")
y_label.pack(pady=(10, 0))
slider2 = ttk.Scale(root, from_=-1.0, to=1.0, orient="horizontal", command=lambda val: update_label(slider2, label2), length=250)
slider2.pack()
label2 = tk.Label(root, text="0.00")
label2.pack()

z_label = tk.Label(root, text="Z-Axis")
z_label.pack(pady=(10, 0))
slider3 = ttk.Scale(root, from_=-1.0, to=1.0, orient="horizontal", command=lambda val: update_label(slider3, label3), length=250)
slider3.pack()
label3 = tk.Label(root, text="0.00")
label3.pack()

# Create Update State button
update_button = ttk.Button(root, text="Update State", command=update_state)
update_button.pack(pady=10)

reset_button = ttk.Button(root, text="Reset State", command=reset_state)
reset_button.pack(pady=10)

# Run the application
root.mainloop()


