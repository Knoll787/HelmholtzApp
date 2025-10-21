import time

class PID:
    def __init__(self, axis, 
                 kp, ki, kd, 
                 setpoint=0, 
                 output_limits=(None, None)):
        self.axis=axis
        self.kp = kp
        self.ki = ki
        self.kd = kd
        #self.kaw = 10 
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
        
        # --- unsaturated output ---
        u = p + i + d
        
        # clamp to output limits
        low, high = self.output_limits
        u_sat = u
        if low is not None:
            u_sat = max(low, u_sat)
        if high is not None:
            u_sat = min(high, u_sat)

        # --- back-calculation anti-windup ---
        if hasattr(self, "kaw") and self.kaw > 0 and dt > 0:
            # correct integral term based on difference
            self._integral += (self.kaw / self.ki) * (u_sat - u) * dt
            # recompute integral contribution
            i = self.ki * self._integral

        # total saturated output
        output = p + i + d
        if low is not None:
            output = max(low, output)
        if high is not None:
            output = min(high, output)

        self.log(self.axis, time=now, pos=measurement, 
            ctrl_out=output, error=error, 
            kp=self.kp, ki=self.ki, kd=self.kd) 
        return output

    

    def step(self, measurement):
        now = time.time()
        if self._last_time is None:
            self._last_time = now
            return 0
        dt = now - self._last_time
        output = 0
        error=0

        
        self.log(self.axis, time=now, pos=measurement, 
            ctrl_out=output, error=error, 
            kp=self.kp, ki=self.ki, kd=self.kd) 
        return -100 
        
    
    def log(self, axis, time, pos, ctrl_out, error, kp, ki, kd):
        with open("../data/test.csv", "a", buffering=1, encoding="utf-8") as f:
            data = f"{time},{axis},{pos},{self.setpoint},{ctrl_out},{error},{kp},{ki},{kd}\n"
            f.write(data)