from ebike_config import EbikeConfig
import numpy as np


class EbikeDynamics(EbikeConfig):
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    
    def get_drag_force(self, velocity: np.ndarray) -> np.ndarray:
        rho = 1.2 #Rho ist die Luftdichte -> ca. 1,2 kg/m^3
        a: float = rho * self.cw_and_area / 2

        return (velocity ** 2) * a
    
    def get_incline_force(self, incline: np.ndarray) -> np.ndarray:
        g = 9.81 #Gravitationskonstante: 9,81 m / s^2
        total_mass = self.bike_mass + self.rider_mass

        return total_mass * g * np.sin(incline)

    def get_total_force(self, acceleration: np.ndarray, incline_force: np.ndarray, drag_force: np.ndarray):
        total_mass = self.bike_mass + self.rider_mass
        
        return total_mass * acceleration - (incline_force + drag_force)
    
    def get_power(self, force: np.ndarray, velocity: np.ndarray) -> np.ndarray:
        
        return np.multiply(force, velocity)
    
    def get_torque(self, force: np.ndarray) -> np.ndarray:

        return force * self.radius
    


    
    

