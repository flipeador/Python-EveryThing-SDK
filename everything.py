"""
The Everything SDK provides a DLL and Lib interface to Everything over IPC.
Everything is required to run in the background.

documentation   : https://www.voidtools.com/support/everything/sdk/
dependency (SDK): https://www.voidtools.com/Everything-SDK.zip
"""
import os, ctypes
import datetime as dt
from typing import Final
from enum import Enum, IntEnum
from ctypes.wintypes import *
from struct import calcsize, unpack

MAX_PATH: Final = 32767

class Request(IntEnum):
    FileName                       = 0x00000001
    Path                           = 0x00000002
    FullPathAndFileName            = 0x00000004
    Extension                      = 0x00000008
    Size                           = 0x00000010
    DateCreated                    = 0x00000020
    DateModified                   = 0x00000040
    DateAccessed                   = 0x00000080
    Attributes                     = 0x00000100
    FileListFileName               = 0x00000200
    RunCount                       = 0x00000400
    DateRun                        = 0x00000800
    DateRecentlyChanged            = 0x00001000
    HighlightedFileName            = 0x00002000
    HighlightedPath                = 0x00004000
    HighlightedFullPathAndFileName = 0x00008000
    All                            = 0x0000FFFF

class Error(Enum):
    Ok              = 0  # The operation completed successfully.
    Memory          = 1  # Failed to allocate memory for the search query.
    IPC             = 2  # IPC is not available.
    RegisterClassEx = 3  # Failed to register the search query window class.
    CreateWindow    = 4  # Failed to create the search query window.
    CreateThread    = 5  # Failed to create the search query thread.
    InvalidIndex    = 6  # Invalid index. The index must be greater or equal to 0 and less than the number of visible results.
    InvalidCall     = 7  # Invalid call.

class ItemIterator:
    def __init__(self, everything, index):
        self.everything = everything
        self.index = index

    def __next__(self):
        self.index += 1
        if self.index < len(self.everything):
            return self
        raise StopIteration

    def __str__(self):
        return self.get_filename()

    def get_filename(self):
        """
        Gets the full path and file name of a visible result.
        :return: Returns a string if successful, otherwise returns None.
        """
        filename = ctypes.create_unicode_buffer(MAX_PATH)
        if self.everything.GetResultFullPathNameW(self.index, filename, MAX_PATH):
            return filename.value
        return None

    def get_size(self):
        """
        Gets the size of a visible result.
        :return: Returns the size if successful, otherwise returns None.
        """
        file_size = ULARGE_INTEGER()
        if self.everything.GetResultSize(self.index, file_size):
            return file_size.value
        return None

    def get_date_accessed(self):
        """
        Gets the accessed date of the visible result.
        """
        return self._get_result_date('Accessed')

    def get_date_created(self):
        """
        Gets the created date of the visible result.
        """
        return self._get_result_date('Created')

    def get_date_modified(self):
        """
        Gets the modified date of the visible result.
        """
        return self._get_result_date('Modified')

    def get_date_recently_changed(self):
        """
        Gets the recently changed date of the visible result.
        """
        return self._get_result_date('RecentlyChanged')

    def get_date_run(self):
        """
        Gets the run date of the visible result.
        """
        return self._get_result_date('Run')

    def is_file(self):
        """
        Determines if the visible result is a file.
        """
        return bool(self.everything.IsFileResult(self.index))

    def is_folder(self):
        """
        Determines if the visible result is a folder.
        """
        return bool(self.everything.IsFolderResult(self.index))

    def _get_result_date(self, tdate):
        filetime_date = ULARGE_INTEGER()
        if self.everything(f'GetResultDate{tdate}', self.index, filetime_date):
            winticks = int(unpack('<Q', filetime_date)[0])
            return dt.datetime.fromtimestamp((winticks - 116444736000000000) / 10000000)
        return None

class Everything:
    def __init__(self, dll=None):
        """
        Loads the EveryThing library into the address space of the calling process.
        :param dll: EveryThing SDK ('SDK\dll\Everything(32|64).dll')
        """
        dll = dll or r'{}\Everything\SDK\DLL\Everything{}.dll'\
            .format(os.environ['ProgramFiles'], 8*calcsize('P'))

        self.dll = ctypes.WinDLL(dll)

        self.func(BOOL, 'QueryW', BOOL)
        self.func(None, 'SetSearchW', LPCWSTR)
        self.func(None, 'SetRegex', BOOL)
        self.func(None, 'SetRequestFlags', DWORD)
        self.func(DWORD, 'GetResultListRequestFlags')
        self.func(DWORD, 'GetResultFullPathNameW', DWORD, LPWSTR, DWORD)
        self.func(DWORD, 'GetNumResults')
        self.func(BOOL, 'GetResultSize', DWORD, PULARGE_INTEGER)
        self.func(BOOL, 'GetResultDateAccessed', DWORD, PULARGE_INTEGER)
        self.func(BOOL, 'GetResultDateCreated', DWORD, PULARGE_INTEGER)
        self.func(BOOL, 'GetResultDateModified', DWORD, PULARGE_INTEGER)
        self.func(BOOL, 'GetResultDateRecentlyChanged', DWORD, PULARGE_INTEGER)
        self.func(BOOL, 'GetResultDateRun', DWORD, PULARGE_INTEGER)
        self.func(BOOL, 'IsFileResult', DWORD)
        self.func(BOOL, 'IsFolderResult', DWORD)
        self.func(DWORD, 'GetLastError')

    def __len__(self):
        """
        Gets the number of visible file and folder results.
        """
        return self.GetNumResults()

    def __getitem__(self, item:int):
        """
        Gets the result/item ``item``.
        """
        assert(0 <= item < len(self)), 'index out of range'
        return ItemIterator(self, item)

    def __getattr__(self, item):
        return getattr(self.dll, f'Everything_{item}')

    def __call__(self, name, *args):
        return getattr(self.dll, f'Everything_{name}')(*args)

    def __iter__(self):
        return ItemIterator(self, -1)

    def func(self, restype, name:str, *argtypes):
        func = getattr(self.dll, f'Everything_{name}')
        func.restype = restype
        func.argtypes = tuple(argtypes)

    def query(self, wait=True):
        """
        Executes an Everything IPC query with the current search state.
        :return: Returns True if successful, otherwise the return value is False.
        """
        return bool(self.QueryW(wait))

    def set_search(self, string:str):
        """
        Sets the search string for the IPC Query.
        """
        self.SetSearchW(str(string))

    def set_regex(self, enabled:bool):
        """
        Enables or disables Regular Expression searching.
        :param enabled: True to enable regex, False to disable regex.
        """
        self.SetRegex(enabled)

    def set_request_flags(self, flags:Request):
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
        return Request(self.GetResultListRequestFlags())

    def get_last_error(self):
        """
        Gets the last-error code value.
        """
        return Error(self.GetLastError())
