from pyXSteam.XSteam import XSteam
import logging
steamTable = XSteam(XSteam.UNIT_SYSTEM_MKS)
steamTable.logger.setLevel('ERROR')
logging.getLogger('pyXSteam.RegionSelection').setLevel('ERROR')


def stmptv(p:float, t:float) -> float:
    """Specific volume as a function of pressure and temperature

    Args:
        p (float): pressure [bara]
        t (float): temperature [°C]

    Returns:
        v (float): specific volume [m3/kg] or NaN if arguments are out of range
    """
    return steamTable.v_pt(p,t)

def stmpth(p:float, t:float) -> float:
    """Entalpy as a function of pressure and temperature

    Args:
        p (float): pressure [bara]
        t (float): temperature [°C]

    Returns:
        h (float): enthalpy [kJ/kg] or NaN if arguments are out of range
    """
    return steamTable.h_pt(p,t)

def stmtqh(t:float, q:float) -> float:
    """Entalpy as a function of temperature and steam quality

    Args:
        t (float): temperature value [°C]
        q (float): steam quality (vapour fraction) [-]

    Returns:
        h (float): enthalpy [kJ/kg] or NaN if arguments are out of range
    """
    if q > 1: q /= 100          # make sure q is decimal
    return steamTable.h_tx(t, q)

def stmpqh(p:float, q:float) -> float:
    """Entalpy as a function of pressure and steam quality

    Args:
        p (float): pressure  [bara]
        q (float): steam quality (vapour fraction) [-]

    Returns:
        h (float): enthalpy [kJ/kg] or NaN if arguments are out of range
    """
    if q > 1: q /= 100          # make sure q is decimal
    return steamTable.h_px(p, q)


def stmpht(p:float, h:float) -> float:
    """temperature as a function of pressure and enthalpy

    Args:
        p (float): preasure [bara]
        h (float): enthalpy [kJ/kg]

    Returns:
        t (float): temperature [°C] or NaN if arguments are out of range
    """
    return steamTable.t_ph(p, h)

def stmpt(p:float) -> float:
    """Saturation-temperature as a function of pressure

    Args:
        p (float): preasure [bara]

    Returns:
        tsat (float): saturation temperature [°C] or NaN if arguments are out of range
    """
    return steamTable.tsat_p(p)

def stmtp(t:float) -> float:
    """Saturation-Pressure as a function of temperature

    Args:
        t (float): temperature [°C]

    Returns:
        psat (float): saturation pressure [bara] or NaN if arguments are out of range
    """
    if t > 0:
        return steamTable.psat_t(t)
    else:
        return tp_subzero(t)
    
def tp_subzero(t):
    """Saturation pressure as a function of temperature 
    for temperatures below 0 °C
    Args:
        t (float): temperature [°C]

    Returns:
        psat (float): saturation pressure [bara]  
    
    Antoine Equation log10(P) = A − (B / (T + C))
    Parameters from webbook.nist.gov
    Temperature (K)	    A	        B	        C	        Reference
    255.9 to 373.	    4.6543	    1435.264	-64.848	    Stull, 1947

    """
    T = t + 273.15  # Convert Celsius to Kelvin    
    return 10 ** (4.6543 - (1435.264 / (T - 64.848)))  # Convert back to bara


def stmphs(p:float, h:float) -> float:
    """Specific entropy as a function of pressure and enthalpy

    Args:
        p (float): preasure [bara]
        h (float): enthalpy [kJ/kg]

    Returns:
        s (float): entropy [kJ/kgK] or NaN if arguments are out of range
    """
    return steamTable.s_ph(p,h)

def stmpsh(p:float, s:float) -> float:
    """Entalpy as a function of pressure and entropy

    Args:
        p (float): preasure [bara]
        s (float): entropy [kJ/kgK]

    Returns:
        h (float): enthalpy [kJ/kg] or NaN if arguments are out of range
    """
    return steamTable.h_ps(p,s)

def stmphv(p:float, h:float) -> float:
    """Specific volume as a function of pressure and enthalpy

    Args:
        p (float): preasure [bara]
        h (float): enthalpy [kJ/kg]

    Returns:
        v (float): specific volume [m3/kg] or NaN if arguments are out of range
    """
    return steamTable.v_ph(p,h)

def stmpth_S(p:float, t:float=None) -> float:    
    """Steam enthalpy calculation.
    Calculate enthalpy of steam. If no temperature given or temperature is below tsat, 
    then saturated steam assumed.

    Args:
        p (float): preasure [bara]
        t (float): temperature [°C] (Optional)

    Returns:
        h (float): enthalpy [kJ/kg]
    """    
    if t is None or t - 1e-6 <= stmpt(p):
        return stmpqh(p, 1.0)
    return stmpth(p, t)

def stmpth_W(p:float, t:float=None) -> float:    
    """Water enthalpy calculation.
    Calculate enthalpy of water. If no temperature given or temperature is over tsat, 
    then saturated water assumed.

    Args:
        p (float): preasure [bara]
        t (float): temperature [°C] (Optional)

    Returns:
        h (float): enthalpy [kJ/kg]
    """    
    if t is None or t - stmpt(p) >= -1e-6:
        return stmpqh(p, 0.0)
    return stmpth(p, t)
    

def stmphq(p:float, h:float) -> float:
    """Steam quality (vapour fraction) as a function of pressure and enthalpy

    Args:
        p (float): pressure [bara]
        h (float): enthalpy [kJ/kg]

    Returns:
        q (float): steam quality [kg/kg]
    """
    return steamTable.x_ph(p, h)


def stmpqv(p:float, q:float) -> float:
    """Steam specific volume as a function of pressure and quality (vapour fraction)

    Args:
        p (float): pressure [bara]
        q (float): steam quality [kg/kg]

    Returns:
        v (float): specific volume [m3/kg]
    """
    return (1 - q) * steamTable.vL_p(p) + q * steamTable.vV_p(p)


def stmtqv(t:float, q:float) -> float:
    """Steam specific volume as a function of temp and quality (vapour fraction)

    Args:
        t (float): temperature [°C]
        q (float): steam quality [kg/kg]

    Returns:
        v (float): specific volume [m3/kg]
    """
    return (1 - q) * steamTable.vL_t(t) + q * steamTable.vV_t(t)
    


