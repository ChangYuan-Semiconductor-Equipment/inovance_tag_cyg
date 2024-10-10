"""PLC exception base class."""


class PLCBaseException(Exception):
    """Base exception class for PLC-related errors.

    This exception class inherits from Exception and serves as the base for all
    exceptions related to PLC operations.
    """


class PLCConnectError(PLCBaseException):
    """Exception raised for PLC connect errors.

    This exception is a subclass of PLCBaseException and is raised when there is
    an error related to connect the PLC.
    """


class PLCWriteError(PLCBaseException):
    """Exception raised for PLC write errors.

    This exception is a subclass of PLCBaseException and is raised when there is
    an error related to writing data to the PLC.
    """


class PLCReadError(PLCBaseException):
    """Exception raised for PLC read errors.

    This exception is a subclass of PLCBaseException and is raised when there
    is an error related to reading data from the PLC.
    """


class PLCRuntimeError(PLCBaseException):
    """Exception raised for PLC runtime errors.

    This exception is a subclass of PLCBaseException and is raised when there
    is a runtime error during PLC operations.
    """
