class Emitter:
    def __init__(self, fullPath):
        self.fullPath = fullPath
        self.header = ""
        self.code = ""

    def emit(self, code):
        self.code += code

    def emitLine(self, code):
        self.code += code + "\n"

    def headerLine(self, code):
        self.header += code + "\n"

    def startStruct(self, name):
        self.emitLine(f"struct {name} {{")

    def endStruct(self):
        self.emitLine("};")

    def writeFile(self):
        with open(self.fullPath, "w") as outputFile:
            outputFile.write(self.header + self.code)
