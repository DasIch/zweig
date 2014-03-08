# coding: utf-8
"""
    test_zweig
    ~~~~~~~~~~

    :copyright: 2014 by Daniel Neuhäuser
    :license: BSD, see LICENSE.rst for details
"""
from __future__ import unicode_literals
import ast
import sys
import textwrap

import pytest

import zweig


PY2 = sys.version_info[0] == 2


only_python2 = pytest.mark.skipif(
    sys.version_info[0] > 2,
    reason='only python 2'
)

min_python3 = pytest.mark.skipif(
    sys.version_info[0] < 3,
    reason='requires python 3'
)


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


@pytest.mark.parametrize('source', [
    """
        def argumentless():
            pass
    """,
    """
        def single_positional(foo):
            return
    """,
    """
        def two_positional(foo, bar):
            return None
    """,
    """
        def defaults(foo, bar=1):
            global something
            global foo, bar
    """,
    """
        def arbitrary_arguments(*args):
            yield
    """,
    """
        def kwargs(**kwargs):
            yield something
    """,
    """
        @foo
        def single_decorator():
            pass
    """,
    """
        @foo
        @bar
        def multiple_decorators():
            pass
    """,
    """
        class NoBase:
            pass
    """,
    """
        class SingleBase(object):
            pass
    """,
    """
        class MultipleBases(Foo, Bar):
            pass
    """,
    """
        @foo
        class SingleDecorator:
            pass
    """,
    """
        @foo
        @bar
        class MultipleDecorators:
            pass
    """,
    """
        del something
        del something, another_thing
    """,
    """
        foo = something
        foo = bar = baz
    """,
    """
        foo += bar
        foo -= bar
        foo *= bar
        foo /= bar
        foo %= bar
        foo **= bar
        foo <<= bar
        foo >>= bar
        foo |= bar
        foo ^= bar
        foo &= bar
        foo //= bar
    """,
    """
        for whatever in whatevers:
            if blubb:
                continue
            else:
                break
        for spam in spams:
            pass
        else:
            pass
    """,
    """
        while True:
            pass
        while True:
            pass
        else:
            pass
    """,
    """
        with foo:
            pass
        with foo as bar:
            pass
    """,
    """
        try:
            pass
        except:
            pass
        except Something:
            pass
        except Something as AnotherThing:
            pass
        try:
            pass
        except:
            pass
        else:
            pass
        try:
            pass
        finally:
            pass
    """,
    """
        assert something
        assert something, message
    """,
    """
        import foo
        import foo, bar
        import spam as eggs
        from . import foo
        from foo import bar
        from foo import bar, baz
        from foo import spam as eggs
    """,
    """
        foo or bar
        foo or bar or baz
        foo and bar
        foo and bar and baz
        foo and bar or baz
        foo and (bar or baz)
        foo or bar and baz
        (foo or bar) and baz
        not foo
        not foo and not bar
    """,
    """
        (foo or bar) and baz
        foo and (bar or baz)
        not (foo or bar)
        not (foo and bar)
    """,
    """
        1 + 1
        1 - 1
        1 * 1
        1 / 1
        1 % 1
        1 << 1
        1 >> 1
        1 | 1
        1 ^ 1
        1 & 1
        1 // 1
    """,
    """
        1 + (1 - 1)
        1 - (1 + 1)
        (1 - 1) + 1
        (1 + 1) - 1
    """,
    """
        1 * (1 / 1)
        1 * (1 // 1)
        1 / (1 * 1)
        1 // (1 * 1)
        1 % (1 * 1)
    """,
    """
        (1 / 1) * 1
        (1 // 1) * 1
        (1 * 1) / 1
        (1 * 1) // 1
        (1 * 1) % 1
        (1 % 1) * 1
        (1 % 1) / 1
        (1 % 1) // 1
    """,
    """
        1 * (1 + 1)
        1 * (1 - 1)
        1 / (1 + 1)
        1 / (1 - 1)
        1 // (1 + 1)
        1 // (1 - 1)
        1 % (1 + 1)
        1 % (1 - 1)
    """,
    """
        (1 + 1) * 1
        (1 - 1) * 1
        (1 + 1) / 1
        (1 - 1) / 1
        (1 + 1) // 1
        (1 - 1) // 1
        (1 + 1) % 1
        (1 - 1) % 1
    """,
    """
        ~1
        not 1
        +1
        -1
    """,
    """
        +(1 + 1)
        -(1 + 1)
        ~(1 + 1)
    """,
    """
        1 ** 1
        -1 ** 1
        1 ** -1
        (-1) ** 1
    """,
    """
        lambda : None
        lambda foo: None
        lambda foo, bar: None
        lambda : None if False else 'foo'
        (lambda : None) if False else 'foo'
    """,
    """
        foo if condition else bar
        foo if condition else bar if True else baz
        spam if (bar if True else baz) else eggs
    """,
    """
        {}
        {key: value}
        {key: value, another_key: another_value}
    """,
    """
        {element}
        {element, another_element}
    """,
    """
        [item for item in foo]
        [item for item in foo if something]
        [subitem for item in foo for subitem in item]
    """,
    """
        {item for item in foo}
        {item for item in foo if something}
        {subitem for item in foo for subitem in item}
    """,
    """
        {key: value for key, value in foo}
        {key: value for key, value in foo if value}
    """,
    """
        (item for item in foo)
    """,
    """
        1 == 1
        1 != 1
        1 < 1
        1 <= 1
        1 > 1
        1 >= 1
        1 is 1
        1 is not 1
        1 in foo
        1 not in foo
    """,
    """
        func()
        func(foo, bar)
        func(*args)
        func(**kwargs)
        func(foo=bar)
        (foo + bar)()
    """,
    """
        'string'
    """,
    """
        foo.bar
        foo.bar.baz
        (foo + bar).baz
    """,
    """
        foo[index]
        foo[:]
        foo[start:]
        foo[:stop]
        foo[start:stop]
        foo[::step]
        foo[start::step]
        foo[:stop:step]
        foo[start:stop:step]
        foo[bar][baz]
        (foo + bar)[index]
    """
])
def test_to_source(source):
    source = textwrap.dedent(source).lstrip()
    tree = ast.parse(source)
    result = zweig.to_source(tree)
    assert result == source


