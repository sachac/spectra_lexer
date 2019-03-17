#!/usr/bin/env python3

""" Unit test utility functions, usable by any test module. """

import os

import pytest


def get_test_filename(r_type:str) -> str:
    """ Get the filename for the program test data by type (i.e. translations that should all pass with matches). """
    return os.path.join(__file__, "..", f"data/{r_type}.json")


def class_tester(test_classes:list):
    """ Using a list of relevant test classes, create a decorator which configures test functions to run
        not only on the designated base class, but also on any derived classes that appear in the list. """
    def using_base(cls:type):
        """ Decorator to define the base class for a class test, so that it may also be run on subclasses.
            Make sure the test is still run on the defined class at minimum even if it isn't in the list. """
        targets = [c for c in test_classes if issubclass(c, cls)] or [cls]
        return pytest.mark.parametrize("cls", targets)
    return using_base
