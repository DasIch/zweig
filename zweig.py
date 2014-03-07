# coding: utf-8
"""
    zweig
    ~~~~~

    :copyright: 2014 by Daniel Neuhäuser
    :license: BSD, see LICENSE.rst for details
"""
from __future__ import unicode_literals
import os
import sys
import ast
from io import StringIO
from contextlib import contextmanager
from itertools import chain
from functools import reduce


PY2 = sys.version_info[0] == 2


def walk_preorder(tree):
    """
    Yields the nodes in the `tree` in preorder.
    """
    yield tree
    for child in ast.iter_child_nodes(tree):
        for descendent in walk_preorder(child):
            yield descendent


def to_source(tree):
    """
    Returns the Python source code representation of the `tree`.
    """
    writer = _SourceWriter()
    writer.visit(tree)
    return writer.output.getvalue()


class _SourceWriter(ast.NodeVisitor):
    def __init__(self):
        self.output = StringIO()
        self.indentation_level = 0
        self.newline = True

    @contextmanager
    def indented(self):
        self.indentation_level += 1
        try:
            yield
        finally:
            self.indentation_level -= 1

    def write(self, source):
        if self.newline:
            self.newline = False
            self.write_indentation()
        self.output.write(source)

    def write_indentation(self):
        self.write('    ' * self.indentation_level)

    def write_newline(self):
        if self.newline:
            self.newline = False
        self.write('\n')
        self.newline = True

    def write_line(self, source):
        self.write(source)
        self.write_newline()

    def write_identifier(self, identifier):
        if PY2:
            self.write(identifier.decode('ascii'))
        else:
            self.write(identifier)

    def write_repr(self, obj):
        if PY2:
            self.write(repr(obj).decode('ascii'))
        else:
            self.write(repr(obj))

    def writing_comma_separated(self, items):
        if items:
            for item in items[:-1]:
                yield item
                self.write(', ')
            yield items[-1]

    def write_comma_separated_nodes(self, nodes):
        for node in self.writing_comma_separated(nodes):
            self.visit(node)

    @contextmanager
    def writing_statement(self):
        yield
        self.write_newline()

    def visit_statements(self, statements):
        for statement in statements[:-1]:
            self.visit(statement)
            if isinstance(statement, (ast.FunctionDef, ast.ClassDef)):
                self.write_newline()
        self.visit(statements[-1])

    def visit_Module(self, node):
        self.visit_statements(node.body)

    def visit_FunctionDef(self, node):
        for decorator in node.decorator_list:
            self.write('@')
            self.visit(decorator)
            self.write_newline()
        self.write('def ')
        self.write_identifier(node.name)
        self.write('(')
        self.visit(node.args)
        self.write(')')
        if not PY2 and node.returns is not None:
            self.write(' -> ')
            self.visit(node.returns)
        self.write(':')
        self.write_newline()
        with self.indented():
            self.visit_statements(node.body)

    def visit_ClassDef(self, node):
        for decorator in node.decorator_list:
            self.write('@')
            self.visit(decorator)
            self.write_newline()
        self.write('class ')
        self.write_identifier(node.name)
        if (
            node.bases or
            (not PY2 and (node.keywords or node.starargs or node.kwargs))
        ):
            self.write('(')
            self.write_comma_separated_nodes(node.bases)
            if not PY2:
                if node.keywords:
                    if node.bases:
                        self.write(', ')
                    self.write_comma_separated_nodes(node.keywords)
                if node.starargs is not None:
                    if node.bases or node.keywords:
                        self.write(', ')
                    self.write('*')
                    self.visit(node.starargs)
                if node.kwargs is not None:
                    if node.bases or node.keywords or node.starargs:
                        self.write(', ')
                    self.write('**')
                    self.visit(node.kwargs)
            self.write(')')
        self.write(':')
        self.write_newline()
        with self.indented():
            self.visit_statements(node.body)

    def visit_Return(self, node):
        with self.writing_statement():
            self.write('return')
            if node.value:
                self.write(' ')
                self.visit(node.value)

    def visit_Delete(self, node):
        with self.writing_statement():
            self.write('del ')
            self.write_comma_separated_nodes(node.targets)

    def visit_Assign(self, node):
        with self.writing_statement():
            for target in node.targets:
                self.visit(target)
                self.write(' = ')
            self.visit(node.value)

    def visit_AugAssign(self, node):
        with self.writing_statement():
            self.visit(node.target)
            self.write(' ')
            self.visit(node.op)
            self.write('= ')
            self.visit(node.value)

    if PY2:
        def visit_Print(self, node):
            with self.writing_statement():
                self.write('print')
                if node.values:
                    self.write(' ')
                    self.write_comma_separated_nodes(node.values)
                if not node.nl:
                    self.write(',')

    def visit_For(self, node):
        self.write('for ')
        self.visit(node.target)
        self.write(' in ')
        self.visit(node.iter)
        self.write(':')
        self.write_newline()
        with self.indented():
            self.visit_statements(node.body)
        if node.orelse:
            self.write_line('else:')
            with self.indented():
                self.visit_statements(node.orelse)

    def visit_While(self, node):
        self.write('while ')
        self.visit(node.test)
        self.write(':')
        self.write_newline()
        with self.indented():
            self.visit_statements(node.body)
        if node.orelse:
            self.write_line('else:')
            with self.indented():
                self.visit_statements(node.orelse)

    def visit_If(self, node):
        self.write('if ')
        self.visit(node.test)
        self.write(':')
        self.write_newline()
        with self.indented():
            self.visit_statements(node.body)
        if node.orelse:
            self.write_line('else:')
            with self.indented():
                self.visit_statements(node.orelse)

    def visit_With(self, node):
        self.write('with ')
        if PY2:
            self.visit(node.context_expr)
            if node.optional_vars:
                self.write(' as ')
                self.visit(node.optional_vars)
        else:
            self.write_comma_separated_nodes(node.items)
        self.write(':')
        self.write_newline()
        with self.indented():
            self.visit_statements(node.body)

    def visit_Raise(self, node):
        with self.writing_statement():
            self.write('raise')
            if PY2:
                if node.type is not None:
                    self.write(' ')
                    self.visit(node.type)
                if node.inst is not None:
                    self.write(', ')
                    self.visit(node.inst)
                if node.tback is not None:
                    self.write(', ')
                    self.visit(node.tback)
            else:
                if node.exc is not None:
                    self.write(' ')
                    self.visit(node.exc)
                if node.cause is not None:
                    self.write(' from ')
                    self.visit(node.cause)

    def visit_Try(self, node):
        self.write_line('try:')
        with self.indented():
            self.visit_statements(node.body)
        for excepthandler in node.handlers:
            self.visit(excepthandler)
        if node.orelse:
            self.write_line('else:')
            with self.indented():
                self.visit_statements(node.orelse)
        if node.finalbody:
            self.write_line('finally:')
            with self.indented():
                self.visit_statements(node.finalbody)

    if PY2:
        def visit_TryExcept(self, node):
            self.write_line('try:')
            with self.indented():
                self.visit_statements(node.body)
            for excepthandler in node.handlers:
                self.visit(excepthandler)
            if node.orelse:
                self.write_line('else:')
                with self.indented():
                    self.visit_statements(node.orelse)

        def visit_TryFinally(self, node):
            self.write_line('try:')
            with self.indented():
                self.visit_statements(node.body)
            self.write_line('finally:')
            with self.indented():
                self.visit_statements(node.finalbody)

    def visit_Assert(self, node):
        with self.writing_statement():
            self.write('assert ')
            self.visit(node.test)
            if node.msg is not None:
                self.write(', ')
                self.visit(node.msg)

    def visit_Import(self, node):
        with self.writing_statement():
            self.write('import ')
            self.write_comma_separated_nodes(node.names)

    def visit_ImportFrom(self, node):
        with self.writing_statement():
            self.write('from ')
            if node.module is None:
                self.write('.')
            else:
                self.write_identifier(node.module)
            self.write(' import ')
            self.write_comma_separated_nodes(node.names)

    def visit_Global(self, node):
        with self.writing_statement():
            self.write('global ')
            for name in self.writing_comma_separated(node.names):
                self.write_identifier(name)

    def visit_Nonlocal(self, node):
        with self.writing_statement():
            self.write('nonlocal ')
            for name in self.writing_comma_separated(node.names):
                self.write_identifier(name)

    def visit_Expr(self, node):
        with self.writing_statement():
            self.visit(node.value)

    def visit_Pass(self, node):
        self.write_line('pass')

    def visit_Break(self, node):
        self.write_line('break')

    def visit_Continue(self, node):
        self.write_line('continue')

    def visit_BoolOp(self, node):
        def write_value(value):
            if _requires_parentheses(node, value):
                self.write('(')
                self.visit(value)
                self.write(')')
            else:
                self.visit(value)
        for value in node.values[:-1]:
            write_value(value)
            self.visit(node.op)
        write_value(node.values[-1])

    def visit_BinOp(self, node):
        if (
            _requires_parentheses(node, node.left) or
            PY2 and isinstance(node.left, ast.Num) and node.left.n < 0
        ):
            self.write('(')
            self.visit(node.left)
            self.write(')')
        else:
            self.visit(node.left)
        self.write(u' ')
        self.visit(node.op)
        self.write(u' ')
        if _requires_parentheses(
            ast.Mult() if isinstance(node.op, ast.Pow) else node,
            node.right
        ):
            self.write('(')
            self.visit(node.right)
            self.write(')')
        else:
            self.visit(node.right)

    def visit_UnaryOp(self, node):
        self.visit(node.op)
        if _requires_parentheses(node, node.operand):
            self.write('(')
            self.visit(node.operand)
            self.write(')')
        else:
            self.visit(node.operand)

    def visit_Lambda(self, node):
        self.write('lambda ')
        self.visit(node.args)
        self.write(': ')
        self.visit(node.body)

    def visit_IfExp(self, node):
        if _requires_parentheses(node, node.body):
            self.write('(')
            self.visit(node.body)
            self.write(')')
        else:
            self.visit(node.body)
        self.write(' if ')
        if _requires_parentheses(node, node.test):
            self.write('(')
            self.visit(node.test)
            self.write(')')
        else:
            self.visit(node.test)
        self.write(' else ')
        self.visit(node.orelse)

    def visit_Dict(self, node):
        self.write('{')
        items = list(zip(node.keys, node.values))
        for key, value in self.writing_comma_separated(items):
            self.visit(key)
            self.write(': ')
            self.visit(value)
        self.write('}')

    def visit_Set(self, node):
        self.write('{')
        self.write_comma_separated_nodes(node.elts)
        self.write('}')

    def visit_ListComp(self, node):
        self.write('[')
        self.visit(node.elt)
        for generator in node.generators:
            self.visit(generator)
        self.write(']')

    def visit_SetComp(self, node):
        self.write('{')
        self.visit(node.elt)
        for generator in node.generators:
            self.visit(generator)
        self.write('}')

    def visit_DictComp(self, node):
        self.write('{')
        self.visit(node.key)
        self.write(': ')
        self.visit(node.value)
        for generator in node.generators:
            self.visit(generator)
        self.write('}')

    def visit_GeneratorExp(self, node):
        self.write('(')
        self.visit(node.elt)
        for generator in node.generators:
            self.visit(generator)
        self.write(')')

    def visit_Yield(self, node):
        self.write('yield')
        if node.value is not None:
            self.write(' ')
            self.visit(node.value)

    def visit_YieldFrom(self, node):
        self.write('yield from ')
        self.visit(node.value)

    def visit_Compare(self, node):
        self.visit(node.left)
        for op, comparator in zip(node.ops, node.comparators):
            self.write(' ')
            self.visit(op)
            self.write(' ')
            self.visit(comparator)

    def visit_Call(self, node):
        if _requires_parentheses(node, node.func):
            self.write('(')
            self.visit(node.func)
            self.write(')')
        else:
            self.visit(node.func)
        self.write('(')
        self.write_comma_separated_nodes(node.args)
        if node.keywords:
            if node.args:
                self.write(', ')
            self.write_comma_separated_nodes(node.keywords)
        if node.starargs is not None:
            if node.args or node.keywords:
                self.write(', ')
            self.write('*')
            self.visit(node.starargs)
        if node.kwargs:
            if node.args or node.keywords or node.starargs:
                self.write(', ')
            self.write('**')
            self.visit(node.kwargs)
        self.write(')')

    if PY2:
        def visit_Repr(self, node):
            self.write('`')
            self.visit(node.value)
            self.write('`')

    def visit_Num(self, node):
        self.write_repr(node.n)

    def visit_Str(self, node):
        self.write_repr(node.s)

    def visit_Bytes(self, node):
        self.write_repr(node.s)

    def visit_Ellipsis(self, node):
        self.write('...')

    def visit_Attribute(self, node):
        if (
            _requires_parentheses(node, node.value) and
            not isinstance(node.value, ast.Attribute)
        ):
            self.write('(')
            self.visit(node.value)
            self.write(')')
        else:
            self.visit(node.value)
        self.write('.')
        self.write_identifier(node.attr)

    def visit_Subscript(self, node):
        if (
            _requires_parentheses(node, node.value) and
            not isinstance(node.value, ast.Subscript)
        ):
            self.write('(')
            self.visit(node.value)
            self.write(')')
        else:
            self.visit(node.value)
        self.write('[')
        self.visit(node.slice)
        self.write(']')

    def visit_Starred(self, node):
        self.write('*')
        self.visit(node.value)

    def visit_Name(self, node):
        self.write_identifier(node.id)

    def visit_List(self, node):
        self.write('[')
        self.write_comma_separated_nodes(node.elts)
        self.write(']')

    def visit_Tuple(self, node):
        self.write_comma_separated_nodes(node.elts)

    def visit_Slice(self, node):
        if node.lower is not None:
            self.visit(node.lower)
            self.write(':')
        if node.upper is not None:
            if node.lower is None:
                self.write(':')
            self.visit(node.upper)
        if node.step is not None:
            if node.lower is None and node.upper is None:
                self.write('::')
            if node.lower is not None or node.upper is not None:
                self.write(':')
            self.visit(node.step)
        if node.lower is None and node.upper is None and node.step is None:
            self.write(':')

    def visit_And(self, node):
        self.write(' and ')

    def visit_Or(self, node):
        self.write(' or ')

    def visit_Add(self, node):
        self.write('+')

    def visit_Sub(self, node):
        self.write('-')

    def visit_Mult(self, node):
        self.write('*')

    def visit_Div(self, node):
        self.write('/')

    def visit_Mod(self, node):
        self.write('%')

    def visit_Pow(self, node):
        self.write('**')

    def visit_LShift(self, node):
        self.write('<<')

    def visit_RShift(self, node):
        self.write('>>')

    def visit_BitOr(self, node):
        self.write('|')

    def visit_BitXor(self, node):
        self.write('^')

    def visit_BitAnd(self, node):
        self.write('&')

    def visit_FloorDiv(self, node):
        self.write('//')

    def visit_Invert(self, node):
        self.write('~')

    def visit_Not(self, node):
        self.write('not ')

    def visit_UAdd(self, node):
        self.write('+')

    def visit_USub(self, node):
        self.write('-')

    def visit_Eq(self, node):
        self.write('==')

    def visit_NotEq(self, node):
        self.write('!=')

    def visit_Lt(self, node):
        self.write('<')

    def visit_LtE(self, node):
        self.write('<=')

    def visit_Gt(self, node):
        self.write('>')

    def visit_GtE(self, node):
        self.write('>=')

    def visit_Is(self, node):
        self.write('is')

    def visit_IsNot(self, node):
        self.write('is not')

    def visit_In(self, node):
        self.write('in')

    def visit_NotIn(self, node):
        self.write('not in')

    def visit_comprehension(self, node):
        self.write(' for ')
        self.visit(node.target)
        self.write(' in ')
        self.visit(node.iter)
        if node.ifs:
            self.write(' if ')
            for filter in node.ifs[:-1]:
                self.visit(filter)
                self.write(' if ')
            self.visit(node.ifs[-1])

    def visit_ExceptHandler(self, node):
        self.write('except')
        if node.type is not None:
            self.write(' ')
            self.visit(node.type)
        if node.name is not None:
            self.write(' as ')
            if PY2:
                self.visit(node.name)
            else:
                self.write(node.name)
        self.write(':')
        self.write_newline()
        with self.indented():
            self.visit_statements(node.body)

    def visit_arguments(self, node):
        if node.args:
            if node.defaults:
                non_defaults = node.args[:-len(node.defaults)]
                defaults = node.args[-len(node.defaults):]
            else:
                non_defaults = node.args
                defaults = []
            if non_defaults:
                self.write_comma_separated_nodes(non_defaults)
            if defaults:
                if non_defaults:
                    self.write(', ')
                for argument, default in zip(defaults, node.defaults):
                    self.visit(argument)
                    self.write('=')
                    self.visit(default)
        if node.vararg:
            if node.args:
                self.write(', ')
            self.write('*')
            self.write_identifier(node.vararg)
        if not PY2 and node.kwonlyargs:
            if not node.vararg:
                self.write('*, ')
            arguments = list(zip(node.kwonlyargs, node.kw_defaults))
            if arguments:
                for argument, default in self.writing_comma_separated(arguments):
                    self.visit(argument)
                    if default is not None:
                        self.write('=')
                        self.visit(default)
        if node.kwarg:
            if node.args or node.vararg or (not PY2 and node.kwonlyargs):
                self.write(', ')
            self.write('**')
            self.write_identifier(node.kwarg)

    def visit_arg(self, node):
        self.write(node.arg)
        if node.annotation is not None:
            self.write(': ')
            self.visit(node.annotation)

    def visit_keyword(self, node):
        self.write_identifier(node.arg)
        self.write('=')
        self.visit(node.value)

    def visit_alias(self, node):
        self.write_identifier(node.name)
        if node.asname is not None:
            self.write(' as ')
            self.write_identifier(node.asname)

    def visit_withitem(self, node):
        self.visit(node.context_expr)
        if node.optional_vars is not None:
            self.write(' as ')
            self.visit(node.optional_vars)


