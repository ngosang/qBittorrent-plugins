#VERSION: 1.60
#AUTHORS: Diego de las Heras (ngosang@hotmail.es)
#         Christophe Dumez (chris@qbittorrent.org)

# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#    * Redistributions of source code must retain the above copyright notice,
#      this list of conditions and the following disclaimer.
#    * Redistributions in binary form must reproduce the above copyright
#      notice, this list of conditions and the following disclaimer in the
#      documentation and/or other materials provided with the distribution.
#    * Neither the name of the author nor the names of its contributors may be
#      used to endorse or promote products derived from this software without
#      specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

try:
    #python3
    from html.parser import HTMLParser
    from urllib.parse import quote, urlencode
    import http.client as httplib
except ImportError:
    #python2
    from HTMLParser import HTMLParser
    from urllib import quote, urlencode
    import httplib

#qBt
from novaprinter import prettyPrinter
from helpers import retrieve_url, download_file

class sumotorrent(object):
    url = 'http://www.sumotorrent.sx'
    name = 'SumoTorrent'
    supported_categories = {'all': '', 'movies': '4', 'tv': '9', 'music': '0', 'games': '2', 'anime': '8', 'software': '1'}
    trackers_list = ['udp://tracker.coppersurfer.tk:6969/announce',
                    'udp://tracker.open-internet.nl:6969/announce',
                    'udp://exodus.desync.com:6969/announce',
                    'udp://tracker.internetwarriors.net:1337/announce',
                    'udp://9.rarbg.com:2710/announce',
                    'udp://tracker.opentrackr.org:1337/announce']
    trackers = '&' + '&'.join(urlencode({'tr' : tracker}) for tracker in trackers_list)

    def download_torrent(self, download_link):
        # we need to follow the redirect to get the magnet link
        conn = httplib.HTTPConnection(self.url[7:])
        conn.request("GET", download_link.replace(self.url, ''))
        response = conn.getresponse()
        if response.status == 302:
            redirection_target = response.getheader('Location')
            print(redirection_target + self.trackers + " " + download_link)
        else:
            raise Exception('Error, please fill a bug report!')

    class MyHtmlParser(HTMLParser):
        def __init__(self, results, url, *args):
            HTMLParser.__init__(self)
            self.url = url
            self.td_counter = None
            self.current_item = None
            self.results = results
            
        def handle_starttag(self, tag, attrs):
            params = dict(attrs)
            if tag == 'a' and 'href' in params:
                if 'en/details/' in params['href'] and (self.td_counter is None or self.td_counter > 5):
                    self.current_item = {}
                    self.td_counter = 0
                    self.current_item['desc_link'] = params['href']
                elif params['href'].startswith('http://torrents.sumotorrent.sx/download/'):
                    parts = params['href'].strip().split('/')
                    self.current_item['link'] = self.url + '/torrent_download/'+parts[-3]+'/'+parts[-2]+'/'+quote(parts[-1]).replace('%20', '+')

            elif tag == 'td' and isinstance(self.td_counter,int):
                self.td_counter += 1
                if self.td_counter > 6:
                    # Display item
                    self.td_counter = None

                    self.current_item['engine_url'] = self.url
                    if not self.current_item['seeds'].isdigit():
                        self.current_item['seeds'] = 0
                    if not self.current_item['leech'].isdigit():
                        self.current_item['leech'] = 0

                    self.current_item['name'] = self.current_item['name'].strip()
                    try: #python2
                        self.current_item['name'] = self.current_item['name'].decode('utf8')
                    except:
                        pass

                    prettyPrinter(self.current_item)
                    self.results.append('a')

        def handle_data(self, data):
            if self.td_counter == 0:
                if 'name' not in self.current_item:
                    self.current_item['name'] = ''
                self.current_item['name'] += data
            elif self.td_counter == 3:
                if 'size' not in self.current_item:
                    self.current_item['size'] = ''
                self.current_item['size'] += data.strip()
            elif self.td_counter == 4:
                if 'seeds' not in self.current_item:
                    self.current_item['seeds'] = ''
                self.current_item['seeds'] += data.strip()
            elif self.td_counter == 5:
                if 'leech' not in self.current_item:
                    self.current_item['leech'] = ''
                self.current_item['leech'] += data.strip()

    def search(self, what, cat='all'):
        results_list = []
        parser = self.MyHtmlParser(results_list, self.url)
        i = 0
        while i < 6:
            dat = retrieve_url(self.url+'/searchResult.php?search=%s&lngMainCat=%s&order=seeders&by=down&start=%d'%(what, self.supported_categories[cat], i))
            parser.feed(dat)
            if len(results_list) < 1:
                break
            del results_list[:]
            i += 1
        parser.close()
