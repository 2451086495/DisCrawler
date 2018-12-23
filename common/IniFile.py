#encoding=utf-8

class IniFile():
    def __init__(self, filename):
        try:
            self.iniFile = open(filename, 'r')
        except IOError as e:
            print 'open ini file %s failed : %s' % (filename,e)
            return

        self.data = {}
        modelName = ""
        for line in self.iniFile.readlines():
            pos = line.find("#")
            if pos != -1:
                line = line[:pos]
            line = line.strip()
            if len(line) < 3:
                continue
            if line[0] == '[' and line[-1] == ']':
                modelName = line[1:-1]
                self.data[modelName] = {}
                continue
            pos = line.find("=")
            if pos != -1:
                self.data[modelName][line[:pos].strip()] = line[pos + 1:].strip()
        if self.data.has_key(''):
            del self.data['']

        self.outData = {}

    def GetData(self, modelName, para, default=''):
        if self.data.has_key(modelName) and self.data[modelName].has_key(para):
            return self.data[modelName][para]
        return default

    def PutData(self, modelName, para, value):
        self.outData[modelName][para] = value;

    def GetMode(self, modelName):
        if self.data.has_key(modelName):
            return self.data[modelName]
        return {}

    def FlushData(self, fileName):
        try:
            file = open(fileName, "w+")
        except IOError:
            print 'FlushData: open %s failed' % fileName
            return

        outStr = ""
        for key, val in self.outData.items():
            outStr  += "\n[%s]\n" % key
            for key, val in self.outData[key].items():
                outStr += "%s=%s\n" % (key, val)
        file.write(outStr)
        file.close()