_precedence_tower = [
    {ast.Lambda},
    {ast.IfExp},
    {ast.Or},
    {ast.And},
    {ast.Not},
    {
        ast.In, ast.NotIn, ast.Is, ast.IsNot, ast.Lt, ast.LtE, ast.Gt, ast.GtE,
        ast.NotEq, ast.Eq
    },
    {ast.BitOr},
    {ast.BitXor},
    {ast.BitAnd},
    {ast.LShift, ast.RShift},
    {ast.Add, ast.Sub},
    {ast.Mult, ast.Div, ast.FloorDiv, ast.Mod},
    {ast.UAdd, ast.USub, ast.Invert},
    {ast.Pow},
    {ast.Subscript, ast.Call, ast.Attribute},
    {
        ast.Tuple, ast.List, ast.Dict, ast.Set, ast.ListComp, ast.DictComp,
        ast.SetComp
    }
]

_all_nodes = set(chain.from_iterable(_precedence_tower))
_node2lower_equal_upper_nodes = {}
lower = set()
for i, nodes in enumerate(_precedence_tower):
    lower = reduce(set.union, _precedence_tower[:i], set())
    upper = reduce(set.union, _precedence_tower[i + 1:], set())
    for node in nodes:
        _node2lower_equal_upper_nodes[node] = (lower, nodes, upper)


