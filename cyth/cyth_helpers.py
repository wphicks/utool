"""
python -c "import doctest, cyth; print(doctest.testmod(cyth.cyth_helpers))"
"""
from __future__ import absolute_import, division, print_function
from os.path import splitext, split, join


def get_cyth_name(py_name):
    """
    >>> py_name = 'vtool.keypoint'
    >>> cy_name = get_cyth_name(py_name)
    >>> print(cy_name)
    vtool._keypoint_cyth
    """
    # Ensure other modules are not affected
    components = py_name.split('.')
    components[-1] = '_' + components[-1] + '_cyth'
    cy_name = '.'.join(components)
    return cy_name


def get_cyth_path(py_fpath):
    """
    >>> py_fpath = '/foo/vtool/vtool/keypoint.py'
    >>> cy_fpath = get_cyth_path(py_fpath)
    >>> print(cy_fpath)
    /foo/vtool/vtool/_keypoint_cyth.pyx
    """
    dpath, fname = split(py_fpath)
    name, ext = splitext(fname)
    assert ext == '.py', 'not a python file'
    cy_fpath = join(dpath, get_cyth_name(name) + '.pyx')
    return cy_fpath