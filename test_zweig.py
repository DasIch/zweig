# coding: utf-8
"""
    test_zweig
    ~~~~~~~~~~

    :copyright: 2014 by Daniel Neuhäuser
    :license: BSD, see LICENSE.rst for details
"""
from __future__ import unicode_literals
import ast
import textwrap

import pytest

import zweig


def test_walk_preorder():
    source = textwrap.dedent("""
        def f():
            foo
            def g():
                baz
            bar
    """)
    tree = ast.parse(source)
    nodes = zweig.walk_preorder(tree)

    node = next(nodes)
    assert isinstance(node, ast.Module)

    node = next(nodes)
    assert isinstance(node, ast.FunctionDef) and node.name == 'f'

    node = next(nodes)
    assert isinstance(node, ast.arguments)

    node = next(nodes)
    assert isinstance(node, ast.Expr)

    node = next(nodes)
    assert isinstance(node, ast.Name) and node.id == 'foo'

    node = next(nodes)
    assert isinstance(node, ast.Load)

    node = next(nodes)
    assert isinstance(node, ast.FunctionDef) and node.name == 'g'

    node = next(nodes)
    assert isinstance(node, ast.arguments)

    node = next(nodes)
    assert isinstance(node, ast.Expr)

    node = next(nodes)
    assert isinstance(node, ast.Name) and node.id == 'baz'

    node = next(nodes)
    assert isinstance(node, ast.Load)

    node = next(nodes)
    assert isinstance(node, ast.Expr)

    node = next(nodes)
    assert isinstance(node, ast.Name) and node.id == 'bar'

    node = next(nodes)
    assert isinstance(node, ast.Load)

    with pytest.raises(StopIteration):
        next(nodes)
