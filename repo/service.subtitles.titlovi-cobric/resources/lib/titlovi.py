# -*- coding: utf-8 -*-

try:
    from HTMLParser import HTMLParser
except ModuleNotFoundError:
    from html.parser import HTMLParser
import re

from prelogging import Prelogger

import requests


# Custom exception, easy to catch
# all errors occurring in this class
class PrevodException(Exception):
    pass

# Custom subtitle parser due to complex HTML page
class PrijevodParser(HTMLParser):

    def __init__(self):
        HTMLParser.__init__(self)
        self.tag = None
        self.description = None
        self.archives = dict()
        self.url = None
        self.lang = None
        self.insideContainer = False
        self.log = Prelogger()

    def handle_starttag(self, tag, attrs):
        if tag == 'li' and len(attrs) > 0 and attrs[0][0] == 'class' and attrs[0][1].startswith("subtitleContainer"):
            self.insideContainer = True
        elif tag == 'h3' and len(attrs) > 0 and attrs[0][0] == 'data-id' and self.insideContainer:
            self.tag = tag
            self.url = '/download/?type=1&mediaid=' + attrs[0][1]
        elif tag == 'h4' and len(attrs) == 0:
            self.tag = tag
        elif tag == 'img' and len(attrs) > 1 and self.insideContainer and attrs[0][0] == 'class' and attrs[0][1].startswith("lang"):
            self.lang = attrs[1][1].rpartition('/')[-1][:2].upper().replace("RS", "SR")
        else:
            self.tag = None

    def handle_endtag(self, tag):
        if tag == 'li' and self.insideContainer and self.url and self.description:
            self.archives[self.url] = (self.description + ' ' + self.lang,)
            self.insideContainer = False
            self.url = None
            self.description = None
            self.lang = None

    def handle_data(self, data):
        if self.tag == 'h4' and self.insideContainer:
            # Get description
            self.description = data.strip()
        self.tag = None

    def get_archives(self):
        return self.archives


# Class handling HTTP traffic to the server
class Titlovi(object):
    # Data division :-)
    TITLOVI_SITE_NAME = "titlovi.com"
    TITLOVI_HOME_URL = "https://{0}".format(TITLOVI_SITE_NAME)
    TITLOVI_SEARCH_URL = "{0}/titlovi/?prijevod=".format(TITLOVI_HOME_URL)
    REGEX_ATTACHMENT = r'attachment; filename=(.+)'
    HEADER_CONT_TYPE = 'Content-Type'
    HEADER_CONT_DISP = 'Content-Disposition'
    USER_AGENT = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.79 Safari/537.36'
    HEADERS = {
        'Host': TITLOVI_SITE_NAME,
        'Origin': TITLOVI_HOME_URL,
        'Referer': "{0}/".format(TITLOVI_HOME_URL),
        'X-Requested-With': 'XMLHttpRequest',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'User-agent': USER_AGENT,
    }

    def __init__(self):
        self.log = Prelogger()
        self.sess = requests.Session()
        self.subtparser = PrijevodParser()
        self.archive = None
        self.archives = None

    # Checks headers, returning appropriate file name
    def _get_archive_name(self, adict):
        keys = list(map(lambda x: x.lower(), adict.keys()))
        filename = re.compile(self.REGEX_ATTACHMENT)
        if self.HEADER_CONT_TYPE.lower() in keys and adict[self.HEADER_CONT_TYPE] == 'application/x-.zip-compressed' \
                and self.HEADER_CONT_DISP.lower() in keys:
            match = filename.search(adict[self.HEADER_CONT_DISP])
            self.log.info("match: {0}".format(match))
            if match:
                # Condense multiple occurrences of dash into one
                pattern = '\-{2,}'
                return re.sub(pattern, '-', match.group(1).replace('_', '-').replace(' ', '-'))
            else:
                return None
        else:
            return None

    # Search by given keyword
    def search(self, search_term, season, episode, media_type):
        self.log.info("url: {0}".format("{0}{1}&t=2&s={2}&e={3}".format(self.TITLOVI_SEARCH_URL, search_term, season, episode)))
        if media_type == 'episode':
            r = self.sess.get(
                url="{0}{1}&t=2&s={2}&e={3}".format(self.TITLOVI_SEARCH_URL, search_term, season, episode),
                headers=self.HEADERS)
        elif media_type == 'movie':
            r = self.sess.get(
                url="{0}{1}&t=1".format(self.TITLOVI_SEARCH_URL, search_term),
                headers=self.HEADERS)
        r.raise_for_status()
        self.subtparser.feed(r.text)
        self.archives = self.subtparser.get_archives()

    # Get subtitle archive itself
    def get_subtitle_archive(self, archive_link):
        if not archive_link:
            raise PrevodException("Link for downloading archive was not provided!")
        r = self.sess.get(
            url="{0}{1}".format(self.TITLOVI_HOME_URL, archive_link),
            allow_redirects=True,
            headers=self.HEADERS)
        r.raise_for_status()
        # Check if this is indeed archive
        archive_name = self._get_archive_name(r.headers)
        if archive_name:
            self.archive = archive_name
            return archive_name, r.content,
        else:
            raise PrevodException("Archive '{0}' is not a subtitle archive!".format(archive_link))
