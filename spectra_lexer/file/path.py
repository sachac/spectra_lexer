""" Module for raw I/O operations as well as parsing file and resource paths. """

import fnmatch
import glob
import os

from appdirs import user_data_dir
from pkg_resources import resource_listdir, resource_string

from spectra_lexer.types import polymorph_index
from spectra_lexer.utils import str_prefix

# Root package name for built-in assets.
_PACKAGE_NAME = str_prefix(__package__, ".")
# Records resource types to check for membership by prefix.
use_if_path_startswith = polymorph_index()


class PathFinder:
    """ Parses path strings into resource identifiers by prefix. """

    @classmethod
    def from_string(cls, s:str):
        """ Given a string, determine the type of resource from the prefix and create the appropriate identifier. """
        for prefix, tp in PATH_TYPES:
            if s.startswith(prefix):
                return tp(s[len(prefix):])

    @classmethod
    def list_from_pattern(cls, pattern:str) -> list:
        """ Given a string, determine the resource type from the prefix and expand the pattern into a list. """
        return cls.from_string(pattern).search()


class Path(str):
    """ Abstract class for a resource path identifier. """

    @classmethod
    def from_list(cls, str_list:list) -> list:
        """ Given a list of strings, make a list of identifiers from the current class and return it. """
        return [cls(s) for s in str_list]

    def read(self) -> bytes:
        raise TypeError("Reading of this resource type is not supported.")

    def write(self, contents:bytes) -> None:
        raise TypeError("Writing of this resource type is not supported.")

    def search(self) -> list:
        return []


@use_if_path_startswith("")
class FilePath(Path):
    """ A file identifier, created from an ordinary file path. Will be used if nothing else matches. """

    def read(self) -> bytes:
        """ Open and read an entire text file as a byte string. """
        with open(self, 'rb') as fp:
            return fp.read()

    def write(self, contents:bytes) -> None:
        """ Write the given byte string as the sole contents of a file.
            If the directory path doesn't exist, create it. """
        directory = os.path.dirname(self) or "."
        os.makedirs(directory, exist_ok=True)
        with open(self, 'wb') as fp:
            fp.write(contents)

    def search(self) -> list:
        """ Return a list containing resources matching the identifier from the filesystem. """
        return self.from_list(glob.glob(self))


@use_if_path_startswith(":/")
class AssetPath(Path):
    """ A built-in asset identifier, created by using pkg_resources. """

    def read(self) -> bytes:
        """ Return a byte string representation of a built-in asset. """
        return resource_string(_PACKAGE_NAME, self)

    def search(self) -> list:
        """ Return a list containing resources matching the identifier from a built-in asset directory. """
        pathname, pattern = os.path.split(self)
        dir_list = resource_listdir(_PACKAGE_NAME, pathname)
        asset_names = fnmatch.filter(dir_list, pattern)
        return self.from_list([os.path.join(pathname, n) for n in asset_names])


@use_if_path_startswith("~")
class UserFilePath(FilePath):
    """ An identifier for a file in the user's app data directory. Produces instances of its superclass only. """

    def __new__(cls, s:str):
        """ If the prefix is ~appname/, it is a file from the user's application-specific data directory.
            If the prefix is ~/, it is specifically a file from THIS application's user data directory. """
        app_prefix, filename = s.split("/", 1)
        directory = user_data_dir(app_prefix or _PACKAGE_NAME)
        return FilePath(os.path.join(directory, filename))


@use_if_path_startswith("NUL")
class NullPath(Path):
    """ A dummy class that reads nothing and writes to a black hole. """

    read = lambda self: b""
    write = lambda *args: None


# Sort resource path types by prefix in reverse so longer ones are tried first.
PATH_TYPES = sorted(use_if_path_startswith.items(), reverse=True)