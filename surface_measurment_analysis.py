import numpy as np

class Orientation():
    def __init__(self, h, d, verbose=0):
        self.verbose = verbose
        self.hx, self.hy = h
        self.dx, self.dy = d
        self.old_m_x = self.old_m_y = self.old_m_z = 0.0

    def linear_estimate(self, m1, m2, m3):
        alpha = self.alpha_linear_estimate(m1)
        beta = self.beta_linear_estimate(m2)
        gamma = self.gamma_linear_estimate(m3)
        return alpha, beta, gamma

    def delta_x_angle(self, m1):
        theta = self.tilt_angle(m1, self.old_m_x, self.hx, self.dx)
        self.old_m_x = m1
        return theta

    def delta_y_angle(self, m2):
        theta = self.tilt_angle(m2, self.old_m_y, self.hy, self.dy)
        self.old_m_y = m2
        return theta

    def delta_z_distance(self, m3):
        delta_z = m3 - self.old_m_z
        self.old_m_z = m3
        return delta_z

    def tilt_angle(self, m, old_m, h, d):
        delta_m = old_m - m
        alpha = np.arctan2(d - m, h)
        A = np.sqrt(h**2 + (d-m)**2)
        q = np.sqrt(delta_m**2 + A**2 - 2*delta_m*A*np.cos((np.pi/2)-alpha))
        theta = np.arcsin(delta_m*np.sin((np.pi/2)-alpha)/q)
        return theta

    def condition_angle(self,x):
        x = x%(2*np.pi)
        if x < 0:
            x = x%(-2*np.pi)
            # if x < -1*np.pi:
            #     x = (2*np.pi) + x
        elif x > 0:
            x = x%(2*np.pi)
            # if x > np.pi:
            #     x = (2*np.pi) - x

        return x

    def sec(self, x):
        return 1/np.cos(x)

    def print(self, verbose, *args):
        if verbose <= self.verbose:
            print(*args)

if __name__ == '__main__':
    # [x, y , z]
    h =  [0.87, 0.87]   # the hight of the sensor from the floor
    d = [0.82, 0.80]     # the distance between the sensor and the wellhead
    m1_list = np.random.normal(loc=0.839, scale=0.01, size=20)            # measurments of the sensor on the x axis
    m1_list = np.append(m1_list, m1_list[-1])
    m2_list = np.random.normal(loc=0.851, scale=0.01, size=20)           # measurments of the sensor on the y axis
    m2_list = np.append(m2_list, m2_list[-1])
    m3_list = np.random.normal(loc=0.990, scale=0.01, size=20)           # measurments of the sensor on the z axis
    m3_list = np.append(m3_list, m3_list[-1])
    verbose = 0        # the more the value the more stuff it will print
    orient = Orientation(h, d, verbose=verbose)
    for m1,m2,m3 in zip(m1_list, m2_list, m3_list):
        print('estimation results: ')
        print('m1 = {}, m2 = {}, m3 = {}'.format(m1,m2,m3))
        print('old_m1 = {}, old_m2 = {}, old_m3 = {}'.format(orient.old_m_x,orient.old_m_y,orient.old_m_z))
        d_x_angle = orient.delta_x_angle(m1)
        d_y_angle = orient.delta_y_angle(m2)
        d_z_dist = orient.delta_z_distance(m3)
        print('d_x_angle = {} rad, d_y_angle = {} rad, d_z_dist = {} m'.format(d_x_angle, d_y_angle, d_z_dist))
        print('d_x_angle = {} deg, d_y_angle = {} deg, d_z_dist = {} mm'.format(np.rad2deg(d_x_angle), np.rad2deg(d_y_angle), d_z_dist*1000))
