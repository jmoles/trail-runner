"""
This module contains utilities specific to chemistry models for the
trail computations.
"""
import numpy as np
import scipy.integrate
import pylab
import sys


class DelayLine(object):
    """ Object to model a delay line implemented in a chemistry.
    """

    __MIN_DL_LENGTH = 2
    __RATE_CNST_DIM_1 = 3
    __MIN_DIM = 2

    def __init__(self,
                 rate_constants,
                 runtime=100,
                 step=0.01,
                 user_interactive=True):
        # Verify that the rate constants are correct type and length.
        if type(rate_constants) != type(np.array(0)):
            raise ValueError(
                "rate_constants is not an {0}.".format(type(np.array(0))))

        if len(rate_constants) < self.__MIN_DL_LENGTH:
            raise ValueError(
                "Length ({0}) must be greater than {1}.".format(
                    len(rate_constants),
                    self.__MIN_DL_LENGTH))

        if rate_constants.ndim < self.__MIN_DIM:
            raise ValueError(
                "Number of dimensions ({0}) must be at least {1}.".format(
                    rate_constants.ndim,
                    self.__MIN_DIM))


        if rate_constants.shape[1] != self.__RATE_CNST_DIM_1:
            raise ValueError(
                "Second dimension of rate constants is {0} and must" \
                " be {1}.".format(
                    rate_constants.shape[1],
                    self.__RATE_CNST_DIM_1))

        if np.any(rate_constants < 0.0):
            raise ValueError(
                "Rate constant is less than 0: {0}.".format(
                    rate_constants))

        # Perform validation on the runtime and step.
        if runtime <= 0:
            raise ValueError(
                "Runtime ({0}) must be grater than 0.".format(runtime))

        if step <= 0:
            raise ValueError(
                "Step ({0}) must be greater than 0.".format(runtime))

        # Store the passed in variables
        self.__rate_k = rate_constants
        self.__length = len(rate_constants)

        # Used as a queue to store the ideal value throughout computation.
        self.ideal_values = [0] * self.__length

        # Build the set of velocity equations and dy functions
        # Velocity equations take this form:
        #   X_{n-1}C + X_{n}S -> X_{n}IM
        #   X_{n}IM           -> X_{n}    + X_{n}C + X_{n}S
        #   X_{n}S            -> X_{n-1}S
        self.__eq_vel = []

        for row in self.__rate_k:
            self.__eq_vel.append(lambda XC, XS: row[0] * XC**1 * XS**1)
            self.__eq_vel.append(lambda XIM: row[1] * XIM**1)
            self.__eq_vel.append(lambda XS: row[2] * XS**1)


        # Store and set up some other variables
        self.__runtime = runtime
        self.__step = step
        self.__user_interactive = user_interactive
        self.__y_vals = None
        self.__prev_y_final = [0] * self.__length

    def evaluate(self, value):
        """ Evaluates the delay line chemistry. User provides an input
        value that is moved through the delay line. Returns a list of
        the values in the delay line.

        Returns:
            list. List of values on delay line outputs in order from
            1 up to length of delay line.

        """
        t_val = np.arange(0, self.__runtime, self.__step)

        y0_val = DelayLine.build_y0_input(value, self.__prev_y_final)

        ode_res, info = scipy.integrate.odeint(
            func=DelayLine.__ode_func,
            y0=y0_val,
            t=t_val,
            args=(self.__eq_vel, self.__length),
            full_output=True)



        if not info["message"].startswith("Integration successful."):
            print "Y0: " + str(y0_val)
            print "t0: " + str(t_val)
            print "__length: " + str(self.__length)
            print "Rate Constants: " + str(self.__rate_k)
            print info
            sys.exit()

        # If we get here, have passed integration. Store the ideal value
        # and pop one from the end.
        self.ideal_values.insert(0, value)
        self.ideal_values.pop()

        # Get the actual values from the output of the system.
        # Results (and *desired* ones) are ordered in:
        #  XIN, X1S, X1IM, *X1*, X1C, X2S, X2IM, *X2*, X2C ...
        ret_list = ode_res[len(ode_res) - 1][3::4]

        # If this is a user mode, save the Y values.
        if self.__user_interactive:
            if self.__y_vals is None:
                self.__y_vals = ode_res
            else:
                self.__y_vals = np.append(self.__y_vals, ode_res, axis=0)

        self.__prev_y_final = ret_list

        return ret_list

    def show_plot(self):
        """ Returns a dictionary with the concentration of the species
        throughout the last evaluation.

        Returns:
            dict. Keys of species names with lists of species concentrations
            throughout the last evaluation.

        """

        # Determine the length of the x axis to plot.
        t_val_mult = self.__y_vals.shape[0] / (self.__runtime / self.__step)
        t_axis = np.arange(0, self.__runtime * t_val_mult, self.__step)

        plot1 = pylab.plot(t_axis, self.__y_vals)
        pylab.legend(plot1, [
            "XIN", "X1S", "X1IM", "X1", "X1C",
            "X2S", "X2IM", "X2", "X2C", "X3S",
            "X3IM", "X3", "X3C"])
        pylab.show()



    @staticmethod
    def build_y0_input(input_val, prev_val):
        """ Generates the appropriate numpy array ready for input to ODE.
        prev_val is a list-like object that matches the length of the
        delay line.
        """

        ret_val = np.array([input_val])

        for curr_n in range(0, len(prev_val)):
            if curr_n == len(prev_val) - 1:
                signal_val = 1.0
            else:
                signal_val = 0.0

            ret_val = np.append(ret_val, np.array([
                signal_val,              # XnS
                0.0,                     # XnIM
                0.0,                     # Xn
                prev_val[curr_n]         # XnC
                ]))

        return ret_val

    @staticmethod
    def __ode_func(y_in, t0, vel, length, debug=False):
        """ Builds the dy functions. Designed for passing as the func for
        scipy.integrate.odeint.

        How these functions look:

         Special case for X at start:
            XIN:    : -1 * vel(0) ("Sourced" from user)
         Otherwise,
            X_{n}S  : -1 * vel(0) + 1 * vel(1) - 1 * vel(2)
            X_{n}IM :  1 * vel(0) - 1 * vel(1)
            X_{n}   :  1 * vel(1)  ("Consumed" by next step)
            X_{n}C  :  1 * vel(1) - 1 * vel(3)
        Special case for last X_{n}C
            X_{n}C  :  1 * vel(1)
        """

        dy_list = []
        # Do the custom part needed for the first row:
        # X, X1S, X1IM, X1, and X1C
        dy_list.append(
            - 1 * vel[0](y_in[0], y_in[1]))
        dy_list.append(
            - 1 * vel[0](y_in[0], y_in[1])
            + 1 * vel[1](y_in[2])
            - 1 * vel[2](y_in[1])
            + 1 * vel[5](y_in[5]))
        dy_list.append(
            + 1 * vel[0](y_in[0], y_in[1])
            - 1 * vel[1](y_in[2]))
        dy_list.append(
            + 1 * vel[1](y_in[2]))
        dy_list.append(
            + 1 * vel[1](y_in[2])
            - 1 * vel[3](y_in[4], y_in[5]))

        # Now do the listing for the rest of the length.
        for curr_n in range(2, length + 1, 1):
            vel_base_idx = (curr_n - 1) * 3
            y_base_idx   = ((curr_n - 1) * 4) + 1

            if debug:

                print """
------------------------------------------------------------------------
curr_n       : {0}
Length       : {1}
vel_base_idx : {2}
y_base_idx   : {3}
                """.format(curr_n, length, vel_base_idx, y_base_idx)

                # Last element, does not have additional supplier.
                if curr_n >= length:
                    print """
X{7}S: - 1 * vel[{0}](y_in[{1}], y_in[{2}])
         + 1 * vel[{3}](y_in[{4}])
         - 1 * vel[{5}](y_in[{6}]))
                    """.format(
                        vel_base_idx, y_base_idx - 1, y_base_idx,
                        vel_base_idx + 1, y_base_idx + 1,
                        vel_base_idx + 2, y_base_idx,
                        curr_n)
                else:
                    print """
X{9}S: - 1 * vel[{0}](y_in[{1}], y_in[{2}])
       + 1 * vel[{3}](y_in[{4}])
       - 1 * vel[{5}](y_in[{6}])
       + 1 * vel[{7}](y_in[{8}]))
                    """.format(
                        vel_base_idx, y_base_idx - 1, y_base_idx,
                        vel_base_idx + 1, y_base_idx + 1,
                        vel_base_idx + 2, y_base_idx,
                        vel_base_idx + 5, y_base_idx + 4,
                        curr_n)

                print """
X{5}IM: + 1 * vel[{0}](y_in[{1}], y_in[{2}])
      - 1 * vel[{3}](y_in[{4}]))
                """.format(
                    vel_base_idx, y_base_idx - 1, y_base_idx,
                    vel_base_idx + 1, y_base_idx + 1,
                    curr_n)

                print """
X{2}: + 1 * vel[{0}](y_in[{1}])
                """.format(
                    vel_base_idx + 1, y_base_idx + 1,
                    curr_n)

                # Last Element does not have XnC consumer.
                if curr_n >= length:
                    print """
    X{2}C: + 1 * vel[{0}](y_in[{1}]))
                    """.format(
                        vel_base_idx + 1, y_base_idx + 1,
                        curr_n)
                else:
                    print """
    X{5}C:  + 1 * vel[{0}](y_in[{1}])
            - 1 * vel[{2}](y_in[{3}], y_in[{4}]))
                    """.format(
                        vel_base_idx + 1, y_base_idx + 1,
                        vel_base_idx + 3, y_base_idx + 3, y_base_idx + 4,
                        curr_n)

            # XnS
            if curr_n >= length:
                # At the end, no input from another function (from user).
                dy_list.append(
                    - 1 * vel[vel_base_idx](
                        y_in[y_base_idx - 1], y_in[y_base_idx])
                    + 1 * vel[vel_base_idx + 1](y_in[y_base_idx + 1])
                    - 1 * vel[vel_base_idx + 2](y_in[y_base_idx]))
            else:
                dy_list.append(
                    - 1 * vel[vel_base_idx](
                        y_in[y_base_idx - 1], y_in[y_base_idx])
                    + 1 * vel[vel_base_idx + 1](y_in[y_base_idx + 1])
                    - 1 * vel[vel_base_idx + 2](y_in[y_base_idx])
                    + 1 * vel[vel_base_idx + 5](y_in[y_base_idx + 4]))

            # XnIM
            dy_list.append(
                + 1 * vel[vel_base_idx](y_in[y_base_idx - 1], y_in[y_base_idx])
                - 1 * vel[vel_base_idx + 1](y_in[y_base_idx + 1]))

            # Xn
            dy_list.append(
                + 1 * vel[vel_base_idx + 1](y_in[y_base_idx + 1]))

            # XnC
            # Last Element does not have XnC consumer.
            if curr_n >= length:
                # At the end, no further cascading.
                dy_list.append(
                    + 1 * vel[vel_base_idx + 1](y_in[y_base_idx + 1]))
            else:
                dy_list.append(
                    + 1 * vel[vel_base_idx + 1](y_in[y_base_idx + 1])
                    - 1 * vel[vel_base_idx + 3](
                        y_in[y_base_idx + 3], y_in[y_base_idx + 4]))


        return np.array(dy_list)
