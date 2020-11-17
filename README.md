# ksl (Kaleb's Shitty LISP)

I have been meaning to learn LISP for a while.
I've read the first ~20 pages of SICP probably 4 times,
and watch a number of videos and read a number of articles on functional programming and LISP in particular.
Still I can't say that I "know" it.
So to make it more fun I decided to implement a LISP as a way to learn it.

__Warning__: ___I DON'T KNOW WHAT I'M DOING___

## Parser

A single-pass recursive-descent lexer/parser is easy to implement for LISP since the language is quite simple.
Parsing can be done separately with the `ksl.parse()` function which returns a simple AST representation of the source.

```
EXPR := ATOM | LIST
LIST := '(' {EXPR} ')'
ATOM := LITERAL | NAME
LITERAL := '\'' {!'\''} '\'' | '\"' {!'\"'} '\"'
NAME := {.}
```

As a convenience I made `NAME`s that parsed as integer and float literals be literal values of those types.
This was to avoid having a million `(int '123')` and be continuously confused as to why `(+ 123 456)` didn't work.
This might lead to some issues since misspelled literals become names: `1O23` or `123e.9`, etc.
However the trade-off is a positive one.

The parser uses a 2-char sliding window which is necessary to skip escaped quotes in string literals.
The number of possible syntax errors in quite small:

* two side by side expressions at the top-level: `1 2`
* unterminated list: `(+ 1 2`
* unterminated literal: `'example text`
* too many closing parens: `(+ 1 2))`
* missing whitespace between sub-expressions in a list `(+'abc'(g))`

These each have their own `SyntaxError` subclass since unterminated lists and literals are necessary for detecting multi-line expressions in the REPL.

## AST

There are 3 types in the AST: `ListExpression`, `Literal`, and `Name` that directly correlate with the elements of the language laid out above.
`ListExpression` is a list, `Literal` is a boxed immediate value of any type, and `Name` is an unresolved name.

Some Examples:

```
(+ 1 2)
=>
ListExpression((
  Name('+'),
  Literal(1),
  Literal(2)))
```

```
(def add3 (a b c) (+ a (+ b c)))
=>
ListExpression((
  Name('def'),
  Name('add3'),
  ListExpression((
    Name('a'),
    Name('b'),
    Name('c'))),
  ListExpression((
    Name('+'),
    Name('a'),
    ListExpression((
      Name('+'),
      Name('b'),
      Name('c')))))))
```

The AST is typically passed directly to the evaluator.

## Engine

A LISP is comprised of these things:
* values
* expressions
* names
* lexical scoping
* macros

### Values

Values are things like numbers, string, objects, functions, etc.
KSL is dynamically typed.
All Python types are available to KSL.

### Expressions

Expressions are represented by a list.
The first element of the list is treated as a function, and the remaining elements arguments to that function.
When expressions are evaluated the function is called with it's arguments and the result of the function is returned in place of the expression.
Expressions can be empty `()`, this evaluates to the value `None` and is not a syntax error.

### Names

Names are placeholders for values.
During the binding phase of evaluation they will be 'resolved', meaning the name will be replaced by the previously value bound to the name.

### Lexical Scoping

Name bindings are lexically scoped.
Multiple bindings to a name can exist, but only one per 'level' or 'scope'.
The 'closest' binding will be chosen when resolving a name.
A newer, more local, scope will be created on the entry into an list expression.

### Macros

Macros are functions which have the ability to add new name bindings to a scope and can modify expressions before their evaluation.
Macros can be a powerful metaprogramming tool, and are often used to define new syntax in LISP.
For example, the `def` macro allows a programmer to define functions in LISP and add them to the local scope.
This is different than a regular function since the sub expressions are not evaluated, but are manipulated literally in their AST form.
Macro function take in the entire list expression they are called in and return a new expression.

### Evaluation Order

This LISP is evaluated in normal-order in a 2 stage process: 'binding' and 'evaluation'.
Normal-order means that when evaluating a list expression the functions are called with the arguments un-evaluated.
The function will then only evaluate the arguments it needs to compute the result.
This also means name-value binding is actually a name-expression binding as all expressions are not evaluated until they are needed.

#### Binding

The expression tree is walked and `Name`s are resolved to the `ListExpression`s or `Literal`s that are bound to those names.
Macro functions are located and run at this time.
Macro function invocations happen by name only;
so unlike with functions where the first element of an expressions can be an expression that returns a function value,
macro function invocations must have the macro name be the first element of the list.
Binding in an expression occurs left to right, so names defined in one sub expression can be used in the next sub expression.

The result of the binding phase will be an un-evaluted expression using the same AST representation as the input,
but with no unresolved names in it.

#### Evaluation

`ListExpression`s are evaluated by calling the function in the list with the arguments from the list unevaluated.
The function arguments are bound to the parameter names and the function body goes through the `bind` stage to resolve all the uses of the parameters.
Then the resulting expression is evaluated.
Builtin functions are defined in Python and Python is not a normal-order evaluation language.
Builtin function must first evalute arguments before they use the value.
`Literal`s are evaluated by simply returning the values they store.

## Important builtins

## Scripting / REPL
