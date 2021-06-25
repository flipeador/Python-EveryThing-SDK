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

class Everything:
    def __init__(self, dll=None):
        """
        Loads the EveryThing library into the address space of the calling process.
        :param dll: EveryThing SDK ('SDK\dll\Everything(32|64).dll')
        """
        dll = dll or r'{}\Everything\SDK\DLL\Everything{}.dll'\
            .format(os.environ['ProgramFiles'], 8*calcsize('P'))

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

    def get_filename(self, *, index=None):
        """
        Gets the full path and file name of a visible result.
        :return: Returns a string if successful, otherwise returns None.
        """
        filename = ctypes.create_unicode_buffer(MAX_PATH)
        if self.GetResultFullPathNameW(self._index(index), filename, MAX_PATH):
            return ctypes.wstring_at(filename)
        return None

    def get_count(self):
        """
        Gets the number of visible file and folder results.
        """
        return self.GetNumResults()

    def get_size(self, *, index=None):
        """
        Gets the size of a visible result.
        :return: Returns the size if successful, otherwise returns None.
        """
        file_size = ULARGE_INTEGER(1)
        if self.GetResultSize(self._index(index), file_size):
            return file_size.value
        return None

    def get_date_accessed(self, *, index=None):
        """
        Gets the accessed date of the visible result.
        """
        return self.get_result_date(self._index(index), 'Accessed')

    def get_date_created(self, *, index=None):
        """
        Gets the created date of the visible result.
        """
        return self.get_result_date(self._index(index), 'Created')

    def get_date_modified(self, *, index=None):
        """
        Gets the modified date of the visible result.
        """
        return self._get_result_date(self._index(index), 'Modified')

    def get_date_recently_changed(self, *, index=None):
        """
        Gets the recently changed date of the visible result.
        """
        return self._get_result_date(self._index(index), 'RecentlyChanged')

    def get_date_run(self, *, index=None):
        """
        Gets the run date of the visible result.
        """
        return self._get_result_date(self._index(index), 'Run')

    def is_file(self, *, index=None):
        """
        Determines if the visible result is a file.
        """
        return bool(self.IsFileResult(self._index(index)))

    def is_folder(self, *, index=None):
        """
        Determines if the visible result is a folder.
        """
        return bool(self.IsFolderResult(self._index(index)))

    def get_last_error(self):
        """
        Gets the last-error code value.
        """
        return Error(self.GetLastError())

    def _index(self, index):
        return self.index if index is None else index

    def _get_result_date(self, index, tdate):
        filetime_date = ULARGE_INTEGER(1)
        if self(f'GetResultDate{tdate}', index, filetime_date):
            winticks = int(unpack('<Q', filetime_date)[0])
            return dt.datetime.fromtimestamp((winticks - 116444736000000000) / 10000000)
        return None

    def __getattr__(self, item):
        return getattr(self.dll, f'Everything_{item}')

    def __call__(self, name, *args):
        return getattr(self.dll, f'Everything_{name}')(*args)

    def __iter__(self):
        self.index = -1
        self.count = self.get_count()
        return self

    def __next__(self):
        self.index += 1
        if self.index < self.count:
            return self
        raise StopIteration
