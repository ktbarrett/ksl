# Kaleb's S\*\*\*\*y LISP

Attempt \#2 (see [old-master](https://github.com/ktbarrett/ksl/tree/old-master)).
Making improvements to the lexer/parser for supporting significant whitespace to remove some parens.
Added support for set and map literals, additional number literals, and better errors.


# Grammar

### Lexer

Rules with a `*` are emitted tokens.

Indention and Dedention tokens are listed, but because they are contextual no rule can be written for them.
When the lexer detects a newline, it:
1. skips the newline
2. starts a capture
3. reads any initial mixed whitespace
4. if the next character is a newline, abandon the current capture, repeat from step 1.
5. if the next character is a line comment, abandon the current capture, skip the comment, repeat from step 1.
6. if the capture has mixed indentation characters, or if the indentation characters don't match the current file's previously set indentation character, error
7. set the current file's indentation character to the character of the capture, if not already set
8. compare the number of characters in the capture against the previous indentation to judge if it's an indent or a dedent

```
newline = "\n" | "\r" | "\r", "\n"
comment = "#", { -"\n" }
*indent = ...
*dedent = ...
identifier_start_char = "~" | "!" | "@" | "$" | "%" | "^" | "&" | "*" | "-" | "_" | "+" | "=" | "|" | "<" | ">" | "." | "/" | "?" | "a" .. "z" | "A" .. "Z" | "\", .
identifier_rest_char = identifier_start_char | digit
*identifier = "-" | [ "-" ], identifier_start_char, { identifier_rest_char }
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
*list_end = ")"
*set_start = "{"
*set_end = "}"
*map_start = "["
*map_end = "]"
*tick = "`"
*comma = ","
*colon = ":"
*semicolon = ";"
```

### Parser

```
list = list_start, { expr, [ comma ] }, list_end
set = set_start, { expr, [ comma ] }, set_end
map = map_start, { expr, colon, expr, [ comma ] }, map_end
expr = identifier | integer | float | string | list | set | map
line = ( list | expr, expr, {expr} ), [ semicolon ]
paragraph = expr, {expr}, [ colon ], indent, ( line | paragraph ), { line | paragraph }, dedent
program = { line | paragraph }, $
```
