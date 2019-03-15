""" Module with instances and groupings of specialized string search dictionaries by the resource they represent. """

from typing import Dict, Optional

from .dict import ReverseStripCaseSearchDict, StripCaseSearchDict
from spectra_lexer.utils import delegate_to


class ResourceNexus:

    PRIORITY: int = 0  # Search priority. Resource prefixes are checked in order from highest to lowest priority nexus.
    PREFIX: str = ""   # Prefix to test (and strip) on input patterns. Empty by default, so pattern is unmodified.

    _d: StripCaseSearchDict = StripCaseSearchDict()  # Current dict used for lookups and commands.

    def check(self, pattern:str, **mode_kwargs) -> Optional[str]:
        """ Indicator function that returns a new pattern on success and can modify the current dict reference. """
        prefix = self.PREFIX
        if pattern.startswith(prefix):
            return pattern[len(prefix):]

    def command_args(self, match:str, mapping:object) -> Optional[tuple]:
        """ Return a tuple of items that can be directly called as an engine command to show a result, or None. """

    search = delegate_to("_d")
    lookup = delegate_to("_d")


class TranslationNexus(ResourceNexus):
    """ A hybrid forward+reverse steno translation nexus. Used when nothing else matches. """

    PRIORITY = 1  # Has low priority. It must outrank the default nexus only.
    _CMD_KEY: str = "show_translation"    # Key for engine command.

    _forward: StripCaseSearchDict         # Forward translations dict (strokes -> English words).
    _reverse: ReverseStripCaseSearchDict  # Reverse translations dict (English words -> strokes).

    def __init__(self, d:Dict[str, str]):
        """ For translation-based searches, spaces and hyphens should be stripped off each end. """
        self._forward = StripCaseSearchDict(d, strip_chars=" -")
        self._reverse = ReverseStripCaseSearchDict(match=d, strip_chars=" -")

    def check(self, pattern:str, strokes:bool=False, **mode_kwargs) -> str:
        """ Indicator function that always returns success. Does not modify the pattern. """
        self._d = self._forward if strokes else self._reverse
        return pattern

    def command_args(self, match:str, mapping:object) -> tuple:
        """ The order of strokes/word in the lexer command is reversed for a reverse dict. """
        args = (match, mapping) if self._d is self._forward else (mapping, match)
        return (self._CMD_KEY, *args)


class RulesNexus(ResourceNexus):
    """ A simple nexus for rule search by name when a prefix is added. There is only one dict which never changes. """

    PRIORITY = 2  # Has medium priority. It must outrank the translations nexus.
    PREFIX = "/"  # A basic slash which is also a prefix of *other*, higher priority prefixes.
    _CMD_KEY: str = "new_output"  # Key for engine command.

    def __init__(self, d:dict):
        """ To search the rules dictionary by name, prefix and suffix reference symbols should be stripped. """
        self._d = StripCaseSearchDict(d, strip_chars=" .+-~")

    def command_args(self, match:str, mapping:object) -> tuple:
        """ If the mapping is a rule, send it as direct output just like the lexer would and return. """
        return self._CMD_KEY, mapping


class IndexNexus(ResourceNexus):
    """ A resource-heavy nexus for finding translations that contain a particular steno rule. """

    PRIORITY = 3   # Has highest priority but lowest chance of success. Must outrank the rules nexus.
    PREFIX = "//"  # This includes the rules prefix, so it must be checked first.

    _children: Dict[str, TranslationNexus]  # Dict containing a whole subnexus for every rule name.
    _d: TranslationNexus                    # Current nexus used to redirect checks and commands.

    def __init__(self, d:Dict[str, dict]):
        """ Index search is a two-part search. The first part goes by rule name, and is very precise.
            It is a key to a dict of child nexus objects, so only exact matches will work. """
        self._children = {k: TranslationNexus(v) for k, v in d.items()}
        self._d = TranslationNexus({})

    def check(self, pattern:str, **mode_kwargs) -> Optional[str]:
        """ Indicator function for a rules search. Prefix is stripped by super method to get subnexus:pattern combo. """
        pattern = super().check(pattern)
        if pattern is not None:
            key, pattern = (pattern.split(":", 1) + [""])[:2]
            if key in self._children:
                d = self._d = self._children[key]
                return d.check(pattern, **mode_kwargs)

    command_args = delegate_to("_d")