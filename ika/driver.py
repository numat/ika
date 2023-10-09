"""IKA TCP adapter for overhead stirrers and hotplates."""

import asyncio
import logging
from abc import ABC
from enum import Enum
from typing import Any, Dict

from ika.util import Client, SerialClient, TcpClient

logger = logging.getLogger('ika')


class IKADevice(ABC):
    """Abstract base class for IKA devices."""

    def __init__(self, address, **kwargs):
        """Set up connection parameters, serial or IP address and port."""
        if address.startswith('/dev') or address.startswith('COM'):  # serial
            self.hw: Client = SerialClient(address=address, **kwargs)
        else:
            self.hw = TcpClient(address=address, **kwargs)
        self.lock = None  # needs to be initialized later, when the event loop exists

    async def __aenter__(self, *args):
        """Provide async enter to context manager."""
        return self

    async def __aexit__(self, *args):
        """Provide async exit to context manager."""
        return

    async def query(self, query) -> str:
        """Query the device and return its response."""
        if not self.lock:
            self.lock = asyncio.Lock()
        async with self.lock:  # lock releases on CancelledError
            return await self.hw._write_and_read(query)

    async def command(self, command) -> None:
        """Send a command to the device and don't expect a response."""
        if not self.lock:
            self.lock = asyncio.Lock()
        async with self.lock:  # lock releases on CancelledError
            await self.hw._write(command)

    async def reset(self) -> None:
        """Reset the device."""
        await self.command('RESET')


class OverheadStirrerProtocol:
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


class OverheadStirrer(OverheadStirrerProtocol, IKADevice):
    """Driver for IKA overhead stirrer."""

    async def get(self):
        """Get overhead stirrer speed, torque, and external temperature reading."""
        speed = await self.query(self.READ_ACTUAL_SPEED)
        speed_sp = await self.query(self.READ_SET_SPEED)
        motor_status = await self.query(self.READ_MOTOR_STATUS)
        torque = await self.query(self.READ_ACTUAL_TORQUE)
        temp = await self.query(self.READ_PT1000)
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
        name = await self.query(self.READ_DEVICE_NAME)
        torque_limit = await self.query(self.READ_TORQUE_LIMIT)
        speed_limit = await self.query(self.READ_SPEED_LIMIT)
        response = {
            'name': name,
            'torque_limit': torque_limit,
            'speed_limit': speed_limit,
        }
        return response

    async def set(self, equipment='speed', setpoint=0):
        """Set a parameter to the specified value."""
        if equipment == 'speed':
            await self.command(self.SET_SPEED + str(setpoint))
        elif equipment == 'speed_limit':
            await self.command(self.SET_SPEED_LIMIT + str(setpoint))
        elif equipment == 'torque_limit':
            await self.command(self.SET_TORQUE_LIMIT + str(setpoint))
        else:
            raise ValueError("Call with 'speed', 'speed_limit', or 'torque_limit'")

    async def control(self, on: bool):
        """Control the overhead stirrer motor."""
        await self.query(self.START_MOTOR if on else self.STOP_MOTOR)


class HotplateProtocol:
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
    READ_ACTUAL_FLUID_TEMP = "IN_PV_7"  # for double temp probe "PT1000"
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


