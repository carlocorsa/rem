# Third party imports
import numpy as np

# Local application imports
from utils import constants
from simulations import variables, scaling

# Load constants
D = constants.D
Cf = constants.CF


def compute_atp(pollutant, rad_eff, th, c_scaling=True, erf_scaling=True, lifetime_range=False):
    """Compute integrated and pulse Absolute Temperature Potential (ATP).
    Depending on the radiative efficiency `rad_eff` the returned potentials
    can be either regional or global.

    Parameters
    ----------
    pollutant: str
        One of the following single lifetime pollutants:
        - SO2
        - BC
        - CH4

    rad_eff: float
        Radiative efficiency for single-lifetime pollutant experiments.

    th: int
        Time horizon.

    c_scaling: boolean (default=True)
        If True, apply climate sensitivity multi-model scaling.

    erf_scaling: boolean (default=True)
        If True, apply radiative forcing multi-model scaling.

    lifetime_range: boolean (default=False)
        If True, use the pollutant lifetime range values
        (tau - tau_std, tau, tau + tau_std) and return a
        potential value for each of them.

    Returns
    -------
    iatp: float or array of floats
        Integrated absolute (either regional or global) temperature potentials.

    atp: float or array of floats
        Pulse absolute (either regional or global) temperature potentials.
    """

    assert pollutant in constants.SLP, "{} is not an accepted pollutant".format(pollutant)

    # Check whether to use the lifetime range rather than a single value
    if lifetime_range:
        tau = np.array([
            constants.SPECS[pollutant]['tau'] - constants.SPECS[pollutant]['tau_std'],
            constants.SPECS[pollutant]['tau'],
            constants.SPECS[pollutant]['tau'] + constants.SPECS[pollutant]['tau_std']
        ])
    else:
        tau = constants.SPECS[pollutant]['tau']

    # Get scaled climate sensitivity
    if c_scaling:
        c_scaled = variables.get_scaled_climate_sensitivity(pollutant)
    else:
        c_scaled = [constants.C1, constants.C2]

    # Keep or remove scaling from the radiative forcing
    if pollutant == 'SO2':
        if not erf_scaling:
            rad_eff = rad_eff / scaling.get_mm_scaling(pollutant)[1]

    # Compute the integrated absolute temperature potential
    iatp = sum((rad_eff * tau * c_scaled[j] / (tau - D[j])) *
               (tau * (1 - np.exp(-th / tau)) - D[j] * (1 - np.exp(-th / D[j])))
               for j in range(2))

    # Compute the pulse absolute temperature potential
    atp = sum(((rad_eff * tau * c_scaled[j]) / (tau - D[j])) *
              (np.exp(-th / tau) - np.exp(-th / D[j]))
              for j in range(2))

    return iatp, atp


def compute_app(pollutant, rad_eff, rad_eff_a, th, rr_precip_avg, precip_avg):
    """Compute integrated and pulse Absolute Regional Precipitation
    Potential (ARPP) for single lifetime pollutants.

    Parameters
    ----------
    Parameters
    ----------
    pollutant: str
        One of the following single lifetime pollutants:
        - SO2
        - BC
        - CH4

    rad_eff: float
        Global radiative efficiency change due to
        perturbation of `pollutant`.

    rad_eff_a: float
        Change in the atmospheric component of the global
        radiative efficiency due to perturbation of `pollutant`.

    th: int
        Time horizon.

    rr_precip_avg: float
        Average regional precipitation difference
        due to perturbation of `pollutant`.

    precip_avg: float
        Global regional precipitation difference
        due to perturbation of `pollutant`.

    Returns
    -------
    iarpp: array of floats
        Integrated Absolute Regional Precipitation Potential (iARPP).

    slow_iarpp: array of floats
        Slow response component of the iARPP.

    fast_iarpp: array of floats
        Fast response component of the iARPP.

    arpp: array of floats
        Pulse Absolute Regional Precipitation Potential (ARPP).

    slow_arpp: array of floats
        Slow response component of the ARPP.

    fast_arpp: array of floats
        Fast response component of the ARPP.
    """

    assert pollutant in constants.SLP, "{} is not an accepted pollutant".format(pollutant)

    # Load constants
    tau = constants.SPECS[pollutant]['tau']
    fp = constants.SPECS[pollutant]['fp']
    k = constants.SPECS[pollutant]['k']

    # Compute the absolute global temperature potentials
    iagtp, agtp = compute_atp(pollutant, rad_eff, th)

    # Compute the integrated absolute regional precipitation potential (iARPP)
    iarpp = Cf * (k * iagtp - fp * rad_eff_a * tau * (1 - np.exp(-th / tau))) * (rr_precip_avg / precip_avg)

    # Compute the slow response component of the iARPP
    slow_iarpp = Cf * k * iagtp * (rr_precip_avg / precip_avg)

    # Compute the fast response component of the iARPP
    fast_iarpp = Cf * -fp * rad_eff_a * tau * (1 - np.exp(-th / tau)) * (rr_precip_avg / precip_avg)

    # Compute the pulse absolute regional precipitation potential (ARPP)
    arpp = Cf * (k * agtp - fp * rad_eff_a * np.exp(-th / tau)) * (rr_precip_avg / precip_avg)

    # Compute the slow response component of the ARPP
    slow_arpp = Cf * k * agtp * (rr_precip_avg / precip_avg)

    # Compute the fast response component of the ARPP
    fast_arpp = Cf * -fp * rad_eff_a * np.exp(-th / tau) * (rr_precip_avg / precip_avg)

    return iarpp, slow_iarpp, fast_iarpp, arpp, slow_arpp, fast_arpp
