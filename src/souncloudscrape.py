import maya 
from requests_html import HTMLSession

session = HTMLSession()

class Track: 
    def __init__(self, title, artist, date, url, duration):
        self.title = title
        self.artist = artist
        self.date = date
        self.url = url
        self.duration = duration

    def __repr__(self):
        return "<Track url={!r}>".format(self.url)
    
    @classmethod
    def from_elements(cls, *, sc, element): 
        track = cls() 

        track.title = element.find(".soundTitle__title", first=True).text
        try:
            track.likes = int(element.find('button.sc-button-like.sc-button.sc-button-small.sc-button-responsive', first=True).html.split('title="Like">')[1].split('<')[0])
        except ValueError:
            pass
        track.posted = maya.parse(element.find('.relativeTime', first=True).attrs['datetime']).datetime
        track.url = '{}{}'.format(sc.base_url, element.find('.soundTitle__title', first=True).attrs['href'])

        return track


class User:
    def __init__(self, *, username, sc):
        self.username = username
        self.sc = sc

        self._meta = {}

    def __repr__(self):
        return "<User {!r}>".format(self.username)

    @property
    def meta(self):
        print("hi")
        if self._meta:
            return self._meta

        r = session.get(self.sc._construct_url(self.username))
        print("this is r", r) 
        r.html.render()

        # Get metadata.
        self._meta['username'] = r.html.find('.profileHeaderInfo__userName', first=True).text
        try:
            self._meta['additional'] = r.html.find('.profileHeaderInfo__additional', first=True).text
        except AttributeError:
            self._meta['additional'] = None

        try:
            self._meta['bio'] = r.html.find('#content > div > div.l-fluid-fixed > div.l-sidebar-right.l-user-sidebar-right > div > article.infoStats > div.infoStats__description > div > div > div', first=True).text
        except AttributeError:
            self._meta['bio'] = None

        self._meta['followers'] = int(r.html.find('#content > div > div.l-fluid-fixed > div.l-sidebar-right.l-user-sidebar-right > div > article.infoStats > table > tbody > tr > td:nth-child(1) > a > div', first=True).text.replace(',', '').replace('K', '000'))
        self._meta['following'] = int(r.html.find('#content > div > div.l-fluid-fixed > div.l-sidebar-right.l-user-sidebar-right > div > article.infoStats > table > tbody > tr > td:nth-child(2) > a > div', first=True).text.replace(',', '').replace('K', '000'))
        self._meta['tracks'] = int(r.html.find('#content > div > div.l-fluid-fixed > div.l-sidebar-right.l-user-sidebar-right > div > article.infoStats > table > tbody > tr > td:nth-child(3) > a > div', first=True).text.replace(',', '').replace('K', '000'))
        try:
            self._meta['likes'] = int(r.html.find('#content > div > div.l-fluid-fixed > div.l-sidebar-right.l-user-sidebar-right > div > article.sidebarModule.g-all-transitions-200-linear.likesModule > a > h3 > span.sidebarHeader__actualTitle', first=True).text.split()[0].replace(',', ''))
        except AttributeError:
            self._meta['likes'] = None


        return self._meta


    @property
    def following(self):
        def gen():
            r = session.get(self.sc._construct_url(self.username, 'following'))

            r.html.render(scrolldown=int(self.meta['following'] / 10), sleep=2)

            for user in r.html.find('a.userBadgeListItem__heading'):
                username = user.attrs['href'][1:].strip()
                yield User(username=username, sc=self.sc)

        return [g for g in gen()]

    @property
    def followers(self):
        def gen():
            r = session.get(self.sc._construct_url(self.username, 'followers'))

            r.html.render(scrolldown=int(self.meta['followers'] / 10), sleep=2)

            for user in r.html.find('a.userBadgeListItem__heading'):
                username = user.attrs['href'][1:].strip()
                yield User(username=username, sc=self.sc)

        return [g for g in gen()]

    @property
    def tracks(self):
        def gen():
            r = session.get(self.sc._construct_url(self.username, 'tracks'))

            r.html.render(scrolldown=int(self.meta['tracks']), sleep=1)

            for track in r.html.find('.sound__content'):
                yield Track.from_element(sc=self.sc, element=track)

        return [g for g in gen()]

class PlayList: 
    def __init__(self, search_term, sc): 
        self.base_url = 'https://soundcloud.com/search/sets?q='
        self.search_term = search_term
        self.sc = sc
        self.url = self.base_url + self.search_term

    def search(self): 
        r = session.get(self.url)
        r.html.render()
        print('yo certainly in this thang'); 
        for like in r.html.find('button[aria-label="Like"]'): 
            print(like.text)

    def search_playwright(self):
        from playwright.sync_api import sync_playwright
        import json
        print('howdy')
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            page = browser.new_page()
            print('this is here')
            def handle_response(response):
                print('this is response', response)
                print('this is reponse url', response.url)
                if ("tracks?" in response.url):
                    print('tracks exists \n \n \n YO! It exist my dawg')
                    print(json.dumps(response.json()))
            page.on("response", handle_response)
            page.goto(self.url, wait_until="networkidle") 
            page.context.close() 
            browser.close()
        
    


class SoundCloud:
    def __init__(self):
        self.base_url = 'https://soundcloud.com'

    def _construct_url(self, *frags):
        return '{}/{}'.format(self.base_url, '/'.join(frags))

    def get_playlists(self, search_term):
        return PlayList(search_term=search_term, sc=self)

    def get_user(self, username):
        return User(username=username, sc=self)
