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
    SET_DEVICE_NAME = "OUT_NAME "  # set name, undocumented
    READ_PT1000 = "IN_PV_3"  # read PT1000 value - temperature from the temperature sensor
    READ_ACTUAL_SPEED = "IN_PV_4"  # current actual speed
    READ_ACTUAL_TORQUE = "IN_PV_5"  # current actual torque
    READ_SET_SPEED = "IN_SP_4"  # speed setpoint
    READ_TORQUE_LIMIT = "IN_SP_5"
    READ_SPEED_LIMIT = "IN_SP_6"
    READ_SAFETY_SPEED = "IN_SP_8"  # safety speed value
    SET_SPEED = "OUT_SP_4 "  # set the speed setpoint
    SET_TORQUE_LIMIT = "OUT_SP_5 "  # set the torque limit
    SET_SPEED_LIMIT = "OUT_SP_6 "
    SET_SAFETY_SPEED = "OUT_SP_8 "
    START_MOTOR = "START_4"  # start stirring
    STOP_MOTOR = "STOP_4"  # stop stirring
    READ_MOTOR_STATUS = "STATUS_4"  # running status, undocumented in manual
    RESET = 'RESET'
    # todo change the direction or rotation with "OUT_MODE_n" (n = 1 or 2).
    # doesn't seem to work with the microstar C
    SET_ROTATION_CLOCKWISE = "OUT_MODE_1"
    SET_ROTATION_CLOCKWISE = "OUT_MODE_2"  # Fixme: verify
    READ_ROTATION_DIRECTION = "IN_MODE"  # todo doesn't seem to work with the microstar C


