"""
The Everything SDK provides a DLL and Lib interface to Everything over IPC.
Everything is required to run in the background.

documentation   : https://www.voidtools.com/support/everything/sdk/
dependency (SDK): https://www.voidtools.com/Everything-SDK.zip
"""
import os
import ctypes
from ctypes.wintypes import *
import struct
import datetime as dt
from typing import Final

EVERYTHING_MAX_PATH: Final = 32767

EVERYTHING_REQUEST_FILE_NAME                          : Final = 0x00000001
EVERYTHING_REQUEST_PATH                               : Final = 0x00000002
EVERYTHING_REQUEST_FULL_PATH_AND_FILE_NAME            : Final = 0x00000004
EVERYTHING_REQUEST_EXTENSION                          : Final = 0x00000008
EVERYTHING_REQUEST_SIZE                               : Final = 0x00000010
EVERYTHING_REQUEST_DATE_CREATED                       : Final = 0x00000020
EVERYTHING_REQUEST_DATE_MODIFIED                      : Final = 0x00000040
EVERYTHING_REQUEST_DATE_ACCESSED                      : Final = 0x00000080
EVERYTHING_REQUEST_ATTRIBUTES                         : Final = 0x00000100
EVERYTHING_REQUEST_FILE_LIST_FILE_NAME                : Final = 0x00000200
EVERYTHING_REQUEST_RUN_COUNT                          : Final = 0x00000400
EVERYTHING_REQUEST_DATE_RUN                           : Final = 0x00000800
EVERYTHING_REQUEST_DATE_RECENTLY_CHANGED              : Final = 0x00001000
EVERYTHING_REQUEST_HIGHLIGHTED_FILE_NAME              : Final = 0x00002000
EVERYTHING_REQUEST_HIGHLIGHTED_PATH                   : Final = 0x00004000
EVERYTHING_REQUEST_HIGHLIGHTED_FULL_PATH_AND_FILE_NAME: Final = 0x00008000
EVERYTHING_REQUEST_ALL                                : Final = 0x0000FFFF

EVERYTHING_OK                   : Final = 0  # The operation completed successfully.
EVERYTHING_ERROR_MEMORY         : Final = 1  # Failed to allocate memory for the search query.
EVERYTHING_ERROR_IPC            : Final = 2  # IPC is not available.
EVERYTHING_ERROR_REGISTERCLASSEX: Final = 3  # Failed to register the search query window class.
EVERYTHING_ERROR_CREATEWINDOW   : Final = 4  # Failed to create the search query window.
EVERYTHING_ERROR_CREATETHREAD   : Final = 5  # Failed to create the search query thread.
EVERYTHING_ERROR_INVALIDINDEX   : Final = 6  # Invalid index. The index must be greater or equal to 0 and less than the number of visible results.
EVERYTHING_ERROR_INVALIDCALL    : Final = 7  # Invalid call.

class Everything:
    """
    Loads the EveryThing library into the address space of the calling process.
    :param dll: SDK\dll\Everything(32|64).dll
    """
    def __init__(self, dll=None):
        if dll is None:
            dll = f"{os.environ['ProgramFiles']}\\Everything\\SDK\\DLL\\Everything{8*struct.calcsize('P')}.dll"
        self.dll = ctypes.WinDLL(dll)

        self.set_args('QueryW', BOOL, BOOL)
        self.set_args('SetSearchW', None, LPCWSTR)
        self.set_args('SetRegex', None, BOOL)
        self.set_args('SetRequestFlags', None, DWORD)
        self.set_args('GetResultListRequestFlags', DWORD)
        self.set_args('GetResultFullPathNameW', DWORD, DWORD, LPWSTR, DWORD)
        self.set_args('GetNumResults', DWORD)
        self.set_args('GetResultSize', BOOL, DWORD, PULARGE_INTEGER)
        self.set_args('GetResultDateAccessed', BOOL, DWORD, PULARGE_INTEGER)
        self.set_args('GetResultDateCreated', BOOL, DWORD, PULARGE_INTEGER)
        self.set_args('GetResultDateModified', BOOL, DWORD, PULARGE_INTEGER)
        self.set_args('GetResultDateRecentlyChanged', BOOL, DWORD, PULARGE_INTEGER)
        self.set_args('GetResultDateRun', BOOL, DWORD, PULARGE_INTEGER)
        self.set_args('IsFileResult', BOOL, DWORD)
        self.set_args('IsFolderResult', BOOL, DWORD)
        self.set_args('GetLastError', DWORD)

    def set_args(self, name, restype, *argtypes):
        func = getattr(self.dll, f'Everything_{name}')
        func.restype = restype
        func.argtypes = argtypes

    def query(self, wait=True):
        """
        Executes an Everything IPC query with the current search state.
        :return: Returns True if successful, otherwise the return value is False.
        """
        return bool(self.QueryW(wait))

    def set_search(self, string):
        """
        Sets the search string for the IPC Query.
        """
        self.SetSearchW(string)

    def set_regex(self, enabled):
        """
        Enables or disables Regular Expression searching.
        :param enabled: True to enable regex, False to disable regex.
        """
        self.SetRegex(enabled)

    def set_request_flags(self, flags):
        """
        Sets the desired result data.
        It is possible the requested data is not available, in which case after you have received your
        results you should call ``get_result_list_request_flags`` to determine the available result data.
        """
        self.SetRequestFlags(flags)

    def get_result_list_request_flags(self):
        """
        Gets the flags of available result data.
        The requested result data may differ to the desired result data specified in ``set_request_flags``.
        """
        return self.GetResultListRequestFlags()

    def get_result(self, index):
        """
        Gets the full path and file name of a visible result.
        :param index: Zero based index of the visible result.
        :return: Returns a string if successful, otherwise returns None.
        """
        filename = ctypes.create_unicode_buffer(EVERYTHING_MAX_PATH)
        if self.GetResultFullPathNameW(index, filename, EVERYTHING_MAX_PATH):
            return ctypes.wstring_at(filename)
        return None

    def get_result_count(self):
        """
        Gets the number of visible file and folder results.
        """
        return self.GetNumResults()

    def get_result_size(self, index):
        """
        Gets the size of a visible result.
        :param index: Zero based index of the visible result.
        :return: Returns the size if successful, otherwise returns None.
        """
        file_size = LARGE_INTEGER(1)
        if self.GetResultSize(index, file_size):
            return file_size.value
        return None

    def get_result_date(self, index, tdate):
        """
        Gets the date of a visible result.
        :param index: Zero based index of the visible result.
        :param tdate: Accessed/Created/Modified/RecentlyChanged/Run.
        :return: Returns datetime if successful, otherwise returns None.
        """
        filetime_date = ULARGE_INTEGER(1)
        if self(f'GetResultDate{tdate}', index, filetime_date):
            winticks = int(struct.unpack('<Q', filetime_date)[0])
            return dt.datetime.fromtimestamp((winticks - 116444736000000000) / 10000000)
        return None

    def is_file_result(self, index):
        """
        Determines if the visible result is a file.
        """
        return bool(self.IsFileResult(index))

    def is_folder_result(self, index):
        """
        Determines if the visible result is a folder.
        """
        return bool(self.IsFolderResult(index))

    def get_last_error(self):
        """
        Gets the last-error code value.
        """
        return self.GetLastError()

    def __getattr__(self, item):
        return getattr(self.dll, f'Everything_{item}')

    def __call__(self, name, *args):
        return getattr(self.dll, f'Everything_{name}')(*args)
