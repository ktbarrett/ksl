# Kaleb's S\*\*\*\*y LISP

Attempt \#2 (see [old-master](https://github.com/ktbarrett/ksl/tree/old-master)).
Making improvements to the lexer/parser for supporting significant whitespace to remove some parens.
Added support for set and map literals, additional number literals, and better errors.


# Grammar

### Lexer

Rules with a `*` are emitted tokens.

Indention, Dedention, No-change-in-indentation tokens are listed;
however, because they are contextual no rule can be written for them.
When the lexer detects a newline, it:
1. skips the newline
2. starts a capture
3. reads any initial mixed whitespace
4. if the next character is a newline, abandon the current capture, repeat from step 1.
5. if the next character is a line comment, abandon the current capture, skip the comment, repeat from step 1.
6. if the capture has mixed indentation characters, or if the indentation characters don't match the current file's previously set indentation character, error
7. set the current file's indentation character to the character of the capture, if not already set
8. compare the number of characters in the capture against the previous indentation to judge if it's an indent, dedent, or neither

```
newline = "\n" | "\r" | "\r", "\n"
comment = "#", { -"\n" }
*indent = ...
*nodent = ...
*dedent = ...
identifier_char = "~" | "!" | "@" | "$" | "%" | "^" | "&" | "*" | "-" | "_" | "+" | "=" | "|" | "<" | ">" | "." | "/" | "?" | "a" .. "z" | "A" .. "Z" | "\", . | digit
identifier_prefix = "-" | "." | "-", "."
*identifier = identifier_prefix | [ identifier_prefix ], identifier_char - digit, { identifier_char }
hex_char = "0" .. "9" | "A" .. "F" | "a" .. "f"
hex = "0", ( "X" | "x" ), hex_char, { hex_char }
octal_char = "0" .. "7"
octal = "0", ( "O" | "o" ), octal_char, { octal_char }
binary_char "0" | "1"
binary = "0", ( "B" | "b" ), binary_char, { binary_char }
digit = "0" .. "9"
decimal = [ "-" ], digit, { digit }
*integer = decimal | hex | octal | binary
fractional = ".", { digit }
exponent = ( "E", "e" ), digit, { digit }
*float = decimal, ( fractional | exponent | fraction, exponent )
escape_char = "n" | "r" | "t" | "0" | "v" | "f" | """ | "'" | "\"
double_quote_string = """, { -( "\" | """ ) | "\", escape_char }, """
single_quote_string = "'", { -( "\" | "'" ) | "\", escape_char }, "'"
*string = double_quote_string | single_quote_string
*lparen = "("
*rparen = ")"
*lcurly = "{"
*rcurly = "}"
*lbracket = "["
*rbracket = "]"
*tick = "`"
*comma = ","
*colon = ":"
*semicolon = ";"
```

### Parser

The parser transforms infix expressions into prefix expressions (Polish notation) through the following set of rules:
* If an infix expression has 0, 1, or 2 elements, return that expression as is
* If an infix expression has 3 or more elements
    * Take the first 2 elements
    * Swap their order
    * Recursively apply these rules to the remaining elements and place the result in a sub-expression
* If a paren-delimited sub-expression is found
    * Recursively apply these rules to the content of the sub-expression
    * Return and treat the result as any other element in the greater expression

```
list = lbracket, { expr, comma }, rbracket
set = lcurly,  expr, comma, { expr, comma }, rcurly
map = lcurly, { expr, colon, expr, comma }, rcurly
value = list | set | map | identifier | integer | float | string
list_expr = lparen, { expr, [comma] }, rparen
expr = list_expr | value
line = expr, expr, { expr }, [semicolon],
paragraph = expr, { expr }, [colon], indent, block, { noident, block }, dedent
block = expr | line | paragraph
module = start, { noident, block }, end
```