class Hotplate(HotplateProtocol, IKADevice):
    """Driver for IKA hotplate stirrer."""

    def __init__(self, address, include_surface_control=False):
        """Set up connection parameters, IP address and port."""
        super().__init__(address)
        self.include_surface_control = include_surface_control

    async def get(self, include_surface_control=False):
        """Get hotplate speed, surface temperature, and process temperature readings."""
        speed = await self.query(self.READ_ACTUAL_SPEED)
        speed_sp = await self.query(self.READ_SPEED_SETPOINT)
        process_temp = await self.query(self.READ_ACTUAL_PROCESS_TEMP)
        process_temp_sp = await self.query(self.READ_PROCESS_TEMP_SETPOINT)
        fluid_temp = await self.query(self.READ_ACTUAL_FLUID_TEMP)
        shaker_status = await self.query(self.READ_SHAKER_STATUS)
        process_heater_status = await self.query(self.READ_PROCESS_HEATER_STATUS)
        surface_data = {
            'actual': await self.query(self.READ_ACTUAL_SURFACE_TEMP)
        }
        if self.include_surface_control:
            surface_data['setpoint'] = await self.query(self.READ_SURFACE_TEMP_SETPOINT)
            # surface_data['active'] = await self.query(self.READ_SURFACE_HEATER_STATUS)
            # FIXME figure out response value of '-90 02'
        # FIXME handle case where process temp probe is unplugged
        response = {
            'speed': {
                'setpoint': int(speed_sp) if isinstance(speed_sp, float) else speed_sp,
                'actual': int(speed) if isinstance(speed, float) else speed,
                'active': shaker_status,
            },
            'process_temp': {
                'setpoint': process_temp_sp,
                'actual': process_temp,
                'active': process_heater_status,
            },
            'surface_temp': surface_data,
            'fluid_temp': {
                'actual': fluid_temp,
            }
        }
        return response

    async def get_info(self):
        """Get name and safety setpoint of hotplate."""
        name = await self.query(self.READ_DEVICE_NAME)
        device_type = await self.query(self.READ_DEVICE_TYPE)
        temp_limit = await self.query(self.READ_TEMP_LIMIT)
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
            await self.command(self.START_THE_HEATER if on else self.STOP_THE_HEATER)
            # note - apparently after starting the heater it resets the setpoint to 0C
        elif equipment == 'motor':
            await self.command(self.START_THE_MOTOR if on else self.STOP_THE_MOTOR)
        else:
            raise ValueError(f'Equipment "{equipment} invalid. '
                             'Must be either "heater" or "motor"')

    async def set(self, equipment: str, setpoint: float):
        """Set a temperature or stirrer setpoint."""
        if equipment == 'process':
            await self.command(self.SET_PROCESS_TEMP_SETPOINT + str(setpoint))
        elif equipment == 'surface':
            await self.command(self.SET_SURFACE_TEMP_SETPOINT + str(setpoint))
        elif equipment == 'shaker':
            if setpoint < 50 or setpoint > 1700:
                raise ValueError(f"Cannot set shaker to {setpoint}RPM. "
                                 "Minimum shaker setpoint is 50RPM and maximum is 1700RPM.")
            # setpoints can be written as a decimal but the shaker will round off to int
            await self.command(self.SET_SPEED_SETPOINT + str(int(setpoint)))
        else:
            raise ValueError(f'Equipment "{equipment} invalid. '
                             'Must be "process", "surface", or "shaker"')

    async def reset(self):
        """Reset the hotplate, and turn off the heater and stirrer."""
        await self.command(self.RESET)


class ShakerProtocol:
    """Protocol for communicating with an orbital shaker.

    RS-232 Information
        - Transmission procedure: asynchronous character transmission in start-stop mode
        - Type of transmission: full duplex
        - 1 start bit; 7 character bits; 1 parity bit (even); 1 stop bit
        - Transmission speed: 9600 bit/s

    Command syntax and format from the manual:
        - commands and parameters are transmitted as capital letters
        - commands and parameters including successive parameters are separated by at least
          one space (hex 0x20)
        - each individual command (including parameters and data and each response are terminated
          with CR LF (hex 0x0d hex 0x0A) and have a maximum length of 80 characters
        - the decimal separator in a number is a dt (hex 0x2E)
    """

    # orbital shaker NAMUR commands
    READ_DEVICE_NAME = "IN_NAME"
    READ_ACTUAL_TEMPERATURE = "IN_PV_2"
    READ_ACTUAL_SPEED = "IN_PV_4"
    READ_SET_TEMPERATURE = "IN_SP_2"
    READ_SET_SPEED = "IN_SP_4"
    SET_TEMP = "OUT_SP_2 "
    SET_SPEED = "OUT_SP_4 "
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
    START_HEATER = "START_2"
    STOP_HEATER = "STOP_2"
    START_MOTOR = "START_4"
    STOP_MOTOR = "STOP_4"
    READ_HEATER_STATUS = "STATUS_2"  # Does not exist - find this
    READ_MOTOR_STATUS = "STATUS 4"  # Does not exist - find this
    READ_SOFTWARE_VERSION = "IN_VERSION"
    READ_SOFTWARE_ID = "IN_SOFTWARE_ID"  # Read software ID and version
    SET_ROTATION_CCW = "OUT_MODE_1"  # Sets rotation to CCW (OUT_MODE_2 does not set to CW)
    # Will not work if the last command sent to the shaker was RESET for some reason??
    RESET = "RESET"  # This will set rotation back to CW after being set to CCW


