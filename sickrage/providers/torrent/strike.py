# Author: matigonkas
# URL: https://github.com/SiCKRAGETV/sickrage
#
# This file is part of SickRage.
#
# SickRage is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# SickRage is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickRage.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals

import sickrage
from sickrage.core.caches import tv_cache
from sickrage.providers import TorrentProvider


class STRIKEProvider(TorrentProvider):
    def __init__(self):
        super(STRIKEProvider, self).__init__("Strike",'getstrike.net', False)

        self.supportsBacklog = True

        self.ratio = 0
        self.cache = StrikeCache(self)
        self.minseed, self.minleech = 2 * [None]

    def search(self, search_strings, search_mode='eponly', epcount=0, age=0, epObj=None):

        results = []
        items = {'Season': [], 'Episode': [], 'RSS': []}

        for mode in search_strings.keys():  # Mode = RSS, Season, Episode
            sickrage.srCore.srLogger.debug("Search Mode: %s" % mode)
            for search_string in search_strings[mode]:

                if mode != 'RSS':
                    sickrage.srCore.srLogger.debug("Search string: " + search_string.strip())

                searchURL = self.urls['base_url'] + "/api/v2/torrents/search/?category=TV&phrase=" + search_string
                sickrage.srCore.srLogger.debug("Search URL: %s" % searchURL)

                try:
                    jdata = sickrage.srCore.srWebSession.get(searchURL).json()
                except Exception:
                    sickrage.srCore.srLogger.debug("No data returned from provider")
                    continue

                results = []

                for item in jdata['torrents']:
                    seeders = ('seeds' in item and item['seeds']) or 0
                    leechers = ('leeches' in item and item['leeches']) or 0
                    title = ('torrent_title' in item and item['torrent_title']) or ''
                    size = ('size' in item and item['size']) or 0
                    download_url = ('magnet_uri' in item and item['magnet_uri']) or ''

                    if not all([title, download_url]):
                        continue

                    # Filter unseeded torrent
                    if seeders < self.minseed or leechers < self.minleech:
                        if mode != 'RSS':
                            sickrage.srCore.srLogger.debug(
                                    "Discarding torrent because it doesn't meet the minimum seeders or leechers: {0} (S:{1} L:{2})".format(
                                            title, seeders, leechers))
                        continue

                    if mode != 'RSS':
                        sickrage.srCore.srLogger.debug("Found result: %s " % title)

                    item = title, download_url, size, seeders, leechers
                    items[mode].append(item)

            # For each search mode sort all the items by seeders if available
            items[mode].sort(key=lambda tup: tup[3], reverse=True)

            results += items[mode]

        return results

    def seedRatio(self):
        return self.ratio


class StrikeCache(tv_cache.TVCache):
    def __init__(self, provider_obj):
        tv_cache.TVCache.__init__(self, provider_obj)

        self.minTime = 30

    def _getRSSData(self):
        search_params = {'RSS': ['x264']}
        return {'entries': self.provider.search(search_params)}
