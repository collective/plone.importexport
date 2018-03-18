# -*- coding: utf-8 -*-
#  A class to catch error and exceptions


class ImportExportError(Exception):

    def __init__(self, message):
        self.message = message

    def __str__(self):
        return repr(self.message)