def _requires_parentheses(parent, child):
    def _normalize(obj):
        if isinstance(obj, (ast.BoolOp, ast.BinOp, ast.UnaryOp)):
            return obj.op.__class__
        return obj.__class__
    parent, child = _normalize(parent), _normalize(child)
    lower, equal = _node2lower_equal_upper_nodes[parent][:2]
    return child in lower | equal


def dump(node, annotate_fields=True, include_attributes=False):
    """
    Like :func:`ast.dump` but with a more readable return value, making the
    output actually useful for debugging purposes.
    """
    def _format(node, level=0):
        if isinstance(node, ast.AST):
            fields = [
                (name, _format(value, level))
                for name, value in ast.iter_fields(node)
            ]
            if include_attributes and node._attributes:
                fields.extend((name, _format(getattr(node, name), level))
                               for name in node._attributes)
            return '{}({})'.format(
                node.__class__.__name__,
                ', '.join(
                    map('='.join, fields)
                    if annotate_fields else
                    (value for _, value in fields)
                )
            )
        elif isinstance(node, list):
            if node:
                indentation = '    ' * (level + 1)
                lines = ['[']
                lines.extend(
                    indentation + _format(n, level + 1) + ',' for n in node
                )
                lines.append(indentation + ']')
                return '\n'.join(lines)
            return '[]'
        return repr(node).decode('ascii') if PY2 else repr(node)
    if not isinstance(node, ast.AST):
        raise TypeError(
            'expected AST, got {!r}'.format(node.__class__.__name__)
        )
    return _format(node)
