import numpy as np

def get_deduct_value(crack_type: str, density: float, severity: str = 'Medium') -> float:
    """
    Returns the deduct value for a given crack type and density.
    
    Parameters:
    - crack_type (str): One of the supported crack types
    - density (float): Distress density as a percentage (0-100)
    - severity (str): Severity level ('Low', 'Medium', 'High')
    
    Returns:
    - float: Deduct value (0-100)
    """
    
    # Define logistic curve parameters for each crack type and severity
    crack_curves = {
        'Rutting': {
            'Low':    {'Dmax': 40, 'k': 0.15, 'x0': 35},
            'Medium': {'Dmax': 60, 'k': 0.20, 'x0': 30},
            'High':   {'Dmax': 80, 'k': 0.25, 'x0': 25}
        },
        'Reflective & Transverse Crack': {
            'Low':    {'Dmax': 35, 'k': 0.14, 'x0': 40},
            'Medium': {'Dmax': 55, 'k': 0.18, 'x0': 35},
            'High':   {'Dmax': 75, 'k': 0.22, 'x0': 30}
        },
        'Block Crack': {
            'Low':    {'Dmax': 45, 'k': 0.16, 'x0': 30},
            'Medium': {'Dmax': 65, 'k': 0.20, 'x0': 25},
            'High':   {'Dmax': 85, 'k': 0.24, 'x0': 20}
        },
        'Longitudinal Crack': {
            'Low':    {'Dmax': 35, 'k': 0.15, 'x0': 35},
            'Medium': {'Dmax': 55, 'k': 0.18, 'x0': 30},
            'High':   {'Dmax': 75, 'k': 0.22, 'x0': 25}
        },
        'Alligator Crack': {
            'Low':    {'Dmax': 45, 'k': 0.15, 'x0': 30},
            'Medium': {'Dmax': 65, 'k': 0.20, 'x0': 25},
            'High':   {'Dmax': 85, 'k': 0.25, 'x0': 20}
        },
        'Patching': {
            'Low':    {'Dmax': 30, 'k': 0.12, 'x0': 40},
            'Medium': {'Dmax': 50, 'k': 0.16, 'x0': 35},
            'High':   {'Dmax': 70, 'k': 0.20, 'x0': 30}
        },
        'Potholes': {
            'Low':    {'Dmax': 50, 'k': 0.20, 'x0': 25},
            'Medium': {'Dmax': 70, 'k': 0.25, 'x0': 20},
            'High':   {'Dmax': 90, 'k': 0.30, 'x0': 15}
        },
        'Bleeding': {
            'Low':    {'Dmax': 25, 'k': 0.10, 'x0': 45},
            'Medium': {'Dmax': 45, 'k': 0.14, 'x0': 40},
            'High':   {'Dmax': 65, 'k': 0.18, 'x0': 35}
        },
        'Corrugation': {
            'Low':    {'Dmax': 35, 'k': 0.13, 'x0': 40},
            'Medium': {'Dmax': 55, 'k': 0.17, 'x0': 35},
            'High':   {'Dmax': 75, 'k': 0.21, 'x0': 30}
        },
        'Raveling & Weathering': {
            'Low':    {'Dmax': 30, 'k': 0.11, 'x0': 45},
            'Medium': {'Dmax': 50, 'k': 0.15, 'x0': 40},
            'High':   {'Dmax': 70, 'k': 0.19, 'x0': 35}
        },
        'Bumps & Sags': {
            'Low':    {'Dmax': 40, 'k': 0.14, 'x0': 35},
            'Medium': {'Dmax': 60, 'k': 0.18, 'x0': 30},
            'High':   {'Dmax': 80, 'k': 0.22, 'x0': 25}
        },
    }
    
    if crack_type not in crack_curves:
        available_types = list(crack_curves.keys())
        raise ValueError(f"Unsupported crack type: {crack_type}. Available types: {available_types}")
    
    if severity not in crack_curves[crack_type]:
        available_severities = list(crack_curves[crack_type].keys())
        raise ValueError(f"Unsupported severity: {severity}. Available severities: {available_severities}")
    
    # Cap density between 0 and 100
    density = max(0, min(100, density))
    
    # Get parameters for the specific crack type and severity
    params = crack_curves[crack_type][severity]
    Dmax, k, x0 = params['Dmax'], params['k'], params['x0']
    
    # Logistic function
    deduct_value = Dmax / (1 + np.exp(-k * (density - x0)))
    return round(deduct_value, 2)