"""汇川 plc 标签通讯."""
# pylint: disable=W1203, disable=W0106, disable=E0401, disable=C0415
import logging
import os.path
from typing import Union

import clr

from inovance_tag.exception import PLCReadError, PLCWriteError


# noinspection PyUnresolvedReferences
class TagCommunication:
    """汇川plc标签通信class."""
    dll_path = f"{os.path.dirname(__file__)}/inovance_tag_dll/TagAccessCS.dll"

    def __init__(self, plc_ip):
        clr.AddReference(self.dll_path)
        from TagAccessCS import TagAccessClass
        self._tag_instance = TagAccessClass()
        self._plc_ip = plc_ip
        self._logger = logging.getLogger(f"{self.__module__}.{self.__class__.__name__}")
        self._handles = {}  # save handle

    @property
    def handles(self):
        """标签实例."""
        return self._handles

    @property
    def ip(self):
        """plc ip."""
        return self._plc_ip

    @property
    def logger(self):
        """日志实例."""
        return self._logger

    @property
    def tag_instance(self):
        """标签通讯实例对象."""
        return self._tag_instance

    def communication_open(self) -> bool:
        """ Connect to plc.

        Returns:
            bool: Is the PLC successfully connected.
        """
        connect_state = self.tag_instance.Connect2PlcDevice(self._plc_ip)
        if connect_state == self.tag_instance.TAResult.ERR_NOERROR:
            return True
        return False

    def execute_read(self, tag_name: str, data_type: str, save_log=True) -> Union[str, int, bool]:
        """ Read the value of the specified tag name.

        Args:
            tag_name: Tag name to be read.
            data_type: Type of data read.
            save_log: Do you want to save the log? Default save.

        Returns:
            Union[str, int, bool]: Return the read value.

        Raises:
            PLCReadError: An exception occurred during the reading process.
        """
        try:
            data_type = f"TC_{data_type.upper()}"
            if (handle := self.handles.get(tag_name)) is None:
                handle = self.tag_instance.CreateTagHandle(tag_name)[0]
                self.handles.update({tag_name: handle})
            save_log and self.logger.info(f"*** Start read {tag_name} value ***")
            result, state = self.tag_instance.ReadTag(handle, getattr(self.tag_instance.TagTypeClass, data_type))
            if data_type == "TC_STRING":
                result = result.strip()
            save_log and self.logger.info(f"*** End read {tag_name}'s value *** -> "
                                          f"value_type: {data_type}, value: {result}, read_state: {state.ToString()}")
            return result
        except Exception as exc:
            raise PLCReadError(f"Read failure: may be not connect plc {self.ip}") from exc

    def execute_write(self, tag_name: str, data_type: str, value: Union[int, bool, str], save_log=True):
        """ Write data of the specified type to the designated tag location.

        Args:
            tag_name: Tag name to be written with value.
            data_type: Write value's data type.
            value: Write value.
            save_log: Do you want to save the log? Default save.

        Returns:
            bool: Is the writing successful.

        Raises:
            PLCWriteError: An exception occurred during the writing process.
        """
        try:
            data_type = f"TC_{data_type.upper()}"
            if (handle := self.handles.get(tag_name)) is None:
                handle = self.tag_instance.CreateTagHandle(tag_name)[0]
                self.handles.update({tag_name: handle})
            save_log and self.logger.info(f"*** Start write {tag_name} value *** -> value_type: "
                                          f"{data_type}, value: {value}")
            result = self.tag_instance.WriteTag(handle, value, getattr(self.tag_instance.TagTypeClass, data_type))
            save_log and self.logger.info(f"*** End write {tag_name}'s value *** -> write_state: {result.ToString()}")
            if result == self.tag_instance.TAResult.ERR_NOERROR:
                return True
            return False
        except Exception as exc:
            raise PLCWriteError(f"*** Write failure: may be not connect plc {self.ip}") from exc

    @staticmethod
    def get_true_bit_with_num(number: int) -> list:
        """ Obtain the specific bits that are True based on an integer.

        Args:
            number (int): Number to be parsed.

        Returns:
            list: Index list with corresponding bit being True.
        """
        binary_str = bin(number)[2:]
        return [i for i, bit in enumerate(reversed(binary_str)) if bit == "1"]
