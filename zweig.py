# coding: utf-8
"""
    zweig
    ~~~~~

    :copyright: 2014 by Daniel Neuhäuser
    :license: BSD, see LICENSE.rst for details
"""
import os
import ast


def walk_preorder(tree):
    """
    Yields the nodes in the `tree` in preorder.
    """
    yield tree
    for child in ast.iter_child_nodes(tree):
        for descendent in walk_preorder(child):
            yield descendent
