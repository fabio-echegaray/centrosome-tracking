import logging

import numpy as np
from lmfit import Parameters

np.set_printoptions(1)
logger = logging.getLogger(__name__)


class PlanarElastica():
    def __init__(self, L=1.0, E=0.625, J=1.0, F=1.0,
                 x0=0.0, y0=0.0, m0=0.01,
                 phi=0.0, theta=3 * np.pi / 2):
        """
        Base class for an elastic rod

        :param L: Length of the fiber.
        :param E: Young's modulus.
        :param J: Area moment of inertia of the cross section of the fiber(rod). EJ is called flexural rigidity.
        :param F: Initial force (at s=0) in pN.
        :param x0: Initial x coordinate of the fiber.
        :param y0: Initial x coordinate of the fiber.
        :param m0: Initial angular momentum (at s=0).
        :param phi: Spatial rotation of the whole fiber.
        :param theta: Initial rotation angle with respect to the arc length
        """
        self._L = L
        self.E = E
        self.J = J
        self.B = E * J  #

        self._F = 0.0
        self._F = F

        self._x0 = x0
        self._y0 = y0
        self.phi = phi

        self._endX = 0.0
        self._endY = 0.0

        self.m0 = m0
        self.theta0 = theta
        self.res = None
        self.curve_x = np.array([0])
        self.curve_y = np.array([0])
        self.curve = None

    def __str__(self):
        str = 'Fiber:\r\n' \
              '{:8} {:8} {:8} | {:9} {:9} {:9} {:9} | {:8} {:8} {:8} {:8}\r\n' \
            .format('L', 'J', 'E', ' x0', ' y0', ' endX', ' endY', 'N1', 'N2', 'm0', 'phi', 'theta_e', 'lambda')
        str += '{:0.2e} {:0.2e} {:0.2e} | {: .2e} {: .2e} {: .2e} {: .2e} | {:0.2e} {:0.2e} {:0.2e} {:0.2e}' \
            .format(self.L, self.J, self.E,
                    self.x0, self.y0, self.endX, self.endY,
                    self.m0, self.phi, self.theta0, self.lambda_const())
        return str

    def lambda_const(self):
        F = np.sqrt(self.N1 ** 2 + self.N2 ** 2)
        return F / self.B

    @property
    def x0(self):
        return self._x0

    @property
    def y0(self):
        return self._y0

    @x0.setter
    def x0(self, value):
        self._x0 = value

    @y0.setter
    def y0(self, value):
        self._y0 = value

    @property
    def endX(self):
        return self._endX

    @property
    def endY(self):
        return self._endY

    @endX.setter
    def endX(self, value):
        self._endX = value
        self.L = np.sqrt(self.endX ** 2 + self.endY ** 2)
        logging.debug('setting endX: endX={:02.2f} endY={:02.2f} L={:02.2f}'.format(self._endX, self._endY, self.L))

    @endY.setter
    def endY(self, value):
        self._endY = value
        self.L = np.sqrt(self.endX ** 2 + self.endY ** 2)
        logging.debug('setting endY: endX={:02.2f} endY={:02.2f} L={:02.2f}'.format(self._endX, self._endY, self.L))

    @property
    def F(self):
        return self._F * self.B / self.L ** 2

    @F.setter
    def F(self, value):
        self._F = value / self.B * self.L ** 2

    @property
    def N1(self):
        return self.F * np.cos(self.theta0)

    @property
    def N2(self):
        return self.F * np.sin(self.theta0)

    @property
    def L(self):
        return self._L

    @L.setter
    def L(self, value):
        _F = self.F
        self._L = value
        self._F = _F / self.B * self.L ** 2

    @property
    def parameters(self):
        params = Parameters()
        params.add('L', value=self.L)
        params.add('E', value=self.E)
        params.add('J', value=self.J, vary=False)
        params.add('F', value=self.F)
        params.add('x0', value=self.x0)
        params.add('y0', value=self.y0)
        params.add('m0', value=self.m0)
        params.add('phi', value=self.phi)
        params.add('theta', value=self.theta0)

        return params

    @parameters.setter
    def parameters(self, value):
        assert type(value) == Parameters, 'value is not a lmfit parameters object'
        vals = value.valuesdict()

        self.L = vals['L']
        self.E = vals['E']
        self.J = vals['J']
        self.B = self.E * self.J

        self.F = vals['F']

        self.x0 = vals['x0']
        self.y0 = vals['y0']
        self.phi = vals['phi']

        self.m0 = vals['m0']
        self.theta0 = vals['theta']
        self.phi = vals['phi']

    def normalized_variables(self):
        return (self.x0 / self.L,
                self.y0 / self.L,
                self.endX / self.L,
                self.endY / self.L)

    def eval(self, num_points=1000):
        if self.F < 0:
            self.F *= -1
            self.theta0 += 2 * np.pi

    def plot(self, ax, alpha=0.5, lw_curve=1):
        if np.isnan(self.curve_x).any() or np.isnan(self.curve_y).any():
            raise Exception("NaNs in computed curves, can't plot")

        self.curve = ax.plot(self.curve_x, self.curve_y, lw=lw_curve, c='r', alpha=alpha,
                             label='%0.1e' % (self.E * self.J), zorder=1, picker=lw_curve)[0]

        L = np.sqrt(np.diff(self.curve_x) ** 2 + np.diff(self.curve_y) ** 2).sum()

        logger.debug(
            'first ({:04.2f},{:04.2f}) last ({:04.2f},{:04.2f}) phi {:04.2f} length {:04.2f} curve length {:04.2f}'.
            format(self.curve_x[0], self.curve_y[0], self.curve_x[-1], self.curve_y[-1], self.phi, self.L, L))