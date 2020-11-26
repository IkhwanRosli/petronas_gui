import numpy as np

class Orientation():
    def __init__(self, h1, d1, h2, d2, h3, d3, verbose=0):
        self.verbose = verbose
        self.h1, self.h2, self.h3 = h1, h2, h3
        self.d1, self.d2, self.d3 = d1, d2, d3

    def analyze_xy(self, m1, m2, lr=1e-5, min_loss=1e-5):
        alpha, beta = self.linear_estimate(m1,m2)
        # alpha, beta = self.condition_angle(alpha), self.condition_angle(beta)
        accurate_linear = self.check_linear_accuracy(alpha,beta)
        self.print(1,'Linear estimate:')
        self.print( 1,'alpha = {} rad, beta = {} rad'.format(alpha, beta))
        self.print( 1,'alpha = {} deg, beta = {} deg'.format(np.rad2deg(alpha), np.rad2deg(beta)))
        lr = self.lr_schedular(accurate_linear, lr)
        alpha, beta = self.optimizing_the_angles(alpha, beta, m1, m2, min_loss, lr)
        alpha, beta = self.condition_angle(alpha), self.condition_angle(beta)
        self.print( 1,'optimized estimate:')
        self.print( 1,'alpha = {} rad, beta = {} rad'.format(alpha, beta))
        self.print( 1,'alpha = {} deg, beta = {} deg'.format(np.rad2deg(alpha), np.rad2deg(beta)))
        return alpha, beta

    def calc_w1(self, m1):
        return (self.d1-m1)/np.sqrt(self.h1**2 + (self.d1-m1)**2)

    def calc_w2(self, m2):
        return (self.d2-m2)/np.sqrt(self.h2**2 + (self.d2-m2)**2)

    def linear_estimate(self, m1, m2):
        alpha = self.alpha_linear_estimate(m1)
        beta = self.beta_linear_estimate(m2)
        return alpha, beta

    def alpha_linear_estimate(self, m1):
        w1 = self.calc_w1(m1)
        alpha = np.pi/2 - w1
        alpha = self.condition_angle(alpha)
        return alpha

    def beta_linear_estimate(self, m2):
        w2 = self.calc_w2(m2)
        beta = np.pi/2 - w2
        beta = self.condition_angle(beta)
        return beta

    def optimizing_the_angles(self, init_alpha, init_beta, m1, m2, min_loss, lr):
        w1 = self.calc_w1(m1)
        w2 = self.calc_w2(m2)
        alpha, beta = init_alpha, init_beta
        L = self.loss(alpha, beta, w1, w2)
        # lr = self.lr_schedular(L, lr)
        self.print( 1, 'loss: ',L, ' , lr: ', lr)
        i = 0
        while (L > min_loss):
            alpha_grad = self.alpha_gradient_to_L(alpha, beta, w1, w2)
            beta_grad = self.beta_gradient_to_L(alpha, beta, w1, w2)
            alpha = self.gradient_descent(alpha, alpha_grad, lr)
            beta = self.gradient_descent(beta, beta_grad, lr)
            L = self.loss(alpha, beta, w1, w2)
            i += 1
            self.print( 2, 'iteration: ', i, 'loss: ',L, ' , lr: ', lr)
        self.print( 1, 'iterations: ', i, 'loss: ',L, ' , lr: ', lr)
        return alpha, beta

    def lr_schedular(self, accurate_linear, lr):
        if accurate_linear:
            return 1e-9
        else:
            return lr

    def check_linear_accuracy(self, alpha, beta):
        if np.abs(alpha) > np.deg2rad(80) and np.abs(alpha) < np.deg2rad(100) :
            if np.abs(beta) > np.deg2rad(80) and np.abs(beta) < np.deg2rad(100):
                return True
        return False

    def loss(self, alpha, beta, w1, w2):
        a = np.tan(alpha)*np.tan(beta)
        b = (1/(w1*w2+1e-10))
        return (a - b)**2

    def alpha_gradient_to_L(self, alpha, beta, w1, w2):
        a = np.tan(alpha)*np.tan(beta)
        b = (1/(w1*w2+1e-10))
        c = np.tan(beta)*self.sec(alpha)**2
        return 2*c*(a-b)

    def beta_gradient_to_L(self, alpha, beta, w1, w2):
        a = np.tan(alpha)*np.tan(beta)
        b = (1/(w1*w2+1e-10))
        c = np.tan(alpha)*self.sec(beta)**2
        return 2*c*(a-b)

    def gradient_descent(self, var, gradient, lr):
        return var-(lr*gradient)

    def condition_angle(self,x):
        x = x%(2*np.pi)
        if x > np.pi:
            x = (2*np.pi) - x
        return x

    def sec(self, x):
        return 1/np.cos(x)

    def print(self, verbose, *args):
        if verbose <= self.verbose:
            print(*args)

if __name__ == '__main__':
    h1 = h2 = h3 = 0.2   # the hight of the sensor from the floor
    d1 = d2 = d3 = 1     # the distance between the sensor and the rod
    m1 = 0.7            # measurment of the sensor on the x axis
    m2 = 0.99            # measurment of the sensor on the y axis
    verbose = 0          # the more the value the more stuff it will print
    orient = Orientation(h1, d1, h2, d2, h3, d3, verbose=verbose)
    alpha = orient.alpha_linear_estimate(m1) # linear estimation of alpha, accurate for small ((pi/2) - alpha) values
    beta = orient.beta_linear_estimate(m2) # linear estimation of beta, accurate for small ((pi/2) - beta) values
    print('linear estimation results: ')
    print('alpha = {} rad, beta = {} rad'.format(alpha, beta))
    print('alpha = {} deg, beta = {} deg'.format(np.rad2deg(alpha), np.rad2deg(beta)))
    alpha, beta = orient.analyze_xy(m1, m2, lr=1e-5, min_loss=1e-5) #more accurate calcualtion of both alpha and beta, it uses gradient descent to solve the non linear equations
    print('more accurate results: ')
    print('alpha = {} rad, beta = {} rad'.format(alpha, beta))
    print('alpha = {} deg, beta = {} deg'.format(np.rad2deg(alpha), np.rad2deg(beta)))
