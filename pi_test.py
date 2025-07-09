from gpiozero import PWMOutputDevice, OutputDevice, Device


x_pwm1 = PWMOutputDevice(17, frequency=1000)
x_dir1 = OutputDevice(22)
x_pwm2 = PWMOutputDevice(27, frequency=1000)
x_dir2 = OutputDevice(23)

y_pwm1 = PWMOutputDevice( 5, frequency=1000)
y_dir1 = OutputDevice( 6)
y_pwm2 = PWMOutputDevice(13, frequency=1000)
y_dir2 = OutputDevice(19)

z_pwm1 = PWMOutputDevice(12, frequency=1000)
z_dir1 = OutputDevice(16)
z_pwm2 = PWMOutputDevice(20, frequency=1000)
z_dir2 = OutputDevice(21)



x_dir1.on()
input("Next...")
x_dir1.off()

x_dir2.on()
input("Next...")
x_dir2.on()

y_dir1.on()
input("Next...")
y_dir1.off()

y_dir2.on()
input("Next...")
y_dir2.on()

z_dir1.on()
input("Next...")
z_dir1.off()

z_dir2.on()
input("Next...")
z_dir2.on()