@only_python2
def test_to_source_2():
    source = textwrap.dedent("""\
    print
    print foo
    print foo, bar
    print foo, bar,
    raise
    raise value
    raise type, value
    raise type, value, tb
    `'foo'`
    """)
    tree = ast.parse(source)
    result = zweig.to_source(tree)
    assert result == source


@min_python3
def test_to_source_3():
    source = textwrap.dedent("""\
        def single_positonal(foo: annotation):
            nonlocal foo
            nonlocal foo, bar

        def return_annotation() -> foo:
            yield from foo

        def kwonly(*, foo):
            pass

        def kwonly_starargs(*, foo=bar):
            pass

        def kwonly_kwargs(*, foo=bar, **kwargs):
            pass

        class Keywords(foo=bar):
            pass

        class Starargs(*args):
            pass

        class Kwargs(**kwargs):
            pass

        class AllArgs(foo=bar, *args, **kwargs):
            pass

        raise
        raise value
        raise value from cause
        b'bytes'
        ...
        *foo = bar
        foo = []
        foo = [1, 2]
    """)
    tree = ast.parse(source)
    result = zweig.to_source(tree)
    assert result == source


def test_dump():
    tree = ast.parse('spam(eggs, "and cheese")')
    assert zweig.dump(tree) == textwrap.dedent("""\
        Module(body=[
            Expr(value=Call(func=Name(id='spam', ctx=Load()), args=[
                Name(id='eggs', ctx=Load()),
                Str(s='and cheese'),
                ], keywords=[], starargs=None, kwargs=None)),
            ])""")
    assert zweig.dump(tree, annotate_fields=False) == textwrap.dedent("""\
        Module([
            Expr(Call(Name('spam', Load()), [
                Name('eggs', Load()),
                Str('and cheese'),
                ], [], None, None)),
            ])""")
    assert zweig.dump(tree, include_attributes=True) == textwrap.dedent("""\
        Module(body=[
            Expr(value=Call(func=Name(id='spam', ctx=Load(), lineno=1, col_offset=0), args=[
                Name(id='eggs', ctx=Load(), lineno=1, col_offset=5),
                Str(s='and cheese', lineno=1, col_offset=11),
                ], keywords=[], starargs=None, kwargs=None, lineno=1, col_offset=0), lineno=1, col_offset=0),
            ])""")


@pytest.mark.parametrize(('source', 'is_target'), [
    ('name', True),
    ('foo, bar', True),
    ('foo(), bar', False),
    ('[foo, bar]', True),
    ('[foo(), bar]', False),
    ('sequence[0]', True),
    ('foo.bar', True)
] + [] if PY2 else [
    ('foo, *bar', True),
    ('*foo', False),
    ('foo, *bar()', False)
]
)
def test_is_possible_target(source, is_target):
    module = ast.parse(source)
    expression = module.body[0].value
    print(zweig.to_source(expression))
    print(zweig.dump(expression))
    assert zweig.is_possible_target(expression) == is_target


def test_set_target_contexts():
    expression = ast.parse('name').body[0].value
    zweig.set_target_contexts(expression)
    assert isinstance(expression.ctx, ast.Store)

    expression = ast.parse('foo.bar').body[0].value
    zweig.set_target_contexts(expression)
    assert isinstance(expression.ctx, ast.Store)

    expression = ast.parse('foo[0]').body[0].value
    zweig.set_target_contexts(expression)
    assert isinstance(expression.ctx, ast.Store)

    expression = ast.parse('foo, bar').body[0].value
    zweig.set_target_contexts(expression)
    assert isinstance(expression.ctx, ast.Store)
    assert isinstance(expression.elts[0].ctx, ast.Store)
    assert isinstance(expression.elts[1].ctx, ast.Store)

    expression = ast.parse('[foo, bar]').body[0].value
    zweig.set_target_contexts(expression)
    assert isinstance(expression.ctx, ast.Store)
    assert isinstance(expression.elts[0].ctx, ast.Store)
    assert isinstance(expression.elts[1].ctx, ast.Store)

    if not PY2:
        expression = ast.parse('foo, *bar').body[0].value
        zweig.set_target_contexts(expression)
        assert isinstance(expression.ctx, ast.Store)
        assert isinstance(expression.elts[0].ctx, ast.Store)
        assert isinstance(expression.elts[1].ctx, ast.Store)
        assert isinstance(expression.elts[1].value.ctx, ast.Store)

        expression = ast.parse('foo, *[bar, bar]').body[0].value
        zweig.set_target_contexts(expression)
        assert isinstance(expression.ctx, ast.Store)
        assert isinstance(expression.elts[0].ctx, ast.Store)
        assert isinstance(expression.elts[1].ctx, ast.Store)
        assert isinstance(expression.elts[1].value.ctx, ast.Store)
        assert isinstance(expression.elts[1].value.elts[0].ctx, ast.Store)
        assert isinstance(expression.elts[1].value.elts[1].ctx, ast.Store)