class Shaker(ShakerProtocol, IKADevice):
    """Driver for IKA orbital shaker."""

    def __init__(self, address, **kwargs):
        """Set up connection parameters, serial or IP address and port."""
        if address.startswith('/dev') or address.startswith('COM'):  # serial
            self.hw: Client = SerialClient(address=address, **kwargs)
        else:
            self.hw = TcpClient(address=address, **kwargs)
        self.lock = None  # needs to be initialized later, when the event loop exists

    async def get(self):
        """Get orbital shaker speed."""
        temp = await self.query(self.READ_ACTUAL_TEMPERATURE)
        temp_sp = await self.query(self.READ_SET_TEMPERATURE)
        heater_status = await self.query(self.READ_HEATER_STATUS)
        speed = await self.query(self.READ_ACTUAL_SPEED)
        speed_sp = await self.query(self.READ_SET_SPEED)
        shaker_status = await self.query(self.READ_MOTOR_STATUS)
        response = {
            'temp': {
                'setpoint': temp_sp,
                'actual': temp,
                'active': heater_status,
            },
            'speed': {
                'setpoint': int(speed_sp) if isinstance(speed_sp, float) else speed_sp,
                'actual': int(speed) if isinstance(speed, float) else speed,
                'active': shaker_status,
            }
        }
        return response

    async def get_info(self):
        """Get name and software version of orbital shaker."""
        name = await self.query(self.READ_DEVICE_NAME)
        version = await self.query(self.READ_SOFTWARE_VERSION)
        software_id = await self.query(self.READ_SOFTWARE_ID)
        response = {
            'name': name,
            'version': version,
            'software_ID': software_id,
        }
        return response

    async def set(self, equipment: str, setpoint: float):
        """Set a temperature or shaker speed setpoint."""
        if equipment == 'heater':
            if setpoint < 1.0 or setpoint > 100:
                raise ValueError('Setpoint invalid. Temperature SP must be between 1C and 100C.')
            await self.command(self.SET_TEMP + str(setpoint))
        elif equipment == 'shaker':
            if setpoint < 300 or setpoint > 3000:
                raise ValueError('Setpoint invalid. Speed SP must be between 300 and 3000rpm.')
            await self.command(self.SET_SPEED + str(setpoint))
        else:
            raise ValueError(f'Equipment "{equipment} invalid. '
                             'Must be either "heater" or "shaker"')

    async def control(self, equipment: str, on: bool):
        """Control the heater controlling process temperature, or shaker motor."""
        if equipment == 'heater':
            await self.command(self.START_HEATER if on else self.STOP_HEATER)
        elif equipment == 'shaker':
            await self.command(self.START_MOTOR if on else self.STOP_MOTOR)
        else:
            raise ValueError(f'Equipment "{equipment} invalid. '
                             'Must be either "heater" or "shaker"')

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
    READ_PARAMETERS = "IN_PARA1"
    SET_PARAMATERS_PUMP = "OUT_PARA1 "  # requires a value to be appended
    SET_PARAMETERS_BLUETOOTH = "OUT_PARA2 "  # requires a value to be appended
    READ_VAC_STATUS = "IN_STATUS"
    # Send the actual device status: 'OUT_STATUS'
    READ_SOFTWARE_VERSION = "IN_VERSION"
    # Read the release date of the display/ logic firmware: 'IN_DATE'
    READ_DEVICE_NAME = "IN_NAME"
    SET_DEVICE_NAME = "OUT_NAME "  # manual incorrectly refers to CUSTOM_DEVICE_NAME
    # Read the device type.: 'IN_DEVICE'
    # Read mac address of Wico.: 'IN_ADDRESS'
    # Read paired mac address of station.: 'IN_PARING' (sic)
    # Write new paired mac addresses of both station and Wico: 'OUT_ADDRESS'
    READ_SET_PRESSURE = "IN_SP_66"
    SET_PRESSURE = "OUT_SP_66 "  # requires a value to be appended
    READ_ACTUAL_PRESSURE = "IN_PV_66"
    READ_VAC_MODE = "IN_MODE_66"
    SET_VAC_MODE = "OUT_MODE_66 "  # requires a value to be appended
    # Reads error state: 'IN_ERROR'
    # Test Error. Sends out error code: 'OUT_ERROR'
    # Reads Bluetooth Device Name: 'IN_BT_NAME'
    # Reads custom device name: 'IN_CUSTOM_DEVICE_NAME'
    # Reads communication watchdog time: 'OUT_CUSTOM_DEVICE_NAME'
    # Sets communication watchdog time: 'IN_WD1@'
    # Set PC communication watchdog time 2: 'OUT_WD1@'
    # Set the PC safety pump rate: 'OUT_WD2@'
    # Set the PC safety pressure: 'OUT_SP_41'
    RESET = "RESET"
    START_MEASUREMENT = "START_66"
    STOP_MEASUREMENT = "STOP_66"
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

    class Mode(Enum):
        """Possible operating modes."""

        AUTOMATIC = '0'  # Automatic boiling point recognition
        MANUAL = '1'  # Pressure control
        PERCENT = '2'  # % pump speed
        PROGRAM = '3'  # User-defined program


