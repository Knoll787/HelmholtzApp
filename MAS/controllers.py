import time

class PID:
    def __init__(self, kp, ki, kd, 
                 setpoint=0, 
                 output_limits=(None, None)):
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.setpoint = setpoint
        self.output_limits = output_limits
        
        self._integral = 0
        self._last_error = 0
        self._last_time = None

    def compute(self, measurement):
        # current time
        now = time.time()
        if self._last_time is None:
            self._last_time = now
            return 0
        
        dt = now - self._last_time
        error = self.setpoint - measurement
        
        # PID terms
        p = self.kp * error
        self._integral += error * dt
        i = self.ki * self._integral
        d = self.kd * (error - self._last_error) / dt if dt > 0 else 0
        
        # save for next iteration
        self._last_error = error
        self._last_time = now
        
        # total output
        output = p + i + d
        
        # clamp to output limits (e.g., current range of coils)
        low, high = self.output_limits
        if low is not None:
            output = max(low, output)
        if high is not None:
            output = min(high, output)
        
        return output
