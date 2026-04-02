# -*- coding: utf-8 -*-

from sys import version_info
import xbmc


class Prelogger(object):

    @staticmethod
    def dolog(txt, log_level):
        if version_info[0] >= 3:
            message = '[titlovi.com by Cobric]: {0}'.format(txt)
        else:
            if isinstance(txt, str):
                txt = txt.decode("utf-8")
            message = (u'[titlovi.com by Cobric]: {0}'.format(txt))
        xbmc.log(msg=message, level=log_level)

    def info(self, message):
        self.dolog(message, xbmc.LOGINFO)

    def notice(self, message):
        self.dolog(message, xbmc.LOGINFO)

    def debug(self, message):
        self.dolog(message, xbmc.LOGDEBUG)

    def error(self, message):
        self.dolog(message, xbmc.LOGERROR)
