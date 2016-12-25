import string
import random

class Generator():

    def id_generator(self, size=6, chars=string.ascii_uppercase + string.digits):
        return ''.join(random.choice(chars) for _ in range(size))

class Level():
    def __init__(self, bid, ask, bidQty, askQty, bidQuoteId, askQuoteId):
        self.bid = bid
        self.ask = ask
        self.bidQty = bidQty
        self.askQty = askQty
        self.bidQuoteId = bidQuoteId
        self.askQuoteId = askQuoteId

class OrderBook():
    def __init__(self, ric, size):
        self.depths = size * [None]
        self.ric = ric
    def getDepth(self):
        return self.depths.__len__()

    def getLevel(self, i):
        if (self.depths.__len__() > i):
            return self.depths[i]
        else:
            return None

    def setLevel(self, bid, ask, bidQty, askQty, bidQuoteId, askQuoteId, i):
        l = Level(bid, ask, bidQty, askQty, bidQuoteId, askQuoteId)
        self.depths[i] = l

    def setDirectLevel(self, l, i):
        self.depths[i] = l
