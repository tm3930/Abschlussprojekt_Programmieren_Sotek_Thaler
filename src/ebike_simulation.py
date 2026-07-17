import logging

from battery import Battery
from motor import Motor
from ebike_dynamics import EbikeDynamics
from gps_data import GPSData
from plotting_utils import plot_speed_power_soc
from data_from_csv import get_data_from_csv

logger = logging.getLogger(__name__)


class EBikeSimulation:
    """Klasse zur Durchführung, Auswertung und zum Export der gesamten E-Bike Simulation."""

    def __init__(self, battery: Battery, motor: Motor, ebike_dynamics: EbikeDynamics, gps_data: GPSData) -> None:
        self.battery = battery
        self.motor = motor
        self.ebike_dynamics = ebike_dynamics
        self.gps_data = gps_data

    def run(self) -> None:
        
        data = get_data_from_csv("final_project_input_data.csv")
        gps = self.gps_data(data)

        distance = gps.get_distance()
        velocity = gps.get_velocity(distance)
        acceleration = gps.get_acceleration(velocity)
        incline = gps.get_incline(distance)


        drag_force = self.ebike_dynamics.get_drag_force(velocity)
        incline_force = self.ebike_dynamics.get_incline_force(incline)
        forward_force = self.ebike_dynamics.get_total_force(acceleration, incline_force, drag_force)
        power = self.ebike_dynamics.get_power(forward_force, velocity)

        plot_speed_power_soc(data)



