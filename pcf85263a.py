"""
`pcf85263a` - PCF85263A Real Time Clock module
====================================================

This library supports the use of the PCF85263-based RTC in CircuitPython. It
contains a base RTC class used by all Adafruit RTC libraries. This base
class is inherited by the chip-specific subclasses.

Functions are included for:
    Reading and writing the time as a struct_time object
    Enabling the 3 timestamp registers
    Reading the timestamp registers as a struct_time object

Implementation Notes
--------------------

Hardware:
* Tested on an Adafruit ItsyBitsy M4 with the PCF85263 connected to its I2C bus.

Software and Dependencies:

* Adafruit CircuitPython firmware: https://github.com/adafruit/circuitpython/releases
* Adafruit's Register library: https://github.com/adafruit/Adafruit_CircuitPython_Register
  * NOTE: requires a version where the "include_weekday" parameter is implemented
* Adafruit's Bus Device library: https://github.com/adafruit/Adafruit_CircuitPython_BusDevice

Notes:

#. Milliseconds are not supported by this RTC.
#. Datasheet: https://www.nxp.com/docs/en/data-sheet/PCF85263A.pdf
#. 1/100 second mode is supported by this RTC, but not implemented in this driver

"""

__version__ = "0.0.1"
__repo__ = "https://github.com/g0tmk/CircuitPython_PCF85263A.git"

import time

from adafruit_bus_device.i2c_device import I2CDevice
from adafruit_register import i2c_bit
from adafruit_register import i2c_bits
from adafruit_register import i2c_bcd_alarm
from adafruit_register import i2c_bcd_datetime

try:
    import typing  # pylint: disable=unused-import
    from busio import I2C
except ImportError:
    pass


