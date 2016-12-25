import quickfix as fix

class FixTools():
    def getHeader(self, msgType):
        request = fix.Message()
        request.getHeader().setField(fix.BeginString(fix.BeginString_FIXT11))
        request.getHeader().setField(fix.MsgType(msgType))
        request.getHeader().setField(fix.SenderCompID("SERVER"))
        request.getHeader().setField(fix.TargetCompID("CLIENT"))
        return request