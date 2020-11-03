from .engine import Expression, Scope, MacroFunctionType


builtin_variables = Scope[Expression]()

builtin_macros = Scope[MacroFunctionType]()
