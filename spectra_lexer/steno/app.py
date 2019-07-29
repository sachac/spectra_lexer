from time import time

from .steno import StenoAnalyzer
from spectra_lexer.core.app import Application
from spectra_lexer.resource import ResourceManager


class StenoApplication(Application):
    """ Base application class with all required components for interactive console operations. """

    def _build_components(self) -> list:
        return [*super()._build_components(), ResourceManager(), StenoAnalyzer()]

    def run(self) -> None:
        """ Run the console in an interactive read-eval-print loop. """
        self.COREConsoleOpen()
        while True:
            self.COREConsoleInput(input())


class _BatchApplication(StenoApplication):
    """ Base application class for batch console operations. """

    COMMAND = ""

    def run(self) -> int:
        """ Run the main command in the console in batch mode and time its execution. """
        start_time = time()
        print("Operation started...")
        self.COREConsoleOpen(interactive=False)
        self.COREConsoleInput(self.COMMAND)
        print(f"Operation done in {time() - start_time:.1f} seconds.")
        return 0


class StenoAnalyzeApplication(_BatchApplication):
    """ Runs the lexer on every item in a JSON steno translations dictionary. """

    COMMAND = "RSRulesSave(LXLexerQueryAll())"


class StenoIndexApplication(_BatchApplication):
    """ Analyzes translations files and creates indices from them. """

    COMMAND = "RSIndexSave(LXLexerMakeIndex())"
