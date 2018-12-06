# -*- coding: utf-8 -*-

class SNMPExceptionError(Exception):
    pass

class SNMPLevelError(SNMPExceptionError):
    def __init__(self, msg):
        self.msg = msg
    def __str__(self):
        return "SNMPLevelError {}".format(self.msg)

class SNMPSocketError(SNMPExceptionError):
    def __init__(self, socker_exc):
        self.msg = str(socker_exc)
    def __str__(self):
        return "SNMPSocketError {}".format(self.msg)

class InvalidOIDError(Exception):
    pass
