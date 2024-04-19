import sys
from lex import *


class Parser:
    def __init__(self, lexer, emitter):
        self.lexer = lexer
        self.emitter = emitter

        self.symbols = set()
        self.labelsDeclared = set()
        self.labelsGotoed = set()

        self.curToken = None
        self.peekToken = None
        self.nextToken()
        self.nextToken()

    def checkToken(self, kind):
        result = kind == self.curToken.kind
        print(
            f"Checking Token: Expected {kind}, got {self.curToken.kind}, Result: {result}"
        )
        return result

    def checkPeek(self, kind):
        return kind == self.peekToken.kind

    def match(self, kind):
        print(f"Attempting to match: {kind} with Current Token: {self.curToken.kind}")
        if not self.checkToken(kind):
            self.abort("Expected " + kind.name + ", got " + self.curToken.kind.name)
        self.nextToken()

    def nextToken(self):
        self.curToken = self.peekToken
        self.peekToken = self.lexer.getToken()

    def isComparisonOperator(self):
        return (
            self.checkToken(TokenType.GT)
            or self.checkToken(TokenType.GTEQ)
            or self.checkToken(TokenType.LT)
            or self.checkToken(TokenType.LTEQ)
            or self.checkToken(TokenType.EQEQ)
            or self.checkToken(TokenType.NOTEQ)
        )

    def abort(self, message):
        sys.exit("Error! " + message)

    # program ::= {statement}
    def program(self):
        self.emitter.headerLine("#include <stdio.h>")
        self.emitter.headerLine("int main(void){")

        while self.checkToken(TokenType.NEWLINE):
            self.nextToken()

        while not self.checkToken(TokenType.EOF):
            self.statement()

        self.emitter.emitLine("return 0;")
        self.emitter.emitLine("}")

        for label in self.labelsGotoed:
            if label not in self.labelsDeclared:
                self.abort("Attempting to GOTO to undeclared label: " + label)

    def statement(self):
        # "PRINT" (expression | string)
        print(
            f"Handling statement for Token: {self.curToken.text}, Type: {self.curToken.kind}"
        )
        if self.checkToken(TokenType.PRINT):
            self.nextToken()

            if self.checkToken(TokenType.STRING):
                self.emitter.emitLine('printf("' + self.curToken.text + '\\n");')
                self.nextToken()

            else:
                self.emitter.emit('printf("%' + '.2f\\n", (float)(')
                self.expression()
                self.emitter.emitLine("));")

        # "IF" comparison "THEN" block "ENDIF"
        elif self.checkToken(TokenType.IF):
            self.nextToken()
            self.emitter.emit("if(")
            self.comparison()

            self.match(TokenType.THEN)
            self.nl()
            self.emitter.emitLine("){")

            while not self.checkToken(TokenType.ENDIF):
                self.statement()

            self.match(TokenType.ENDIF)
            self.emitter.emitLine("}")

        # "WHILE" comparison "REPEAT" block "ENDWHILE"
        elif self.checkToken(TokenType.WHILE):
            self.nextToken()
            self.emitter.emit("while(")
            self.comparison()

            self.match(TokenType.REPEAT)
            self.nl()
            self.emitter.emitLine("){")

            while not self.checkToken(TokenType.ENDWHILE):
                self.statement()

            self.match(TokenType.ENDWHILE)
            self.emitter.emitLine("}")

        # "LABEL" ident
        elif self.checkToken(TokenType.LABEL):
            self.nextToken()

            if self.curToken.text in self.labelsDeclared:
                self.abort("Label already exists: " + self.curToken.text)
            self.labelsDeclared.add(self.curToken.text)

            self.emitter.emitLine(self.curToken.text + ":")
            self.match(TokenType.IDENT)

        # "GOTO" ident
        elif self.checkToken(TokenType.GOTO):
            self.nextToken()
            self.labelsGotoed.add(self.curToken.text)
            self.emitter.emitLine("goto " + self.curToken.text + ";")
            self.match(TokenType.IDENT)

        # "LET" ident = expression
        elif self.checkToken(TokenType.LET):
            self.nextToken()

            if self.curToken.text not in self.symbols:
                self.symbols.add(self.curToken.text)
                self.emitter.headerLine("float " + self.curToken.text + ";")

            self.emitter.emit(self.curToken.text + " = ")
            self.match(TokenType.IDENT)
            self.match(TokenType.EQ)

            self.expression()
            self.emitter.emitLine(";")

        # "INPUT" ident
        elif self.checkToken(TokenType.INPUT):
            self.nextToken()

            if self.curToken.text not in self.symbols:
                self.symbols.add(self.curToken.text)
                self.emitter.headerLine("float " + self.curToken.text + ";")

            self.emitter.emitLine(
                'if(0 == scanf("%' + 'f", &' + self.curToken.text + ")) {"
            )
            self.emitter.emitLine(self.curToken.text + " = 0;")
            self.emitter.emit('scanf("%')
            self.emitter.emitLine('*s");')
            self.emitter.emitLine("}")
            self.match(TokenType.IDENT)

        elif self.checkToken(TokenType.CLASS):
            self.parse_class()

        else:
            self.abort(
                "Invalid statement at "
                + self.curToken.text
                + " ("
                + self.curToken.kind.name
                + ")"
            )

        self.nl()

    # comparison ::= expression (("==" | "!=" | ">" | ">=" | "<" | "<=") expression)+
    def comparison(self):
        self.expression()
        if self.isComparisonOperator():
            self.emitter.emit(self.curToken.text)
            self.nextToken()
            self.expression()
        while self.isComparisonOperator():
            self.emitter.emit(self.curToken.text)
            self.nextToken()
            self.expression()

    # expression ::= term {( "-" | "+" ) term}
    def expression(self):
        self.term()
        while self.checkToken(TokenType.PLUS) or self.checkToken(TokenType.MINUS):
            self.emitter.emit(self.curToken.text)
            self.nextToken()
            self.term()

    # term ::= unary {( "/" | "*" ) unary}
    def term(self):
        self.unary()
        while self.checkToken(TokenType.ASTERISK) or self.checkToken(TokenType.SLASH):
            self.emitter.emit(self.curToken.text)
            self.nextToken()
            self.unary()

    # unary ::= ["+" | "-"] primary
    def unary(self):
        if self.checkToken(TokenType.PLUS) or self.checkToken(TokenType.MINUS):
            self.emitter.emit(self.curToken.text)
            self.nextToken()
        self.primary()

    # primary ::= number | ident
    def primary(self):
        if self.checkToken(TokenType.NUMBER):
            self.emitter.emit(self.curToken.text)
            self.nextToken()
        elif self.checkToken(TokenType.IDENT):
            if self.curToken.text not in self.symbols:
                self.abort(
                    "Referencing variable before assignment: " + self.curToken.text
                )

            self.emitter.emit(self.curToken.text)
            self.nextToken()
        else:
            self.abort("Unexpected token at " + self.curToken.text)

    # nl ::= '\n'+
    def nl(self):
        self.match(TokenType.NEWLINE)
        while self.checkToken(TokenType.NEWLINE):
            self.nextToken()

    def parse_class(self):
        self.match(TokenType.CLASS)  # Already matched CLASS and moved next
        class_name = self.curToken.text
        self.nextToken()  # Move past the class name identifier
        self.emitter.startStruct(class_name)  # Start struct definition

        while not self.checkToken(TokenType.ENDCLASS):
            if self.checkToken(TokenType.NEWLINE):
                self.nextToken()  # Skip newlines within class definitions
                continue
            elif self.checkToken(TokenType.VARIABLE):
                self.nextToken()  # Move past the VARIABLE keyword
                if not self.checkToken(TokenType.IDENT):
                    self.abort("Variable name expected after VARIABLE keyword")
                var_name = self.curToken.text
                self.nextToken()  # Move past the variable name
                self.emitter.emitLine(f"    float {var_name};")  # Emit struct member
            else:
                self.abort("Only variable declarations are allowed inside classes")

        self.match(TokenType.ENDCLASS)
        self.emitter.endStruct()  # Close struct definition

    def parse_variable_declaration(self):
        self.match(TokenType.VARIABLE)
        var_name = self.curToken.text
        self.match(TokenType.IDENT)
        self.register_variable(var_name)
