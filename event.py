from enum import Enum


class Category(Enum):
    SPORTS = "Sports"
    THEATERS = "Theaters"
    CONCERTS = "Concerts"
    FESTIVALS = "Festivals"
    CLUBBING = "Clubbing"


class Event:
    def __init__(self, name, startingDate, endingDate, location,
                 description, imageUrl, category, moreDetails, valid):
        self.name = name
        self.startingDate = startingDate
        self.endingDate = endingDate
        self.location = location
        self.description = description
        self.imageUrl = imageUrl
        self.moreDetails = moreDetails
        self.valid = valid

        for cat in Category:
            if category == cat.value:
                self.category = category

    def __str__(self):
        return self.name