class Vacuum(VacuumProtocol, IKADevice):
    """Driver for IKA vacuum pump."""

    def __init__(self, address, **kwargs):
        """Set up connection parameters, serial or IP address and port."""
        if address.startswith('/dev') or address.startswith('COM'):  # serial
            self.hw: Client = SerialClient(address=address, **kwargs)
        else:
            self.hw = TcpClient(address=address, **kwargs)
        self.lock = None  # needs to be initialized later, when the event loop exists

    async def get_pressure(self) -> float:
        """Get vacuum pressure, converting to mmHg."""
        raw_pressure = await self.query(self.READ_ACTUAL_PRESSURE)
        return round(float(raw_pressure) / 1.333, 2)

    async def get_pressure_setpoint(self) -> float:
        """Get vacuum pressure setpoint, converting to mmHg."""
        raw_sp = await self.query(self.READ_SET_PRESSURE)
        return round(float(raw_sp) / 1.333, 2)

    async def get_status(self) -> bool:
        """Get vacuum status and convert to running/not running bool.

        TODO: Figure out the actual status bit (bit 25?)
        """
        raw_status = await self.query(self.READ_VAC_STATUS)
        return not (raw_status == '75' or raw_status == '79'
                    or raw_status == '203' or raw_status == '207'
                    or raw_status[0:2] == '32')

    async def get_vac_mode(self) -> str:
        """Get vacuum mode."""
        raw_mode = await self.query(self.READ_VAC_MODE)
        return raw_mode

    async def get(self) -> Dict[str, Any]:
        """Get pump operating data."""
        pressure = await self.get_pressure()
        pressure_sp = await self.get_pressure_setpoint()
        vac_mode = await self.get_vac_mode()
        vac_status = await self.get_status()

        response = {
            'active': vac_status,
            'mode': VacuumProtocol.Mode(vac_mode).name,
            'pressure': {
                'setpoint': pressure_sp,
                'actual': pressure,
            }
        }
        return response

    async def get_info(self) -> Dict[str, str]:
        """Get name and software version of vacuum."""
        name = await self.query(self.READ_DEVICE_NAME)
        version = await self.query(self.READ_SOFTWARE_VERSION)
        response = {
            'name': name,
            'version': version,
        }
        return response

    async def set(self, setpoint: float):
        """Set a vacuum pressure setpoint, converting from mmHg to mbar.

        Unlike other commands, the vacuum echoes back, so use query().
        """
        setpoint_mbar = str(int(setpoint * 1.333))
        await self.query(self.SET_PRESSURE + setpoint_mbar)

    async def set_mode(self, mode: VacuumProtocol.Mode):
        """Set the operating mode.

        Unlike other commands, the vacuum echoes back, so use query().
        """
        await self.query(self.SET_VAC_MODE + str(mode.value))

    async def set_name(self, name: str):
        """Set a custom device name.

        Unlike other commands, the vacuum echoes back, so use query().
        """
        await self.query(self.SET_DEVICE_NAME + name)

    async def control(self, on: bool):
        """Control the vacuum running status.

        Unlike other commands, the vacuum echoes back, so use query().
        """
        await self.query(self.START_MEASUREMENT if on else self.STOP_MEASUREMENT)
