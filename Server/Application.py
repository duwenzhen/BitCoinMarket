import json
from urllib2 import urlopen

import quickfix as fix
import quickfix50sp2 as fix50sp2

import Tools
from Tools import FixTools


class Application(fix.Application):
    def __init__(self):
        super(Application, self).__init__()
        self.dicoRicSession = {}
        self.fixTools = FixTools.FixTools()
    def onCreate(self, sessionID):
        self.sessionID = sessionID
        print ("Application created - session: " + sessionID.toString())

    def onLogon(self, sessionID):
        print "Logon", sessionID

    def onLogout(self, sessionID):
        print "Logout", sessionID

    def toAdmin(self, message, sessionID):
        pass

    def fromAdmin(self, message, sessionID):
        pass

    def fromApp(self, message, sessionID):
        self.onMessage(message, sessionID)
        print "IN", message

    def toApp(self, message, sessionID):
        print "OUT", message

    def run(self):
        print '''
	input 1 to quit
	'''
        while True:
            input = raw_input()
            if input == '1':
                break
            elif input == 'p':
                self.sendPrice()
            else:
                continue

    def onMessage(self, message, sessionID):
        msgType = fix.MsgType()
        message.getHeader().getField(msgType)
        if (msgType.getValue() == "V"):
            fReqId = fix.MDReqID()
            message.getField(fReqId)
            fSubReqType = fix.SubscriptionRequestType()
            message.getField(fSubReqType)
            fMarketDepth = fix.MarketDepth()
            message.getField(fMarketDepth)
            fMdUpdateType = fix.MDUpdateType()
            message.getField(fMdUpdateType)
            fNoMDEntryTypes = fix.NoMDEntryTypes()
            message.getField(fNoMDEntryTypes)

            for i in xrange(fNoMDEntryTypes.getValue()):
                mdReqGroup = fix50sp2.MarketDataRequest().NoMDEntryTypes()
                message.getGroup(i+1, mdReqGroup)
                mdEntryType = fix.MDEntryType()
                mdReqGroup.getField(mdEntryType)

            fNoRelatedSym = fix.NoRelatedSym()
            message.getField(fNoRelatedSym)


            for i in xrange(fNoRelatedSym.getValue()):
                instrMdReqGroup = fix50sp2.MarketDataRequest().NoRelatedSym()
                message.getGroup(i+1,instrMdReqGroup)
                fSymbol = fix.Symbol()
                instrMdReqGroup.getField(fSymbol)
                fCFICode = fix.CFICode()
                instrMdReqGroup.getField(fCFICode)

                currency = fix.Currency()
                instrMdReqGroup.getField(currency)

                fSettlType = fix.SettlType()
                instrMdReqGroup.getField(fSettlType)
                fMdStreamID = fix.MDStreamID()
                instrMdReqGroup.getField(fMdStreamID)
                if (self.dicoRicSession.has_key(fSymbol.getString())):
                    self.dicoRicSession[fSymbol.getString()].append((sessionID, fReqId.getString()))
                else:
                    self.dicoRicSession[fSymbol.getString()] = [(sessionID, fReqId.getString())]




    def queryEnterOrder(self):
        print ("\nTradeCaptureReport (AE)\n")





    def createMDMessage(self, orderBook, reqId):
        message = self.fixTools.getHeader(fix.MsgType_MarketDataSnapshotFullRefresh)
        message.setField(fix.MarketDepth(0))
        message.setField(fix.MDReqID(reqId))
        ###instrument
        message.setField(fix.Symbol(orderBook.ric))
        message.setField(fix.CFICode("I"))
        ###instrument

        message.setField(fix.LastUpdateTime())

        noMDEntriesGroup = fix50sp2.MarketDataIncrementalRefresh.NoMDEntries()
        position = 0
        for l in orderBook.depths:
            position= position + 1
            #bid
            noMDEntriesGroup.setField(fix.MDEntryType(fix.MDEntryType_BID))
            noMDEntriesGroup.setField(fix.MDEntryPx(l.bid))
            noMDEntriesGroup.setField(fix.MDEntrySize(l.bidQty))
            noMDEntriesGroup.setField(fix.QuoteCondition('A'))
            noMDEntriesGroup.setField(fix.Currency("USD"))
            noMDEntriesGroup.setField(fix.SettlType("0"))
            noMDEntriesGroup.setField(fix.QuoteEntryID(l.bidQuoteId))
            noMDEntriesGroup.setField(fix.MDEntryPositionNo(position))
            message.addGroup(noMDEntriesGroup)

            #ask
            noMDEntriesGroup.setField(fix.MDEntryType(fix.MDEntryType_OFFER))
            noMDEntriesGroup.setField(fix.MDEntryPx(l.ask))
            noMDEntriesGroup.setField(fix.MDEntrySize(l.askQty))
            noMDEntriesGroup.setField(fix.QuoteCondition('A'))
            noMDEntriesGroup.setField(fix.Currency("USD"))
            noMDEntriesGroup.setField(fix.SettlType("0"))
            noMDEntriesGroup.setField(fix.QuoteEntryID(l.askQuoteId))
            noMDEntriesGroup.setField(fix.MDEntryPositionNo(position))
            message.addGroup(noMDEntriesGroup)
        return message

    def getOrderBook(self, ric):
        orderBook = Tools.ToolsCommon.OrderBook(ric, 1)

        url = "https://api.coindesk.com/v1/bpi/currentprice.json"
        donnee = urlopen(url).read().decode('utf8')

        data = json.loads(donnee)
        xbtusd = data["bpi"]["USD"]["rate"]
        orderBook.setLevel(float(xbtusd) - 1, float(xbtusd) + 1, 100, 100, "bidquoteid","askquoteid", 0)

        return orderBook

    def sendPrice(self):

        orderBook = self.getOrderBook("xau")
        sessionList = self.dicoRicSession["xau"]
        for (session, reqId) in sessionList:
            message = self.createMDMessage(orderBook, reqId)
            fix.Session.sendToTarget(message, session)