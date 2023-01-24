"""IKA TCP adapter for overhead stirrers and hotplates."""

import logging

from ika.util import TcpClient

logger = logging.getLogger('ika')


class OverheadStirrerProtocol():
    """Protocol for communicating with an overhead stirrer.

    Command syntax and format from the manual:
        - commands and parameters are transmitted as capital letters
        - commands and parameters including successive parameters are separated by at least
          one space (hex 0x20)
        - each individual command (including parameters and data and each response are terminated
          with Blank CR LF (hex 0x20 hex 0x0d hex 0x0A) and have a maximum length of 80 characters
        - the decimal separator in a number is a dt (hex 0x2E)
    """

    # overhead stirrer NAMUR commands
    READ_DEVICE_NAME = "IN_NAME"
    READ_PT1000 = "IN_PV_3"  # read PT1000 value - temperature from the temperature sensor
    READ_ACTUAL_SPEED = "IN_PV_4"  # current actual speed
    READ_ACTUAL_TORQUE = "IN_PV_5"  # current actual torque
    READ_SET_SPEED = "IN_SP_4"  # speed setpoint
    READ_TORQUE_LIMIT = "IN_SP_5"
    READ_SPEED_LIMIT = "IN_SP_6"
    READ_SAFETY_SPEED = "IN_SP_8"  # safety speed value
    SET_SPEED = "OUT_SP_4"  # set the speed setpoint
    SET_TORQUE_LIMIT = "OUT_SP_5"  # set the torque limit
    SET_SPEED_LIMIT = "OUT_SP_6"
    SET_SAFETY_SPEED = "OUT_SP_8"
    START_MOTOR = "START_4"  # start stirring
    STOP_MOTOR = "STOP_4"  # stop stirring
    SWITCH_TO_NORMAL_OPERATING_MODE = 'RESET'
    # todo change the direction or rotation with "OUT_MODE_n" (n = 1 or 2).
    # doesn't seem to work with the microstar C
    SET_ROTATION_DIRECTION = "OUT_MODE_"
    READ_ROTATION_DIRECTION = "IN_MODE"  # todo doesn't seem to work with the microstar C


class OverheadStirrer(TcpClient, OverheadStirrerProtocol):
    """Driver for IKA overhead stirrer."""

    def __init__(self, ip: str, port: int = 23):
        """Set up connection parameters, IP address and port."""
        self.units = None
        if ":" in ip:
            port = int(ip.split(":")[1])
            ip = ip.split(':')[0]
        super().__init__(ip, port)

    async def get(self):
        """Get overhead stirrer speed, torque, and external temperature reading."""
        speed = await self._write_and_read(self.READ_ACTUAL_SPEED)
        torque = await self._write_and_read(self.READ_ACTUAL_TORQUE)
        temp = await self._write_and_read(self.READ_PT1000)
        # FIXME handle case where temp probe is unplugged
        response = {
            'speed': speed,
            'torque': torque,
            'temp': temp,
        }
        return response

    async def get_info(self):
        """Get name and safety setpoints of overhead stirer."""
        name = await self._write_and_read(self.READ_DEVICE_NAME)
        torque_limit = await self._write_and_read(self.READ_TORQUE_LIMIT)
        speed_limit = await self._write_and_read(self.READ_SPEED_LIMIT)
        response = {
            'name': name,
            'torque_limit': torque_limit,
            'speed_limit': speed_limit,
        }
        return response


class HotplateProtocol():
    """Protocol for communicating with an overhead stirrer.

    Command syntax and format from the manual:
        - commands and parameters are transmitted as capital letters
        - commands and parameters including successive parameters are separated by at least
          one space (hex 0x20)
        - each individual command (including parameters and data and each response are terminated
          with Blank CR LF (hex 0x20 hex 0x0d hex 0x0A) and have a maximum length of 80 characters
        - the decimal separator in a number is a dt (hex 0x2E)
    """

    # hotplate NAMUR commands
    READ_DEVICE_NAME = "IN_NAME"
    READ_ACTUAL_PROCESS_TEMP = "IN_PV_1"
    READ_ACTUAL_SURFACE_TEMP = "IN_PV_2"
    READ_ACTUAL_SPEED = "IN_PV_4"
    READ_VISCOSITY_TREND_VALUE = "IN_PV_5"
    READ_RATED_TEMPERATURE_VALUE = "IN_SP_1"
    READ_TEMP_LIMIT = "IN_SP_3"  # find the set safe temperature of the plate, the target/set
    # temperature the plate can go to is 50 degrees beneath this
    READ_RATED_SPEED_VALUE = "IN_SP_4"
    SET_TEMPERATURE_VALUE = "OUT_SP_1 "  # requires a value to be appended to the end
    SET_SPEED_VALUE = "OUT_SP_4 "  # requires a value to be appended to the end
    START_THE_HEATER = "START_1"
    STOP_THE_HEATER = "STOP_1"
    START_THE_MOTOR = "START_4"
    STOP_THE_MOTOR = "STOP_4"
    SWITCH_TO_NORMAL_OPERATING_MODE = "RESET"
    SET_OPERATING_MODE_A = "SET_MODE_A"
    SET_OPERATING_MODE_B = "SET_MODE_B"
    SET_OPERATING_MODE_D = "SET_MODE_D"
    SET_WD_SAFETY_LIMIT_TEMPERATURE_WITH_SET_VALUE_ECHO = "OUT_SP_12@"
    # requires a value to be appended to the end of the command
    SET_WD_SAFETY_LIMIT_SPEED_WITH_SET_VALUE_ECHO = "OUT_SP_42@"
    # requires a value to be appended to the end of the command
    WATCHDOG_MODE_1 = "OUT_WD1@"  # requires a watchdog time (20-1500 s) to be appended to the end
    # This command launches the watchdog function and must be transmitted within the set time.
    # In watchdog mode 1, if event WD1 occurs, the heating and stirring functions are switched off
    #  and ER 2 is displayed
    WATCHDOG_MODE_2 = "OUT_WD2@"  # requires a watchdog time (20-1500 s) to be appended to the end
    # This command launches the watchdog function and must be transmitted within the set time.
    # In watchdog mode 2, if event WD2 occurs, the speed and temperature setpoint are set to their
    # watchdog setpoints.
    # the WD2 event can be reset with the command "OUT_WD2@0", which also stops the watchdog


class Hotplate(TcpClient, HotplateProtocol):
    """Driver for IKA hotplate stirrer."""

    def __init__(self, ip: str, port: int = 23):
        """Set up connection parameters, IP address and port."""
        self.units = None
        if ":" in ip:
            port = int(ip.split(":")[1])
            ip = ip.split(':')[0]
        super().__init__(ip, port)

    async def get(self):
        """Get hotplate speed, surface temperature, and process temperature readings."""
        speed = await self._write_and_read(self.READ_ACTUAL_SPEED)
        surface_temp = await self._write_and_read(self.READ_ACTUAL_SURFACE_TEMP)
        process_temp = await self._write_and_read(self.READ_ACTUAL_PROCESS_TEMP)
        # FIXME handle case where process temp probe is unplugged
        response = {
            'speed': speed,
            'surface_temp': surface_temp,
            'process_temp': process_temp,
        }
        return response

    async def get_info(self):
        """Get name and safety setpoint of hotplate."""
        name = await self._write_and_read(self.READ_DEVICE_NAME)
        temp_limit = await self._write_and_read(self.READ_RATED_SET_SAFETY_TEMPERATURE_VALUE)
        response = {
            'name': name,
            'temp_limit': temp_limit,
        }
        return response
