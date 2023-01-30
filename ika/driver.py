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
    READ_DEVICE_TYPE = "IN_TYPE"
    READ_ACTUAL_PROCESS_TEMP = "IN_PV_1"
    READ_ACTUAL_SURFACE_TEMP = "IN_PV_2"
    READ_ACTUAL_SPEED = "IN_PV_4"
    READ_VISCOSITY_TREND_VALUE = "IN_PV_5"
    READ_PROCESS_TEMP_SETPOINT = "IN_SP_1"
    READ_SURFACE_TEMP_SETPOINT = "IN_SP_2"
    READ_TEMP_LIMIT = "IN_SP_3"  # find the set safe temperature of the plate, the target/set
    # temperature the plate can go to is 50 degrees beneath this
    READ_SPEED_SETPOINT = "IN_SP_4"
    SET_PROCESS_TEMP_SETPOINT = "OUT_SP_1 "  # requires a value to be appended
    SET_SURFACE_TEMP_SETPOINT = "OUT_SP_2 "
    SET_SPEED_SETPOINT = "OUT_SP_4 "  # requires a value to be appended
    START_THE_HEATER = "START_1"
    STOP_THE_HEATER = "STOP_1"
    START_THE_MOTOR = "START_4"
    STOP_THE_MOTOR = "STOP_4"
    RESET = "RESET"
    SET_OPERATING_MODE_A = "SET_MODE_A"
    SET_OPERATING_MODE_B = "SET_MODE_B"
    SET_OPERATING_MODE_D = "SET_MODE_D"
    SET_WD_SAFETY_LIMIT_TEMPERATURE_WITH_SET_VALUE_ECHO = "OUT_SP_12@"
    # requires a value to be appended
    SET_WD_SAFETY_LIMIT_SPEED_WITH_SET_VALUE_ECHO = "OUT_SP_42@"
    # requires a value to be appended
    WATCHDOG_MODE_1 = "OUT_WD1@"  # requires a watchdog time (20-1500 s) to be appended to the end
    # This command launches the watchdog function and must be transmitted within the set time.
    # In watchdog mode 1, if event WD1 occurs, the heating and stirring functions are switched off
    #  and ER 2 is displayed
    WATCHDOG_MODE_2 = "OUT_WD2@"  # requires a watchdog time (20-1500 s) to be appended to the end
    # This command launches the watchdog function and must be transmitted within the set time.
    # In watchdog mode 2, if event WD2 occurs, the speed and temperature setpoint are set to their
    # watchdog setpoints.
    # the WD2 event can be reset with the command "OUT_WD2@0", which also stops the watchdog
    COMMUNICATE_WITH_EUROSTAR = "IN_PV_4"
    # If this response is received, the hotplate has been erroneously configured to attempt to
    # communicate with a Eurostar overhead stirrer over RS-232.


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
        speed_sp = await self._write_and_read(self.READ_SPEED_SETPOINT)
        surface_temp = await self._write_and_read(self.READ_ACTUAL_SURFACE_TEMP)
        surface_temp_sp = await self._write_and_read(self.READ_SURFACE_TEMP_SETPOINT)
        process_temp = await self._write_and_read(self.READ_ACTUAL_PROCESS_TEMP)
        process_temp_sp = await self._write_and_read(self.READ_PROCESS_TEMP_SETPOINT)
        # FIXME handle case where process temp probe is unplugged
        response = {
            'speed': {
                'setpoint': int(speed_sp),
                'actual': int(speed),
            },
            'surface_temp': {
                'setpoint': surface_temp_sp,
                'actual': surface_temp,
            },
            'process_temp': {
                'setpoint': process_temp_sp,
                'actual': process_temp,
            },
        }
        return response

    async def get_info(self):
        """Get name and safety setpoint of hotplate."""
        name = await self._write_and_read(self.READ_DEVICE_NAME)
        device_type = await self._write_and_read(self.READ_DEVICE_TYPE)
        temp_limit = await self._write_and_read(self.READ_TEMP_LIMIT)
        response = {
            'name': name,
            'device_type': device_type,
            'temp_limit': temp_limit,
        }
        return response

    async def control(self, equipment: str, on: bool):
        """Control the heater controlling process temperature, or shaker motor.

        Note: direct control of surface temperature is not implemented.
        """
        if equipment == 'heater':
            await self._write(self.START_THE_HEATER if on else self.STOP_THE_HEATER)
            # note - apparently after starting the heater it resets the setpoint to 0C
        elif equipment == 'motor':
            await self._write(self.START_THE_MOTOR if on else self.STOP_THE_MOTOR)
        else:
            raise ValueError(f'Equipment "{equipment} invalid. '
                             'Must be either "heater" or "motor"')

    async def set(self, equipment: str, setpoint: float):
        """Set a temperature or stirrer setpoint."""
        if equipment == 'process':
            await self._write(self.SET_PROCESS_TEMP_SETPOINT + str(setpoint))
        elif equipment == 'surface':
            await self._write(self.SET_SURFACE_TEMP_SETPOINT + str(setpoint))
        elif equipment == 'shaker':
            if setpoint < 50 or setpoint > 1700:
                raise ValueError(f"Cannot set shaker to {setpoint}RPM. "
                                 "Minimum shaker setpoint is 50RPM and maximum is 1700RPM.")
            # setpoints can be written as a decimal but the shaker will round off to int
            await self._write(self.SET_SPEED_SETPOINT + str(int(setpoint)))
        else:
            raise ValueError(f'Equipment "{equipment} invalid. '
                             'Must be "process", "surface", or "shaker"')

    async def reset(self):
        """Reset the hotplate, and turn off the heater and stirrer."""
        await self._write(self.RESET)
