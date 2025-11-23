"""汇川 plc 标签通讯."""
# pylint: skip-file
import logging
import os.path
import pathlib
from typing import Union
from logging.handlers import TimedRotatingFileHandler

import clr

from inovance_tag.exception import PLCReadError, PLCWriteError


class TagCommunication:
    """汇川plc标签通信class."""
    dll_path = f"{os.path.dirname(__file__)}/inovance_tag_dll/TagAccessCS.dll"
    LOG_FORMAT = "%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s"

    def __init__(self, plc_ip: str, plc_name: str = "", save_log: bool = False):
        """标签通讯构造方法.

        Args:
            plc_ip: plc ip address.
            plc_name: plc name.
        """
        logging.basicConfig(level=logging.INFO, encoding="UTF-8", format=self.LOG_FORMAT)

        # noinspection PyUnresolvedReferences
        clr.AddReference(self.dll_path)
        # noinspection PyUnresolvedReferences
        from TagAccessCS import TagAccessClass

        self.save_log = save_log
        self.plc_name = plc_name if plc_name else plc_ip
        self._tag_instance = TagAccessClass()
        self._plc_ip = plc_ip
        self.logger = logging.getLogger(__name__)
        self._handles = {}  # save handle
        self._file_handler = None  # 保存日志的处理器
        self._initial_log_config()

    def _initial_log_config(self):
        """日志配置."""
        if self.save_log:
            self._create_log_dir()
            self.logger.addHandler(self.file_handler)  # handler_passive 日志保存到统一文件

    @property
    def file_handler(self) -> TimedRotatingFileHandler:
        """设置保存日志的处理器, 每隔 24h 自动生成一个日志文件.

        Returns:
            TimedRotatingFileHandler: 返回 TimedRotatingFileHandler 日志处理器.
        """
        if self._file_handler is None:
            self._file_handler = TimedRotatingFileHandler(
                f"{os.getcwd()}/log/plc_{self.plc_name}.log",
                when="D", interval=1, backupCount=10, encoding="UTF-8"
            )
            self._file_handler.namer = self._custom_log_name
            self._file_handler.setFormatter(logging.Formatter(self.LOG_FORMAT))
        return self._file_handler

    def _custom_log_name(self, log_path: str):
        """自定义新生成的日志名称.

        Args:
            log_path: 原始的日志文件路径.

        Returns:
            str: 新生成的自定义日志文件路径.
        """
        _, suffix, date_str, *__ = log_path.split(".")
        new_log_path = f"{os.getcwd()}/log/plc_{self.plc_name}_{date_str}.{suffix}"
        return new_log_path

    @staticmethod
    def _create_log_dir():
        """判断log目录是否存在, 不存在就创建."""
        log_dir = pathlib.Path(f"{os.getcwd()}/log")
        if not log_dir.exists():
            os.mkdir(log_dir)

    @property
    def handles(self):
        """标签实例."""
        return self._handles

    @property
    def ip(self):
        """plc ip."""
        return self._plc_ip

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
            self._handles = {}
            self.logger.info("连接 %s plc 成功", self._plc_ip)
            return True
        self.logger.info("连接 %s plc 失败", self._plc_ip)
        return False

    def execute_read(self, data_type: str, address: str, save_log=True) -> Union[str, int, bool]:
        """ Read the value of the specified tag name.

        Args:
            address: Tag name to be read.
            data_type: Type of data read.
            save_log: Do you want to save the log? Default save.

        Returns:
            Union[str, int, bool]: Return the read value.

        Raises:
            PLCReadError: An exception occurred during the reading process.
        """
        if "str" in data_type:
            data_type = "string"
        data_type = f"TC_{data_type.upper()}"
        if (handle := self.handles.get(address)) is None:
            self.create_handles(address)
            handle = self.handles.get(address)

        result, state = self.tag_instance.ReadTag(handle, getattr(self.tag_instance.TagTypeClass, data_type))

        save_log and self.logger.info("读取 %s 地址的值是: %s", address, result)
        if state == self.tag_instance.TAResult.ERR_NOERROR:
            if data_type == "TC_STRING":
                if result:
                    result = result.strip()
                else:
                    result = ""
            return result
        raise PLCReadError("读取 %s 数据失败", address)

    def execute_read_array(self, data_type: str, address: str, save_log=True) -> list[Union[str, int, bool, float]]:
        """读取数组类型的数据.

        Args:
            address: Tag name to be read.
            data_type: 数据元素类型.
            save_log: Do you want to save the log? Default save.

        Returns:
            list[Union[str, int, bool, float]: 返回读取到的数组数据.

        Raises:
            PLCReadError: An exception occurred during the reading process.
        """
        try:
            data_type = f"TC_{data_type.upper()}"
            if (handle := self.handles.get(address)) is None:
                handle = self.tag_instance.CreateTagHandle(address)[0]
                self.handles.update({address: handle})
            results, state = self.tag_instance.ReadArray(handle, getattr(self.tag_instance.TagTypeClass, data_type))
            save_log and self.logger.info("读取 %s 地址的值是: %s", address, results)
            if state == self.tag_instance.TAResult.ERR_NOERROR:
                values = []
                for result in results:
                    if data_type == "TC_STRING":
                        if result:
                            result = result.strip()
                        else:
                            result = ""
                    values.append(result)
                return values
            raise PLCReadError("读取 %s 数据失败", address)
        except Exception as exc:
            raise PLCReadError(f"Read failure: may be not connect plc {self.ip}") from exc

    def execute_write(self, data_type: str, address: str, value: Union[int, bool, str], save_log=True):
        """ Write data of the specified type to the designated tag location.

        Args:
            address: Tag name to be written with value.
            data_type: Write value's data type.
            value: Write value.
            save_log: Do you want to save the log? Default save.

        Raises:
            PLCWriteError: An exception occurred during the writing process.
        """
        if "str" in data_type:
            data_type = "string"
        data_type = f"TC_{data_type.upper()}"
        if (handle := self.handles.get(address)) is None:
            self.create_handles(address)
            handle = self.handles.get(address)

        result = self.tag_instance.WriteTag(handle, value, getattr(self.tag_instance.TagTypeClass, data_type))

        if result != self.tag_instance.TAResult.ERR_NOERROR:
            raise PLCWriteError("向 %s 写入 %s 失败", address, value)

        if save_log:
            self.logger.info("向地址 %s 写入 %s 成功", address, value)

    def execute_write_array(self, data_type: str, address: str, value: list[Union[int, bool, str]], save_log=True):
        """写入数组数据.

        Args:
            address: 数组标签地址.
            data_type: 数组成员类型.
            value: Write value.
            save_log: Do you want to save the log? Default save.

        Raises:
            PLCWriteError: An exception occurred during the writing process.
        """
        if "str" in data_type:
            data_type = "string"
        data_type = f"TC_{data_type.upper()}"
        if (handle := self.handles.get(address)) is None:
            self.create_handles(address)
            handle = self.handles.get(address)

        result = self.tag_instance.WriteTagArray(
            handle, value, len(value), getattr(self.tag_instance.TagTypeClass, data_type)
        )

        if result != self.tag_instance.TAResult.ERR_NOERROR:
            raise PLCWriteError("向 %s 写入 %s 失败", address, value)

        if save_log:
            self.logger.info("向地址 %s 写入 %s 成功", address, value)

    def create_handles(self, address: str):
        """创建标签对应的 handle.

        Args:
            address: 标签地址.
        """
        handle, state = self.tag_instance.CreateTagHandle(address)
        if state == self.tag_instance.TAResult.ERR_NOERROR:
            self.logger.info("创建标签 %s 对应的 handle 成功", address)
            self.handles.update({address: handle})
        else:
            self.logger.info("创建标签 %s 对应的 handle 失败", address)
            self.communication_open()