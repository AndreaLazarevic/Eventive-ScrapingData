from bs4 import BeautifulSoup
from datetime import datetime
import requests
import abc
from event import Event, Category
import pyrebase


def configureDatabase():
    config = {
        
    }

    firebase = pyrebase.initialize_app(config)
    db = firebase.database()

    return db


def serialise_to_json(obj):
    known_classes = {
        'Event': Event,
    }

    obj_type = type(obj).__name__

    if obj_type not in known_classes.keys():
        known_types = ", ".join(known_classes.keys())
        raise TypeError("Error! Unknown class! "
                        "Can only serialise objects of types: {}".format(known_types))

    obj_dict = {}
    obj_dict.update(vars(obj))

    return obj_dict


def convert_to_timestamp(datetime_object):
    timestamp = datetime.timestamp(datetime_object)
    return timestamp


# For websites which display dates using full month name but in Serbian
def month(i):
    switcher = {
        1: 'januar',
        2: 'februar',
        3: 'mart',
        4: 'april',
        5: 'maj',
        6: 'juni',
        7: 'juli',
        8: 'avgust',
        9: 'septembar',
        10: 'oktobar',
        11: 'novembar',
        12: 'decembar'
    }
    return switcher.get(i, "Invalid month")


class GenericParser:
    def templateMethod(self, url, numberOfPages, providedCategory):
        events = []
        if numberOfPages != 0:
            pages = [str(i) for i in range(1, numberOfPages)]

            for page in pages:
                response = requests.get(url + page)
                soup = BeautifulSoup(response.content, 'html.parser')
                events = self.execute(soup, providedCategory)
                self.addToDatabase(events)

        if numberOfPages == 0:
            response = requests.get(url)
            soup = BeautifulSoup(response.content, 'html.parser')
            events = self.execute(soup, providedCategory)
            self.addToDatabase(events)

        return events

    def addToDatabase(self, events):
        db = configureDatabase()
        for event in events:
            event = serialise_to_json(event)
            db.child("events-new").push(event)

    @abc.abstractmethod
    def execute(self, soup):
        """Parse data from concrete website and returns list of events."""


class TheatersParser(GenericParser):
    def execute(self, soup, providedCategory):
        theaterItems = soup.find_all(class_='rs-inner-single-over')
        theaterEvents = []

        for item in theaterItems:
            category = providedCategory
            name = item.find('h2').get_text()
            date = item.find(class_='rs-inner-date').get_text()

            # Converting date to appropriate format
            datetime_object = datetime.strptime(date, '%d.%m.%Y.')
            date = convert_to_timestamp(datetime_object)


            if item.find(class_='rs-inner-time').find('a') is not None:
                location = item.find(class_='rs-inner-time').find('a').get_text()
            else:
                location = ""

            moreDetails = item.find(class_='rs-single-tags').find('a')['href']
            detailPage = requests.get(moreDetails)
            detailSoup = BeautifulSoup(detailPage.content, 'html.parser')

            description = detailSoup.find(class_='rs-tab-content').find_all('p')
            pretty = ""

            for paragraph in description:
                pretty += paragraph.get_text() + " "

            description = pretty
            imageUrl = detailSoup.find(class_='rs-featured-single').find('img')['src']

            event = Event(name, date, date, location, description, imageUrl, category, moreDetails, 0)

            theaterEvents.append(event)

        return theaterEvents


class DayInBelgradeParser(GenericParser):
    def execute(self, soup, providedCategory):
        eventItems = soup.find_all(class_='item-list')
        events = []

        for item in eventItems:
            category = providedCategory
            name = item.find('a').get_text()
            date = item.find(class_='tie-date').get_text()

            for i in range(1, 13):
                date = date.replace(" " + month(i) + " ", str(i) + ".")

            # Converting date to appropriate format
            datetime_object = datetime.strptime(date, '%d.%m.%Y.')
            date = convert_to_timestamp(datetime_object)

            location = ""
            description = item.find(class_='entry').find('p').get_text()
            if item.find('img') is not None:
                imageUrl = item.find('img')['src']
            else:
                imageUrl = ""

            moreDetails = "https://www.danubeogradu.rs" + item.find(class_='entry').find(class_='more-link')['href']

            event = Event(name, date, date, location, description, imageUrl, category, moreDetails, 0)

            events.append(event)

        return events


class ClubbingParser(GenericParser):
    def execute(self, soup, providedCategory):
        eventItems = soup.find_all(class_='media event')
        events = []

        for item in eventItems:
            category = providedCategory
            name = item.find(class_='media-heading').find('a').get_text().lstrip()
            date = item.find(class_='time').get_text().replace("  ", "").replace("\n", " ")

            location = item.find(class_='icon-location').get_text()
            description = ""
            imageUrl ="https://onlyclubbing.com" + item.find('img')['src']
            moreDetails = item.find(class_='media-heading').find('a')['href']

            event = Event(name, date, date, location, description, imageUrl, category, moreDetails, 0)

            events.append(event)

        return events


if __name__ == "__main__":
    list = []

    # theatersParser = TheatersParser()
    # list = theatersParser.templateMethod("https://repertoar.rs/predstave/", 0, Category.THEATERS.value)

    # concertsParser = DayInBelgradeParser()
    # list = concertsParser.templateMethod("https://www.danubeogradu.rs/izlasci/muzika/koncerti/page/", 4,
    #                                    Category.CONCERTS.value)

    # festivalsParser = DayInBelgradeParser()
    # list = festivalsParser.templateMethod("https://www.danubeogradu.rs/izlasci/festivali/page/", 4,
    # Category.FESTIVALS.value)

    # sportsParser = DayInBelgradeParser()
    # list = sportsParser.templateMethod("https://www.danubeogradu.rs/izlasci/sport/", 0, Category.SPORTS.value)

    # Pages for clubbing events does not exist anymore

    # clubbingParser = DayInBelgradeParser()
    # list = clubbingParser.templateMethod("https://www.danubeogradu.rs/izlasci/muzika/clubbing/", 0,
    # Category.CLUBBING.value)

    # clubbingParser = ClubbingParser()
    # list = clubbingParser.templateMethod("https://onlyclubbing.com/kalendar-desavanja", 0, Category.CLUBBING.value)

    for item in list:
        print(item)