class PCF85263A:
    """Interface to the PCF85263A RTC.

    :param I2C i2c_bus: The I2C bus object
    """

    # TODO: add flag bits (alarms, timestamp flags, etc)

    # For the PCF85263, the "oscillator stopped" bit is in highest bit of register 1
    datetime_compromised = i2c_bit.RWBit(0x1, 7)
    """True if the clock integrity is compromised."""

    # 0x01: first time value is in register 0x1 (it stores seconds)
    # False: means that day comes before weekday in the registers
    # 0: means the first 'day of the week' is represented as 0 not 1
    datetime_register = i2c_bcd_datetime.BCDDateTimeRegister(0x01, False, 0)
    """Current date and time."""

    # 2: number of bits in the register
    # 0x23: register address
    # 0: lowest bit position in the register (so bits 1-0)
    timestamp1_control_mode = i2c_bits.RWBits(2, 0x23, 0)
    """Sets the mode for timestamp 1"""
    timestamp1_mode_no_timestamp = 0  # default
    timestamp1_mode_first_ts_pin_event = 1
    timestamp1_mode_last_ts_pin_event = 2

    # 3: number of bits in the register
    # 0x23: register address
    # 6: lowest bit position in the register (so bits 6-7)
    timestamp2_control_mode = i2c_bits.RWBits(3, 0x23, 2)
    """Sets the mode for timestamp 2"""
    timestamp2_mode_no_timestamp = 0  # default
    timestamp2_mode_first_switch_to_battery = 1
    timestamp2_mode_last_switch_to_battery = 2
    timestamp2_mode_last_switch_to_vdd = 3
    timestamp2_mode_first_ts_pin_event = 4
    timestamp2_mode_last_ts_pin_event = 5

    # 2: number of bits in the register
    # 0x23: register address
    # 6: lowest bit position in the register (so bits 6-7)
    timestamp3_control_mode = i2c_bits.RWBits(2, 0x23, 6)
    """Sets the mode for timestamp 3"""
    timestamp3_mode_no_timestamp = 0  # default
    timestamp3_mode_first_switch_to_battery = 1
    timestamp3_mode_last_switch_to_battery = 2
    timestamp3_mode_last_switch_to_vdd = 3


    # 0x11: first time value is in register 0x11 (it stores seconds)
    # False: means that day comes before weekday in the registers
    # 0: means the first 'day of the week' is represented as 0 not 1
    # include_weekday=False means the weekday field is skipped for these registers
    timestamp1_register = i2c_bcd_datetime.BCDDateTimeRegister(0x11, False, 0, include_weekday=False)
    """Current date and time."""


    # 0x17: first time value is in register 0x11 (it stores seconds)
    # False: means that day comes before weekday in the registers
    # 0: means the first 'day of the week' is represented as 0 not 1
    # include_weekday=False means the weekday field is skipped for these registers
    timestamp2_register = i2c_bcd_datetime.BCDDateTimeRegister(0x17, False, 0, include_weekday=False)
    """Current date and time."""

    # 0x1D: first time value is in register 0x11 (it stores seconds)
    # False: means that day comes before weekday in the registers
    # 0: means the first 'day of the week' is represented as 0 not 1
    # include_weekday=False means the weekday field is skipped for these registers
    timestamp3_register = i2c_bcd_datetime.BCDDateTimeRegister(0x1D, False, 0, include_weekday=False)
    """Current date and time."""

    # 0x08: First alarm register is reg 0x08
    # True: this RTC does support seconds for the alarm
    # True: means that day and weekday share a register
    # 0: first day of the week is value 0 and not 1.
    alarm = i2c_bcd_alarm.BCDAlarmTimeRegister(
        0x08, has_seconds=True, weekday_shared=True, weekday_start=0
    )
    """Alarm time for the alarm."""

    alarm_interrupt = i2c_bit.RWBit(0x01, 1)
    """True if the interrupt pin will output when alarm is alarming."""

    # flags
    periodic_interrupt_flag = i2c_bit.RWBit(0x2B, 7)
    alarm2_flag = i2c_bit.RWBit(0x2B, 6)
    alarm1_flag = i2c_bit.RWBit(0x2B, 5)
    watchdog_flag = i2c_bit.RWBit(0x2B, 4)
    battery_switch_flag = i2c_bit.RWBit(0x2B, 3)
    timestamp3_event_flag = i2c_bit.RWBit(0x2B, 2)
    timestamp2_event_flag = i2c_bit.RWBit(0x2B, 1)
    timestamp1_event_flag = i2c_bit.RWBit(0x2B, 0)
    
    # alarm compare bits - when set, the corresponding alarm is active
    alarm2_control_compare_weekdays = i2c_bit.RWBit(0x10, 7)
    alarm2_control_compare_hours = i2c_bit.RWBit(0x10, 6)
    alarm2_control_compare_minutes = i2c_bit.RWBit(0x10, 5)
    alarm1_control_compare_months = i2c_bit.RWBit(0x10, 4)
    alarm1_control_compare_days = i2c_bit.RWBit(0x10, 3)
    alarm1_control_compare_hours = i2c_bit.RWBit(0x10, 2)
    alarm1_control_compare_minutes = i2c_bit.RWBit(0x10, 1)
    alarm1_control_compare_seconds = i2c_bit.RWBit(0x10, 0)

    # 2: number of bits in the register
    # 0x25: register address
    # 0: lowest bit position in the register
    oscillator_capacitance = i2c_bits.RWBits(2, 0x25, 0)
    """Sets the oscillator's capacitance value"""
    oscillator_capacitance_7pf = 0  # default
    oscillator_capacitance_6pf = 1
    oscillator_capacitance_12_5pf = 2

    # 6: number of bits in the register
    # 0x24: register address
    # 0: lowest bit position in the register
    offset_register = i2c_bits.RWBits(8, 0x24, 0)
    """Sets the offset register for calibration. Signed number representing 2.170 ppm/step"""

    def __init__(self, i2c_bus: I2C) -> None:
        time.sleep(0.05)
        self.i2c_device = I2CDevice(i2c_bus, 0x51)

        # Try and verify this is the RTC we expect by checking the timer B
        # frequency control bits which are 1 on reset and shouldn't ever be
        # changed.
        buf = bytearray(2)
        buf[0] = 0x12
        with self.i2c_device as i2c:
            i2c.write_then_readinto(buf, buf, out_end=1, in_start=1)

    @property
    def datetime(self) -> time.struct_time:
        """Gets the current date and time or sets the current date and time then starts the
        clock."""
        return self.datetime_register

    @datetime.setter
    def datetime(self, value: time.struct_time) -> None:
        # Automatically sets lost_power to false.
        self.datetime_register = value
        self.datetime_compromised = False
