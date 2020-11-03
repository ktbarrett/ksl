from typing import Any, Union, Protocol, Dict, List, TypeVar, Callable, Optional


MacroFunctionType = Callable[['ListExpression'], 'Expression']


T = TypeVar('T')


def eval(
    expr: 'Expression',
    variable_scope: Optional['Scope[Expression]'] = None,
    macro_scope: Optional['Scope[MacroFunctionType]'] = None
) -> Any:
    """
    """
    if variable_scope is None:
        from .builtins import builtin_variables as variable_scope
    if macro_scope is None:
        from .builtins import builtin_macros as macro_scope
    bound = expr.bind(variable_scope, macro_scope)
    return bound.eval()


class Expression(Protocol[T]):
    """
    The fundamental element of computation in a LISP.

    All elements of a LISP program are either an expression or a syntactic form (a macro).
    Expressions are evaluated in two steps: bind() and eval().
    The bind() step exists to resolve all names in an expression by replacing them with the
    expression they are bound to.
    In the bind() step, macro functions, which allow the user to define new name bindings
    and create new syntax are also run.
    At the end of the bind() step, all names should be resolved.
    In the eval() step the expressions are evaluated by interpreting list expressions as
    function calls with arguments.
    The result of the function call is returned to the enclosing list expression until
    it exists the top-level expression returning a result to the user.
    eval() can
    """

    def bind(self, variable_scope: 'Scope[Expression]', macro_scope: 'Scope[MacroFunctionType]') -> 'Expression[T]':
        """
        Replaces instances of Name with a bound expression and runs macro functions.

        Macro functions can define new names and transform expressions allowing new
        syntaxes to be defined.
        bind() can be run on any expression, and if run more than once on the same expression
        with the same arguments, is effectively a no-op.
        """

    def eval(self) -> T:
        """
        Executed an expression that has been bound.

        List Expression encode function calls and arguments to those functions.
        The eval() step calls those functions and folds an expression tree into a single value.
        If an unbound name is seen, an error is raised.
        eval() can only be run safely on expressions where all names have been resolved.
        Running eval() on the same expression will return the same argument if and only if
        the expression is pure.
        """


class Scope(Dict[str, T]):
    """
    A stack of namespaces

    New names are added to the current namespace.
    Names are retrieved starting at the current namespace and travelling
    upwards through the parents until the name is found.
    If no name is found on retrieval, throws NameError.
    """

    def __init__(self, parent: Union[None, 'Dict[str, T]'] = None):
        super().__init__()
        self._parent = parent

    @property
    def parent(self) -> Union[None, 'Dict[str, T]']:
        return self._parent

    def __getitem__(self, item: str) -> T:
        if item in self:
            return super().__getitem__(item)
        elif self._parent is not None:
            return self._parent[item]
        raise NameError(f"Name '{item}' not in scope")


class Literal(Expression[T]):
    """
    A expression for literal values

    Since this object already has a value, bind() does nothing,
    and eval() simply returns the value.
    """

    def __init__(self, value: T, **info: Any):
        self._value = value
        self._info = info

    @property
    def value(self) -> T:
        return self._value

    @property
    def info(self) -> Dict[str, Any]:
        return self._info

    def bind(self, variable_scope: Scope[Expression], macro_scope: Scope[MacroFunctionType]) -> Expression:
        return self

    def eval(self) -> T:
        return self._value


class Name(str, Expression[Any]):
    """
    An expression for names to be resolved later

    This is a placeholder for a value that will be resolved later in the bind() step.
    Names should not exist after the bind() step, so eval()ing a Name raises a RuntimeError.
    """

    def __new__(cls, name: str, **info: Any):
        s = str.__new__(cls, name)
        s._info = info
        return s

    @property
    def info(self) -> Dict[str, Any]:
        return self._info

    def bind(self, variable_scope: Scope[Expression], macro_scope: Scope[MacroFunctionType]) -> Expression:
        return variable_scope[self]

    def eval(self) -> Any:
        raise RuntimeError("Attempted evaluating unbound name")


class Parameter(Name):
    """
    A name that is captured by a function

    Functions definition adds these to the scope during the bind() step
    where they are mapped to function parameter names.
    Function objects hold a reference to a parameter and bind an expression when the
    function is invoked.
    When eval()ed, the parameter acts as a proxy for the bound expression.
    """

    def set_value(self, value: Expression) -> None:
        self._value = value

    def eval(self) -> Any:
        return self._value.eval()


class ListExpression(tuple, Expression):
    """
    A ListExpression encodes a function or macro call on arguments.

    During bind(), if the first element of a list expression is a macro function,
    the macro is executed on the unbound expression list transforming it into another
    expression list.
    Then the resulting expression runs through bind() in case it is not fully bound.
    During eval(), the first element of a list expression is considered a function,
    The first value in the list is eval()ed and then the remaining unevaluated args
    are passed to the function and the resulting value returned.
    """

    def __new__(cls, sub_expressions: List[Expression], **info: Any):
        if not sub_expressions:
            raise ValueError("List expressions cannot be empty")
        s = tuple.__new__(cls, sub_expressions)
        s._info = info
        return s

    @property
    def info(self) -> Dict[str, Any]:
        return self._info

    def bind(self, variable_scope: Scope[Expression], macro_scope: Scope[MacroFunctionType]) -> Expression:
        if len(self) >= 1:
            func = self[0]
            if isinstance(func, Name) and func in macro_scope:
                macro = macro_scope[func]
                changed = macro(self)
                return changed.bind(variable_scope, macro_scope)
        return ListExpression(
            expr.bind(variable_scope, macro_scope)
            for expr in self)

    def eval(self) -> Any:
        func, *args = self
        func = func.eval()
        res = func(args)
        return res
