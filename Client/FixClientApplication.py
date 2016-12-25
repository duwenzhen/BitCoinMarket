import sys
import os
import time
import thread
import quickfix as fix
from datetime import datetime
import cPickle as p
import json
from urllib2 import urlopen
import Tools
import quickfix50sp2 as fix50sp2


class FixClientApplication(fix.Application):

    def __init__(self, socketio):
        super(FixClientApplication,self).__init__()
        self.socketio = socketio
        self.generator = Tools.ToolsCommon.Generator()
        self.fixTools = Tools.FixTools.FixTools()

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

    def marketDataRequest(self, ric):
        request = self.fixTools.getHeader(fix.MsgType_MarketDataRequest)
        reqId = self.generator.id_generator()
        request.setField(fix.MDReqID(reqId))
        request.setField(fix.SubscriptionRequestType(fix.SubscriptionRequestType_SNAPSHOT_PLUS_UPDATES))
        request.setField(fix.MarketDepth(0))
        request.setField(fix.MDUpdateType(fix.MDUpdateType_FULL_REFRESH))
        mdReqGroup = fix50sp2.MarketDataRequest().NoMDEntryTypes()
        mdReqGroup.setField(fix.MDEntryType(fix.MDEntryType_BID))
        request.addGroup(mdReqGroup)
        mdReqGroup.setField(fix.MDEntryType(fix.MDEntryType_OFFER))
        request.addGroup(mdReqGroup)

        instrMdReqGroup = fix50sp2.MarketDataRequest().NoRelatedSym()

        ###instrument
        instrMdReqGroup.setField(fix.Symbol(str(ric)))
        instrMdReqGroup.setField(fix.CFICode("I"))
        ###instrument

        instrMdReqGroup.setField(fix.Currency("USD"))
        instrMdReqGroup.setField(fix.SettlType("0"))
        instrMdReqGroup.setField(fix.MDStreamID("GOLD"))
        request.addGroup(instrMdReqGroup)
        fix.Session.sendToTarget(request, self.sessionID)

    def run(self):
        count = 0
        while True:
            self.socketio.sleep(5)
            count += 1

            url = "https://api.coindesk.com/v1/bpi/currentprice.json"
            donnee = urlopen(url).read().decode('utf8')

            data = json.loads(donnee)
            xbtusd = data["bpi"]["USD"]["rate"]
            self.socketio.emit('level',
                          {'data': '100: %.4f:%.4f :100' % (float(xbtusd) - 1, float(xbtusd) + 1), 'count': count},
                          room='xau',
                          namespace='/test')



    def onMessage(self, message, sessionID):
        print "OnMessage %s" % message
        print "ici------------------ %s" % message
        msgType = fix.MsgType()
        message.getHeader().getField(msgType)
        if (msgType.getValue() == "W"):
            print "MarketDataSnapshotFullRefresh %s" % message
            fMarketDepth = fix.MarketDepth()
            message.getField(fMarketDepth)
            fMDReqID= fix.MDReqID()
            message.getField(fMDReqID)
            fSymbol = fix.Symbol()
            message.getField(fSymbol)
            fCFICode = fix.CFICode()
            message.getField(fCFICode)
            fLastUpdateTime = fix.LastUpdateTime()
            message.getField(fLastUpdateTime)

            fNoMDEntries = fix.NoMDEntries()
            message.getField(fNoMDEntries)

            orderBook = Tools.ToolsCommon.OrderBook(fSymbol.getString(), fNoMDEntries.getValue() / 2)
            fNoMDEntriesGroup = fix50sp2.MarketDataIncrementalRefresh.NoMDEntries()
            for i in xrange(fNoMDEntries.getValue()):
                message.getGroup(i + 1, fNoMDEntriesGroup)
                fMDEntryType = fix.MDEntryType()
                fNoMDEntriesGroup.getField(fMDEntryType)
                fMDEntryPx = fix.MDEntryPx()
                fNoMDEntriesGroup.getField(fMDEntryPx)
                fMDEntrySize= fix.MDEntrySize()
                fNoMDEntriesGroup.getField(fMDEntrySize)
                fQuoteCondition= fix.QuoteCondition()
                fNoMDEntriesGroup.getField(fQuoteCondition)
                fCurrency= fix.Currency()
                fNoMDEntriesGroup.getField(fCurrency)
                fSettlType= fix.SettlType()
                fNoMDEntriesGroup.getField(fSettlType)
                fQuoteEntryID= fix.QuoteEntryID()
                fNoMDEntriesGroup.getField(fQuoteEntryID)
                fMDEntryPositionNo = fix.MDEntryPositionNo()
                fNoMDEntriesGroup.getField(fMDEntryPositionNo)
                if (fMDEntryType.getString() == fix.MDEntryType_BID):
                    l = orderBook.getLevel(fMDEntryPositionNo.getValue() - 1)
                    if (l == None):
                        l = Tools.ToolsCommon.Level(fMDEntryPx.getValue(), 0, fMDEntrySize.getValue(),0, fQuoteEntryID.getValue(), "")
                    else:
                        l.bid = fMDEntryPx.getValue()
                        l.bidQty= fMDEntrySize.getValue()
                        l.bidQuoteId = fQuoteEntryID.getString()
                    orderBook.setDirectLevel(l, fMDEntryPositionNo.getValue() - 1)
                else:
                    l = orderBook.getLevel(fMDEntryPositionNo.getValue() - 1)
                    if (l == None):
                        l = Tools.ToolsCommon.Level(0, fMDEntryPx.getValue(), 0, fMDEntrySize.getValue(), "", fQuoteEntryID.getValue())
                    else:
                        l.ask = fMDEntryPx.getValue()
                        l.askQty = fMDEntrySize.getValue()
                        l.askQuoteId = fQuoteEntryID.getString()
                    orderBook.setDirectLevel(l, fMDEntryPositionNo.getValue() - 1)
            print "orderbook"

            self.display(orderBook, fLastUpdateTime.getString())


    def display(self, orderBook, lastUpdateTime):
        l = None
        for i in xrange(orderBook.getDepth()):
             l = orderBook.getLevel(i)
        self.socketio.emit('level',
                           {'data': '%.4f: %.4f:%.4f :%.4f' % (l.bidQty, l.bid, l.ask, l.askQty), 'count': lastUpdateTime},
                           room=orderBook.ric,
                           namespace='/test')

    def queryEnterOrder(self):
        print ("\nTradeCaptureReport (AE)\n")

