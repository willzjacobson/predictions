# coding=utf-8
__author__ = 'ashishgagneja'

# original author
# __author__ = 'SuperCell93'

# NOAA formula using the Arden Buck Equation to find water vapor mixing ratios

import math


def compute_bulb(temp, dewpt, pressure):
    """
    compute wet bulb temperature in Celsius

    :param temp: float
        temperature in Fahrenheit
    :param dewpt: float
        dew point temperature in Fahrenheit
    :param pressure: float
        pressure in Hg inches

    :return: float
    """

    temp_c = _convert_to_c(temp)
    dewpt_c = _convert_to_c(dewpt)
    pressure_mb = _convert_to_pressure_nmb(pressure)

    es = float(_esubx(temp_c))
    e2 = _inverted_rh(es, _relative_hum(temp_c, dewpt_c))

    tw_guess = 0  # guess that the wet bulb is the dew point
    increase = 10  # start by increasing by 10
    prev_sign, e_diff = 1, 1

    return _calculate_bulb(e_diff, tw_guess, temp_c, pressure_mb, e2, prev_sign,
                         increase)



def compute_bulb_helper(args):
    """
    same as compute_bulb() except takes all its parameters as a list

    :param args: list
        list of parameter if compute_bulb()

    :return: same as compute_bulb()
    """

    temp, dewpt, pressure = args
    return compute_bulb(temp, dewpt, pressure)



def _convert_to_c(temp_f):
    """
    convert temperature from fahrenheit to celsius

    :param temp_f: float
        temperature in fahrenheit
    :return: float
    """
    return (5.0 / 9.0) * (temp_f - 32.0)  # Convert F to C



def _convert_to_pressure_nmb(pressure_hg):
    """
    conver pressure from Hg inches to millibars
    :param pressure_hg: float
        pressure in Hg inches
    :return: float
    """
    return 33.8639 * pressure_hg



def _esubx(temp_c):  # accept C temp
    return 6.112 * math.exp(
        (17.67 * temp_c) / (temp_c + 243.5))



def _calculate_bulb(e_diff, wetbulb_guess, thetemp, press_mb, e, prev_sign,
                   increase):

    while abs(e_diff) > 0.05:

        ew_guess = 6.112 * math.exp(
                17.67 * wetbulb_guess / (wetbulb_guess + 243.5))
        e_guess = ew_guess - press_mb * (
            float(thetemp) - float(wetbulb_guess)) * 0.00066 * (
            1 + (0.00115 * wetbulb_guess))
        e_diff = float(e) - e_guess
        increase = float(increase)

        if e_diff == 0:
            break

        else:
            if e_diff < 0:
                cursign = -1
                if cursign != prev_sign:
                    prev_sign = cursign
                    increase /= 10
                else:
                    increase = increase

            else:
                cursign = 1
                if cursign != prev_sign:
                    prev_sign = cursign
                    increase /= 10
                else:
                    increase = increase

        if abs(e_diff) <= 0.05:
            break
        else:
            wetbulb_guess += increase * prev_sign

    return wetbulb_guess


def _relative_hum(temp, dewpt):
    """
    compute relative humidity

    :param temp: float
        temperature in Celsius
    :param dewpt: float
        dew point in Celsius

    :return: float
    """
    return 100 * (
        math.exp(17.625 * dewpt / (243.04 + dewpt)) / math.exp(
                17.625 * temp / (243.04 + temp)))


def _inverted_rh(es, rh):
    return es * (float(rh) / 100.0)
