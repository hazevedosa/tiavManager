import time

class PidController:

    def setPoint(self, target, kprop, kint, kderiv):
        self.set_point = target
        self.kprop = kprop
        self.kint = kint
        self.kderiv = kderiv
        self.prev_time = time.time()
        self.prev_err = 0
        self.sum = 0
        self.prev_set = False

    def control(self, process_var):
        t = time.time()
        diff = t - self.prev_time

        err = self.set_point - process_var

        # print(self.set_point)

        if not self.prev_set:
            self.prev_set = True
            self.prev_err = err
            return 0

        dt = float(diff) * 0.000001
        dt = max(dt, 0.01)
        prop_gain = 0.0
        deriv_gain = 0.0
        int_gain = 0.0

        if not self.kprop == 0:
            prop_gain = err * self.kprop

        if not self.kderiv == 0:
            deriv = (err - self.prev_err) / dt
            deriv_gain = deriv * self.kderiv

        if not self.kint == 0:
            self.sum += err * dt
            int_gain = self.sum * self.kint

        self.prev_err = err
        self.prev_time = t

        return prop_gain + deriv_gain + int_gain
