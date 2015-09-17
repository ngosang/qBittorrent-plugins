#VERSION: 1.00
#AUTHORS: Diego de las Heras (ngosang@hotmail.es)

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
    from http.client import HTTPConnection as http
except ImportError:
    #python2
    from HTMLParser import HTMLParser
    from httplib import HTTPConnection as http

#qBt
from novaprinter import prettyPrinter
from helpers import download_file

class tntvillage(object):
    """ Search engine class """
    url = 'http://www.tntvillage.scambioetico.org'
    name = 'TNT Village'
    supported_categories = {'all'       : '0',
                            'movies'    : '4',
                            'tv'        : '29',
                            'music'     : '2',
                            'games'     : '11',
                            'anime'     : '7',
                            'software'  : '10',
                            'books'     : '3'}

    def download_torrent(self, info):
        """ Downloader """
        print(download_file(info))

    class MyHtmlParseWithBlackJack(HTMLParser):
        """ Parser class """
        def __init__(self, results, url):
            HTMLParser.__init__(self)
            self.results = results
            self.url = url
            self.td_counter = None
            self.current_item = None

        def handle_starttag(self, tag, attrs):
            params = dict(attrs)
            if tag == 'a':
                if 'href' in params:
                    if self.td_counter == 1:
                        self.current_item['link'] = params['href'].strip()
                    elif self.td_counter == 7:
                        self.current_item['desc_link'] = params['href'].strip()

            elif tag == 'tr':  
                self.current_item = {}
                self.td_counter = 0

            elif tag == 'td':
                if self.td_counter is not None:
                    self.td_counter += 1

        def handle_endtag(self, tag):
            if tag == 'tr' and 'link' in self.current_item:
                # display item
                self.td_counter = None
                self.current_item['engine_url'] = self.url
                self.current_item['size'] = ''
                self.current_item['name'] = self.current_item['name'].strip()
                prettyPrinter(self.current_item)
                self.results.append('a')

        def handle_data(self, data):                     
            if self.td_counter == 4:
                self.current_item['leech'] = data.strip()
                if not self.current_item['leech'].isdigit():
                    self.current_item['leech'] = 0
            elif self.td_counter == 5:
                self.current_item['seeds'] = data.strip()
                if not self.current_item['seeds'].isdigit():
                    self.current_item['seeds'] = 0
            elif self.td_counter == 7:
                if 'name' not in self.current_item:
                    self.current_item['name'] = data
                else:
                    self.current_item['name'] += " " + data
                

    def search(self, what, cat="all"):
        """ Performs search """

        list_searches = []
        parser = self.MyHtmlParseWithBlackJack(list_searches, self.url)
        headers = {"Content-type": "application/x-www-form-urlencoded", "X-Requested-With": "XMLHttpRequest"}
        connection = http("www.tntvillage.scambioetico.org")
        i = 1
        while i < 15:
            query = "cat=%s&page=%d&srcrel=%s" % (self.supported_categories[cat], i, what)
            connection.request("POST", "/src/releaselist.php", query, headers)
            response = connection.getresponse()
            if response.status != 200:
                return
            html = response.read().decode('utf-8')
            parser.feed(html)
            if len(list_searches) < 1:
                break
            del list_searches[:]
            i += 1

        connection.close()
        parser.close()
