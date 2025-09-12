import sdl2
import sdl2.ext

sdl2.SDL_Init(sdl2.SDL_INIT_JOYSTICK)
sdl2.SDL_JoystickEventState(sdl2.SDL_ENABLE)

joystick = sdl2.SDL_JoystickOpen(0)
print(f"Opened joystick: {sdl2.SDL_JoystickName(joystick).decode()}")

event = sdl2.SDL_Event()
running = True
while running:
    while sdl2.SDL_PollEvent(event):
        if event.type == sdl2.SDL_JOYBUTTONDOWN:
            print(f"Button {event.jbutton.button} pressed")
        elif event.type == sdl2.SDL_JOYAXISMOTION:
            print(f"Axis {event.jaxis.axis} value: {event.jaxis.value}")
        elif event.type == sdl2.SDL_JOYHATMOTION:
            print(f"Hat {event.jhat.hat} value: {event.jhat.value}")
