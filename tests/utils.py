import sys
import os
from antlr4 import *
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "build"))

from build.TyCLexer import TyCLexer
class Tokenizer:
    """Lexer wrapper for testing"""

    def __init__(self, source_code: str):
        self.source_code = source_code

    def get_tokens_as_string(self) -> str:
        """Get tokens as comma-separated string"""
        input_stream = InputStream(self.source_code)
        lexer = TyCLexer(input_stream)
        token_stream = CommonTokenStream(lexer)
        token_stream.fill()

        tokens = []
        for token in token_stream.tokens:
            if token.type != -1:  # EOF
                token_name = lexer.symbolicNames[token.type]
                token_text = token.text if token.text else ""
                tokens.append(f"{token_text}")

        tokens.append("EOF")
        return ",".join(tokens)


from build.TyCParser import TyCParser
from src.utils.error_listener import NewErrorListener
class Parser:
    """Parser wrapper for testing"""

    def __init__(self, source_code: str):
        self.source_code = source_code

    def parse(self) -> str:
        """Parse source code and return result"""
        input_stream = InputStream(self.source_code)
        lexer = TyCLexer(input_stream)
        token_stream = CommonTokenStream(lexer)
        parser = TyCParser(token_stream)
        parser.removeErrorListeners()
        parser.addErrorListener(NewErrorListener.INSTANCE)

        try:
            tree = parser.program()
            return "success"
        except Exception as e:
            return str(e)
from src.astgen.ast_generation import ASTGeneration
class ASTGenerator:
    """Class to generate AST from TyC source code."""

    def __init__(self, input_string: str):
        self.input_string = input_string
        self.input_stream = InputStream(input_string)
        self.lexer = TyCLexer(self.input_stream)
        self.token_stream = CommonTokenStream(self.lexer)
        self.parser = TyCParser(self.token_stream)
        self.parser.removeErrorListeners()
        self.parser.addErrorListener(NewErrorListener.INSTANCE)
        self.ast_generator = ASTGeneration()

    def generate(self):
        parse_tree = self.parser.program()
        ast = self.ast_generator.visit(parse_tree)
        return ast