class OverheadStirrer(TcpClient, OverheadStirrerProtocol):
    """Driver for IKA overhead stirrer."""

    async def get(self):
        """Get overhead stirrer speed, torque, and external temperature reading."""
        speed = await self._write_and_read(self.READ_ACTUAL_SPEED)
        speed_sp = await self._write_and_read(self.READ_SET_SPEED)
        motor_status = await self._write_and_read(self.READ_MOTOR_STATUS)
        torque = await self._write_and_read(self.READ_ACTUAL_TORQUE)
        temp = await self._write_and_read(self.READ_PT1000)
        # FIXME handle case where temp probe is unplugged
        response = {
            'speed': {
                'setpoint': speed_sp,
                'actual': speed,
                'active': motor_status,
            },
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

    async def set(self, equipment='speed', setpoint=0):
        """Set a parameter to the specified value."""
        if equipment == 'speed':
            await self._write(self.SET_SPEED + str(setpoint))
        elif equipment == 'speed_limit':
            await self._write(self.SET_SPEED_LIMIT + str(setpoint))
        elif equipment == 'torque_limit':
            await self._write(self.SET_TORQUE_LIMIT + str(setpoint))
        else:
            raise ValueError("Call with 'speed', 'speed_limit', or 'torque_limit'")

    async def control(self, on: bool):
        """Control the overhead stirrer motor."""
        await self._write(self.START_MOTOR if on else self.STOP_MOTOR)

    async def reset(self):
        """Reset the overhead stirrer."""
        await self._write(self.RESET)


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
    READ_PROCESS_HEATER_STATUS = "STATUS_1"  # undocumented in manual
    READ_SURFACE_HEATER_STATUS = "STATUS_2"  # undocumented in manual
    READ_SHAKER_STATUS = "STATUS_4"  # undocumented in manual
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

    def __init__(self, address, include_surface_control=False):
        """Set up connection parameters, IP address and port."""
        super().__init__(address)
        self.include_surface_control = include_surface_control

    async def get(self, include_surface_control=False):
        """Get hotplate speed, surface temperature, and process temperature readings."""
        speed = await self._write_and_read(self.READ_ACTUAL_SPEED)
        speed_sp = await self._write_and_read(self.READ_SPEED_SETPOINT)
        process_temp = await self._write_and_read(self.READ_ACTUAL_PROCESS_TEMP)
        process_temp_sp = await self._write_and_read(self.READ_PROCESS_TEMP_SETPOINT)
        shaker_status = await self._write_and_read(self.READ_SHAKER_STATUS)
        process_heater_status = await self._write_and_read(self.READ_PROCESS_HEATER_STATUS)
        surface_data = {
            'actual': await self._write_and_read(self.READ_ACTUAL_SURFACE_TEMP)
        }
        if self.include_surface_control:
            surface_data['setpoint'] = await self._write_and_read(self.READ_SURFACE_TEMP_SETPOINT)
            # surface_data['active'] = await self._write_and_read(self.READ_SURFACE_HEATER_STATUS)
            # FIXME figure out response value of '-90 02'
        # FIXME handle case where process temp probe is unplugged
        response = {
            'speed': {
                'setpoint': int(speed_sp) if type(speed_sp) is float else speed_sp,
                'actual': int(speed) if type(speed) is float else speed,
                'active': shaker_status,
            },
            'process_temp': {
                'setpoint': process_temp_sp,
                'actual': process_temp,
                'active': process_heater_status,
            },
            'surface_temp': surface_data,
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


class ShakerProtocol:
    """Protocol for communicating with an orbital shaker.

    Command syntax and format from the manual:
        - commands and parameters are transmitted as capital letters
        - commands and parameters including successive parameters are separated by at least
          one space (hex 0x20)
        - each individual command (including parameters and data and each response are terminated
          with Blank CR LF (hex 0x20 hex 0x0d hex 0x0A) and have a maximum length of 80 characters
        - the decimal separator in a number is a dt (hex 0x2E)
    """

    ...


class Shaker(TcpClient, ShakerProtocol):
    """Driver for IKA orbital shaker."""


class VacuumProtocol:
    """Protocol for communicating with a vacuum pump.

    Command syntax and format from the manual:
        - commands and parameters are transmitted as capital letters
        - commands and parameters including successive parameters are separated by at least
          one space (hex 0x20)
        - each individual command (including parameters and data and each response are terminated
          with Blank CR LF (hex 0x20 hex 0x0d hex 0x0A) and have a maximum length of 80 characters
        - the decimal separator in a number is a dt (hex 0x2E)
    """

    # vacuum pump NAMUR commands
    # Return the actual values: 'IN_PARA1'
    # Set the set values for the pump control: 'OUT_PARA1'
    # Set the set values for Bluetooth connection: 'OUT_PARA2'
    # Send the actual device status: 'OUT_STATUS'
    # Reads the status of a device: 'IN_STATUS'
    # Read the version of the firmware: 'IN_VERSION'
    # Read the release date of the display/ logic firmware: 'IN_DATE'
    READ_DEVICE_NAME = 'IN_NAME'
    # Read the device type.: 'IN_DEVICE'
    # Read mac address of Wico.: 'IN_ADDRESS'
    # Read paired mac address of station.: 'IN_PARING' (sic)
    # Write new paired mac addresses of both station and Wico: 'OUT_ADDRESS'
    # Reads the set pressure value: 'IN_SP_66'
    # Sets set point pressure value: 'OUT_SP_66'
    # Reads the actual pressure value: 'IN_PV_66'
    # Reads the evacuating mode: 'IN_MODE_66'
    # Sets the evacuating mode: 'OUT_MODE_66'
    # Reads error state: 'IN_ERROR'
    # Test Error. Sends out error code: 'OUT_ERROR'
    # Reads Bluetooth Device Name: 'IN_BT_NAME'
    # Reads custom device name: 'IN_CUSTOM_DEVICE_NAME'
    # Reads communication watchdog time: 'OUT_CUSTOM_DEVICE_NAME'
    # Sets communication watchdog time: 'IN_WD1@'
    # Set PC communication watchdog time 2: 'OUT_WD1@'
    # Set the PC safety pump rate: 'OUT_WD2@'
    # Set the PC safety pressure: 'OUT_SP_41'
    RESET = 'RESET'
    # Starts the measurement: 'START_66'
    # Stops the measurement: 'STOP_66'
    # Starts IAP mode: 'ENTER_IAP'
    # It is used to calibrate vacuum: 'CALIB_66'
    # It is used to read vacuum calibration values: 'IN_CALIB_66'
    # It is used to calibrate vacuum: 'OUT_CALIB_66'

    ERROR_CODES = {
        3: ("The device temperature has exceeeded its limit."
            "Have you tried turning it off and on again?"),
        4: "The motor has overloaded.  Have you tried turning it off and on again?",
        8: "The speed sensor has faulted.  Contact service.",
        9: "The internal flash has a read or write error.  Contact service."
    }


class Vacuum(TcpClient, VacuumProtocol):
    """Driver for IKA vacuum pump."""
