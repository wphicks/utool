# -*- coding: utf-8 -*-
"""
Helpers for tests

This module contains a more sane reimplementation of doctest functionality.
(I.E.  asserts work and you don't have to worry about stdout mucking things up)
The code isn't super clean though due to time constriaints.  Many functions
probably belong elsewhere and the parsers need a big cleanup.

TODO:
    * report the line of the doctest in the file when reporting errors as well as
     the relative line

    * restructure so there is a test collection step, a filtering step, and an
      execution step
"""
from __future__ import absolute_import, division, print_function, unicode_literals
import six
#from six.moves import builtins
from collections import namedtuple
import inspect
import types
import traceback  # NOQA
import sys
from os.path import basename
from utool import util_print  # NOQA
from utool import util_arg
from utool import util_path
from utool import util_time
from utool import util_inject
from utool import util_dbg
from utool._internal import meta_util_six
from utool._internal.meta_util_six import get_funcname
print, rrr, profile = util_inject.inject2(__name__, '[tests]')


VERBOSE_TEST = util_arg.get_argflag(('--verbtest', '--verb-test', '--verbose-test'))
#PRINT_SRC = not util_arg.get_argflag(('--noprintsrc', '--nosrc'))
DEBUG_SRC = not util_arg.get_argflag('--nodbgsrc')
PRINT_SRC = util_arg.get_argflag(('--printsrc', '--src', '--show-src', '--showsrc'),
                                 help_='show docstring source when running tests')
#PRINT_FACE = not util_arg.get_argflag(('--noprintface', '--noface'))
PRINT_FACE = util_arg.get_argflag(('--printface', '--face'))
#BIGFACE = False
BIGFACE = util_arg.get_argflag('--bigface')
SYSEXIT_ON_FAIL = util_arg.get_argflag(('--sysexitonfail', '--fastfail'),
                                       help_='Force testing harness to exit on first test failure')
VERBOSE_TIMER = not util_arg.get_argflag('--no-time-tests')
INDENT_TEST   = False
#EXEC_MODE = util_arg.get_argflag('--exec-mode', help_='dummy flag that will be removed')

ModuleDoctestTup = namedtuple('ModuleDoctestTup', ('enabled_testtup_list',
                                                   'frame_fpath',
                                                   'all_testflags', 'module'))


class TestTuple(object):
    """
    Simple container for test objects to replace old tuple format
    exec mode specifies if the test is being run as a script
    """
    def __init__(self, name, num, src, want, flag, frame_fpath=None, exec_mode=False):
        self.name = name  # function / class / testable name
        self.num = num    # doctest index
        self.src = src    # doctest src
        self.want = want  # doctest required result (optional)
        self.flag = flag  # doctest commandline flags
        self.frame_fpath = frame_fpath  # parent file fpath
        self.exec_mode = exec_mode      # flags if running as script

##debug_decor = lambda func: func

#if VERBOSE_TEST:
#    from utool import util_decor
#    #debug_decor = util_decor.indent_func
#    #debug_decor = util_decor.tracefunc


HAPPY_FACE_BIG = r'''
               .-""""""-.
             .'          '.
            /   O      O   \
           :                :
           |                |
           '  ,          ,' :
            \  '-......-'  /
             '.          .'
               '-......-'
                   '''

SAD_FACE_BIG = r'''
               .-""""""-.
             .'          '.
            /   O      O   \
           :           `    :
           |                |
           :    .------.    :
            \  '        '  /
             '.          .'
               '-......-'
                  '''

HAPPY_FACE_SMALL = r'''
     .""".
    | o o |
    | \_/ |
     ' = '
    '''

SAD_FACE_SMALL = r'''
     .""".
    | . . |
    |  ~  |
     ' = '
    '''

if BIGFACE:
    HAPPY_FACE = HAPPY_FACE_BIG
    SAD_FACE = SAD_FACE_BIG
else:
    HAPPY_FACE = HAPPY_FACE_SMALL
    #SAD_FACE = SAD_FACE_BIG
    SAD_FACE = SAD_FACE_SMALL


def doctest_module_list(module_list):
    """
    Runs many module tests

    Entry point for batch run
    Depth 0)

    Ignore:
        :'<,'>!sort -n -k 2
    """
    import utool as ut
    nPass_list = []
    nTotal_list = []
    failed_cmds_list = []
    error_reports_list = []
    print('[util_test] Running doctests on module list')

    try:
        ut.write_to('test_times.txt', '\n\n --- begining doctest_module_list\n', mode='a')
    except IOError as ex:
        ut.printex(ex, '[util_test] IOWarning', iswarning=True)

    failed_doctest_fname = 'failed_doctests.txt'
    with open(failed_doctest_fname, 'a') as file_:
        file_.write('\n-------\n\n')
        file_.write(ut.get_printable_timestamp() + '\n')
        file_.write('logfile (only present if logging) = %r\n' %
                    (ut.util_logging.get_current_log_fpath(),))
        testkw = dict(allexamples=True, return_error_report=True)
        with ut.Timer(verbose=False) as t:
            for module in module_list:
                (nPass, nTotal, failed_list, error_report_list) = ut.doctest_funcs(
                    module=module, **testkw)
                nPass_list.append(nPass)
                nTotal_list.append(nTotal)
                failed_cmds_list.append(failed_list)
                error_reports_list.append(error_report_list)
                # Write failed tests to disk
                for cmd in failed_list:
                    file_.write(cmd + '\n')
        total_time = t.ellapsed
        nPass = sum(nPass_list)
        nTotal = sum(nTotal_list)
        file_.write('PASSED %d / %d' % (nPass, nTotal))

    failed_cmd_list = ut.flatten(failed_cmds_list)
    error_report_list = ut.filter_Nones(ut.flatten(error_reports_list))
    if len(error_report_list) > 0:
        print('\nPrinting %d error reports' % (len(error_report_list),))
        for count, error_report in enumerate(error_report_list):
            print('\n=== Error Report %d / %d' % (count, len(error_report_list)))
            print(error_report)
        print('--- Done printing error reports ----')

    try:
        ut.write_to('test_times.txt', '\n\n --- finished doctest_module_list total_time=%.3fs\n' % (total_time), mode='a')
    except IOError as ex:
        ut.printex(ex, '[util_test] IOWarning', iswarning=True)

    print('')
    print('+========')
    print('| FINISHED TESTING %d MODULES' % (len(module_list),))
    print('| PASSED %d / %d' % (nPass, nTotal))
    print('L========')
    if len(failed_cmd_list) > 0:
        print('FAILED TESTS:')
        print('\n'.join(failed_cmd_list))
    return nPass, nTotal, failed_cmd_list


def doctest_funcs(testable_list=None, check_flags=True, module=None, allexamples=None,
                  needs_enable=None, strict=False, verbose=True, return_error_report=False):
    """
    Main entry point into utools main module doctest harness
    Imports a module and checks flags for the function to run
    Depth 1)

    Args:
        testable_list (list):
        check_flags (bool): Force checking of the --test- and --exec- flags
        module (None):
        allexamples (None):
        needs_enable (None):

    Returns:
        tuple: (nPass, nTotal, failed_cmd_list)

    CommandLine:
        python -m ibeis.model.preproc.preproc_chip --all-examples

    References:
        http://legacy.python.org/dev/peps/pep-0338/
        https://docs.python.org/2/library/runpy.html

    Example:
        >>> # DISABLE_DOCTEST
        >>> from utool.util_tests import *  # NOQA
        >>> testable_list = []
        >>> check_flags = True
        >>> module = None
        >>> allexamples = None
        >>> needs_enable = None
        >>> # careful might infinitely recurse
        >>> (nPass, nTotal) = doctest_funcs(testable_list, check_flags, module,
        ...                                 allexamples, needs_enable)
        >>> print((nPass, nTotal))
    """
    import multiprocessing
    import utool as ut  # NOQA
    ut.start_logging()
    multiprocessing.freeze_support()  # just in case
    ut.inject_colored_exceptions()

    if (verbose or VERBOSE_TEST) and ut.NOT_QUIET:
        if VERBOSE_TEST:
            print('[util_test.doctest_funcs][DEPTH 1] doctest_funcs()')
        print('[util_test.doctest_funcs] Running doctest_funcs')
    if ut.is_developer():
        ut.change_term_title('DocTest ' + ' '.join(sys.argv))

    # parse out testable doctesttups
    mod_doctest_tup = get_module_doctest_tup(
        testable_list, check_flags, module, allexamples, needs_enable, N=1,
        verbose=verbose)
    enabled_testtup_list, frame_fpath, all_testflags, module = mod_doctest_tup
    modname = ut.get_modname_from_modpath(frame_fpath)

    # Run enabled examles
    nPass = 0
    nFail = 0
    failed_flag_list = []
    error_report_list = []
    nTotal = len(enabled_testtup_list)
    if ut.get_argflag(('--edit-test-file', '--etf')):
        ut.editfile(frame_fpath)
    exec_mode = all([testtup.exec_mode for testtup in enabled_testtup_list])

    for testtup in enabled_testtup_list:
        name = testtup.name
        num  = testtup.num
        src  = testtup.src
        want = testtup.want
        flag = testtup.flag
        #if ut.is_developer():
        #    ut.change_term_title('DocTest ' + modname + ' ' + name)
        print('\n\n')
        print('--------------------------------------------------------------')
        print('--------------------------------------------------------------')
        #if EXEC_MODE:
        #    print(' ---- EXEC ' + name.upper() + ':' + str(num) + '---')
        #else:
        print(' ---- DOCTEST ' + modname + ' ' + name.upper() + ':' + str(num) + '---')

        if PRINT_SRC or VERBOSE_TEST:
            print(ut.msgblock('EXEC SRC', src))
        test_globals = module.__dict__.copy()
        error_report = None
        try:
            testkw = dict(
                globals=test_globals,  # HACK
                want=want, return_error_report=True)
            assert testtup.frame_fpath == frame_fpath
            test_locals, error_report = ut.run_test(testtup, **testkw)
            is_pass = (test_locals is not False)
            if is_pass:
                if VERBOSE_TEST:
                    print('seems to pass')
                nPass += 1
            else:
                if VERBOSE_TEST:
                    print('raising failed exception')
                raise Exception('failed')
        except Exception:
            if VERBOSE_TEST:
                print('Seems to fail. ')
            nFail += 1
            failed_flag_list.append(flag)
            error_report_list.append(error_report)
            if strict or util_arg.SUPER_STRICT:
                raise
            else:
                if VERBOSE_TEST:
                    print('Silently Failing: '
                          'maybe adding the --super-strict flag would help debug?')
            pass
    #L__________________
    #+-------------------
    # Print Results
    if nTotal == 0 and not allexamples:
        valid_test_argflags = ['--allexamples'] + all_testflags
        warning_msg = ut.codeblock(
            r'''
            No test flags sepcified
            Please choose one of the following flags or specify --enableall
            Valid test argflags:
            ''') + ut.indentjoin(valid_test_argflags, '\n    ')
        warning_msg = ut.indent(warning_msg, '[util_test.doctest_funcs]')
        ut.colorprint(warning_msg, 'red')

    if not exec_mode:
        print('+-------')
        print('| finished testing fpath=%r' % (frame_fpath,))
        print('| passed %d / %d' % (nPass, nTotal))
        print('L-------')
    failed_cmd_list = []
    if nFail > 0:
        #modname = module.__name__
        modname = ut.get_modname_from_modpath(frame_fpath)
        # TODO: ensure that exename is in the PATH
        exename = basename(sys.executable)
        failed_cmd_list = ['%s -m %s %s' % (exename, modname, flag_)
                            for flag_ in failed_flag_list]
        #failed_cmd_list = ['python %s %s' % (frame_fpath, flag_)
        #                    for flag_ in failed_flag_list]
        print('Failed sys.argv = %r' % (' '.join(sys.argv),))
        print('Failed Tests:')
        print('\n'.join(failed_cmd_list))
    #L__________________
    if return_error_report:
        return (nPass, nTotal, failed_cmd_list, error_report_list)
    else:
        return (nPass, nTotal, failed_cmd_list)


def run_test(func_or_testtup, return_error_report=False, *args, **kwargs):
    """
    Runs the test function with success / failure printing

    Args:
        func_or_testtup (func or tuple): function or doctest tuple

    Varargs/Kwargs:
        Anything that needs to be passed to <func_>
    """
    import utool as ut
    #func_is_testtup = isinstance(func_or_testtup, tuple)
    # NOTE: isinstance is not gaurenteed not work here if ut.rrrr has been called
    func_is_testtup = isinstance(func_or_testtup, TestTuple)
    exec_mode = False
    write_times = True
    if func_is_testtup:
        testtup = func_or_testtup
        src         = testtup.src
        funcname    = testtup.name
        frame_fpath = testtup.frame_fpath
        #(funcname, src, frame_fpath) = func_or_testtup
        exec_mode = testtup.exec_mode
    else:
        func_ = func_or_testtup
        funcname = get_funcname(func_)
        frame_fpath = ut.get_funcfpath(func_)
    upper_funcname = funcname.upper()
    if ut.VERBOSE:
        print('\n=============================')
        print('**[TEST.BEGIN] %s ' % (sys.executable))
        print('**[TEST.BEGIN] %s ' % (funcname,))
    #print('  <funcname>  ')
    #print('  <' + funcname + '>  ')
    #short_funcname = ut.clipstr(funcname, 8)
    # TODO: make the --exec- prefix specify this instead of --test-
    verbose_timer = not exec_mode and VERBOSE_TIMER
    nocheckwant = True if exec_mode else None
    print_face = not exec_mode and PRINT_FACE
    #indent_test = not exec_mode and INDENT_TEST
    error_report = None

    try:
        #+----------------
        # RUN THE TEST WITH A TIMER
        with util_time.Timer(upper_funcname, verbose=verbose_timer) as timer:
            if func_is_testtup:
                test_locals = _exec_doctest(src, kwargs, nocheckwant)
            else:
                # TEST INPUT IS A LIVE PYTHON FUNCTION
                test_locals = func_(*args, **kwargs)
            print('')
        #L________________
        #+----------------
        # LOG PASSING TEST
        if not exec_mode:
            print('\n=============================')
            print('**[TEST.FINISH] %s -- SUCCESS' % (funcname,))
            if print_face:
                print(HAPPY_FACE)
            if write_times:
                timemsg = '%.4fs in %s %s\n' % (
                    timer.ellapsed, funcname, frame_fpath)
                try:
                    ut.write_to('test_times.txt', timemsg, mode='a')
                except IOError as ex:
                    ut.printex(ex, '[util_test] IOWarning', iswarning=True)
        #L________________
        # RETURN VALID TEST LOCALS
        if return_error_report:
            return test_locals, error_report
        return test_locals

    except Exception as ex:
        import utool as ut
        # Get locals in the wrapped function
        ut.printex(ex, tb=True)
        error_report_lines = ['**[TEST.ERROR] %s -- FAILED:\n    type(ex)=%s' % (
            funcname, type(ex))]
        error_report_lines.append(ut.formatex(ex, tb=True))
        def print_report(msg):
            error_report_lines.append(msg)
            print(msg)
        print_report('\n=============================')
        print_report('**[TEST.FINISH] %s -- FAILED:\n    type(ex)=%s' % (funcname, type(ex)))
        exc_type, exc_value, tb = sys.exc_info()
        if PRINT_FACE:
            print_report(SAD_FACE)
        if func_is_testtup:
            print_report('Failed in module: %r' % frame_fpath)
            if True or DEBUG_SRC:
                src_with_lineno = ut.number_text_lines(src)
                print_report(ut.msgblock('FAILED DOCTEST IN %s' % (funcname,), src_with_lineno))
            #ut.embed()

            #print('\n... test encountered error. sys.exit(1)\n')
            #sys.exit(1)
            #failed_execline = traceback.format_tb(tb)[-1]
            #parse_str = 'File {fname}, line {lineno}, in {modname}'
            #parse_dict = parse.parse('{prefix_}' + parse_str + '{suffix_}', failed_execline)
            #if parse_dict['fname'] == '<string>':
            #    lineno = int(parse_dict['lineno'])
            #    failed_line = src.splitlines()[lineno - 1]
            #    print('Failed on line: %s' % failed_line)
        if util_arg.SUPER_STRICT:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            if not func_is_testtup:
                # Remove this function from stack strace
                # dont do this for execed code
                exc_traceback = exc_traceback.tb_next
            # Python 2*3=6
            if True:
                # FIXME: use common code
                six.reraise(exc_type, exc_value, exc_traceback)
            else:
                ## PYTHON 2.7 DEPRICATED:
                #if six.PY2:
                #    raise exc_type, exc_value, exc_traceback.tb_next
                #    #exec ('raise exc_type, exc_value,
                #    exc_traceback.tb_next', globals(), locals())
                ## PYTHON 3.3 NEW METHODS
                #elif six.PY3:
                #    ex = exc_type(exc_value)
                #    ex.__traceback__ = exc_traceback.tb_next
                #    raise ex
                #else:
                #    raise AssertionError('Weird python version')
                pass
        if SYSEXIT_ON_FAIL:
            print('[util_test] SYSEXIT_ON_FAIL = True')
            print('[util_test] exiting with sys.exit(1)')
            sys.exit(1)
        #raise
        if return_error_report:
            error_report = '\n'.join(error_report_lines)
            return False, error_report


def _exec_doctest(src, kwargs, nocheckwant=None):
    """
    Helper for run_test

    block of code that runs doctest and was too big to be in run_test
    """
    # TEST INPUT IS PYTHON CODE TEXT
    #test_locals = {}
    test_globals = kwargs.get('globals', {}).copy()
    want = kwargs.get('want', None)
    #test_globals['print'] = doctest_print
    # EXEC FUNC
    #six.exec_(src, test_globals, test_locals)  # adds stack to debug trace
    import utool as ut
    if ut.get_argflag(('--cmd', '--embed')):
        src += '\nimport utool as ut; ut.embed()'  # TODO RECTIFY WITH TF
    code = compile(src, '<string>', 'exec')
    try:
        # IN EXEC CONTEXT THERE IS NO DIFF BETWEEN LOCAL / GLOBALS.  ONLY PASS
        # IN ONE DICT. OTHERWISE TREATED ODDLY
        # References: https://bugs.python.org/issue13557
        #exec(code, test_globals, test_locals)
        test_locals = test_globals
        exec(code, test_globals)
    except ExitTestException:
        print('Test exited before show')
        pass
    if nocheckwant is None:
        nocheckwant = util_arg.get_argflag('--no-checkwant', help_='Turns off checking for results')
    if nocheckwant or want is None or want == '':
        if not nocheckwant:
            print('warning test does not want anything')
    else:
        if want.endswith('\n'):
            want = want[:-1]
        result = str(test_locals.get('result', 'NO VARIABLE NAMED result'))
        if result != want:
            errmsg1 = ''
            try:
                import utool as ut
                difftext = ut.get_textdiff(result, want)
                if util_dbg.COLORED_EXCEPTIONS:
                    difftext = ut.get_colored_diff(difftext)
                errmsg1 += ('DIFF/GOT/EXPECTED\n' + difftext + '\n')
            except ImportError:
                errmsg1 += ('REPR_GOT: result=\n%r\n' % (result))
                errmsg1 += ('REPR_EXPECTED: want=\n%r\n' % (want))
            else:
                if VERBOSE_TEST:
                    errmsg1 += ('REPR_GOT: result=\n%r\n' % (result))
                    errmsg1 += ('REPR_EXPECTED: want=\n%r\n' % (want))
            errmsg1 += ''
            errmsg1 += ('STR_GOT: result=\n%s\n' % (result))
            errmsg1 += ('STR_EXPECTED: want=\n%s\n' % (want))
            raise AssertionError('result != want\n' + errmsg1)
    return test_locals


def get_module_testlines(module_list, remove_pyc=True, verbose=True,
                         pythoncmd=None):
    """
    Builds test commands for autogen tests
    called by autogen test scripts
    """
    import utool as ut  # NOQA
    if pythoncmd is None:
        pythoncmd = sys.executable
        #'python'
    testcmd_list = []
    for module in module_list:
        mod_doctest_tup = get_module_doctest_tup(
            module=module, allexamples=True, verbose=verbose)
        enabled_testtup_list, frame_fpath, all_testflags, module_ = mod_doctest_tup
        for testtup in enabled_testtup_list:
            #testflag = testtup[-1]
            testflag = testtup.flag
            if remove_pyc:
                # FIXME python 3 __pycache__/*.pyc
                frame_fpath = frame_fpath.replace('.pyc', '.py')
            frame_rel_fpath = ut.get_relative_modpath(frame_fpath)
            testcmd = ' '.join((pythoncmd, frame_rel_fpath, testflag))
            testcmd_list.append(testcmd)
    return testcmd_list


def parse_docblocks_from_docstr(docstr):
    """
    parse_docblocks_from_docstr
    Depth 5)
    called by parse_doctest_from_docstr
    TODO: move to util_inspect

    Args:
        docstr (str):

    Returns:
        list: docstr_blocks tuples
            [(blockname, blockstr, offset)]


    Example:
        >>> # ENABLE_DOCTEST
        >>> from utool.util_tests import *  # NOQA
        >>> import utool as ut
        >>> #import ibeis
        >>> #import ibeis.model.hots.query_request
        >>> #func_or_class = ibeis.model.hots.query_request.QueryParams
        >>> func_or_class = ut.parse_docblocks_from_docstr
        >>> docstr = ut.get_docstr(func_or_class)
        >>> docstr_blocks = parse_docblocks_from_docstr(docstr)
        >>> result = str(docstr_blocks)
        >>> print(result)
    """
    # FIXME Requires tags to be separated by two spaces
    if docstr is None:
        return []
    import parse
    import utool as ut
    import itertools
    docstr = ut.ensure_unicode(docstr)
    initial_docblocks = docstr.split('\n\n')
    docblock_len_list = [str_.count('\n') + 2 for str_ in initial_docblocks]
    offset_iter = itertools.chain([0], ut.cumsum(docblock_len_list)[:-1])
    initial_line_offsets = [offset for offset in offset_iter]

    if VERBOSE_TEST:
        if ut.VERBOSE:
            print('__________')
            print('__Initial Docblocks__')
            print('\n---\n'.join(initial_docblocks))
    docstr_blocks = []
    for docblock, line_offset in zip(initial_docblocks, initial_line_offsets):
        docblock = docblock.strip('\n')
        indent = ' ' * ut.get_indentation(docblock)
        parse_result = parse.parse(indent + '{tag}:\n{rest}', docblock)
        if parse_result is not None:
            header = parse_result['tag']
        else:
            header = ''
        docstr_blocks.append((header, docblock, line_offset))
    #print(docstr_blocks)

    docblock_headers = ut.get_list_column(docstr_blocks, 0)
    docblock_bodys = ut.get_list_column(docstr_blocks, 1)
    docblock_offsets = ut.get_list_column(docstr_blocks, 2)

    if VERBOSE_TEST:
        print('[util_test]   * found %d docstr_blocks' % (len(docstr_blocks),))
        print('[util_test]   * docblock_headers = %r' % (docblock_headers,))
        print('[util_test]   * docblock_offsets = %r' % (docblock_offsets,))
        if ut.VERBOSE:
            print('[util_test]  * docblock_bodys:')
            print('\n-=-\n'.join(docblock_bodys))
    return docstr_blocks


def parse_doctest_from_docstr(docstr):
    r"""
    because doctest itself doesnt do what I want it to do
    called by get_doctest_examples
    Depth 4)

    CAREFUL, IF YOU GET BACK WRONG RESULTS MAKE SURE YOUR DOCSTR IS PREFFIXED
    WITH R

    Ignore:
        >>> # DISABLE_DOCTEST
        >>> from utool.util_tests import *  # NOQA
        >>> from ibeis.model.hots import score_normalization
        >>> func_or_class = score_normalization.cached_ibeis_score_normalizer
        >>> docstr = ut.get_docstr(func_or_class)
        >>> testsrc_list, testwant_list, testlinenum_list, func_lineno, docstr = get_doctest_examples(func_or_class)
        >>> result = str(len(testsrc_list) + len(testwant_list))
        >>> print(result)
        2
    """
    import utool as ut
    docstr_blocks = parse_docblocks_from_docstr(docstr)

    example_docblocks = []
    example_setups = []

    def read_exampleblock(dockblock):
        nonheader_src = ut.unindent('\n'.join(docblock.splitlines()[1:]))
        nonheader_lines = nonheader_src.splitlines()
        reversed_src_lines = []
        reversed_want_lines = []
        finished_want = False

        # Read the example block backwards to get the want string
        # and then the rest should all be source
        for line in reversed(nonheader_lines):
            if not finished_want:
                if line.startswith('>>> ') or line.startswith('... '):
                    finished_want = True
                else:
                    reversed_want_lines.append(line)
                    continue
            reversed_src_lines.append(line[4:])
        test_src = '\n'.join(reversed_src_lines[::-1])
        test_want = '\n'.join(reversed_want_lines[::-1])
        return test_src, test_want

    for header, docblock, line_offset in docstr_blocks:
        if header.startswith('Example'):
            example_docblocks.append((header, docblock, line_offset))

        if header.startswith('Setup'):
            setup_src = read_exampleblock(docblock)[0]
            example_setups.append(setup_src)

    testheader_list     = []
    testsrc_list        = []
    testwant_list       = []
    testlineoffset_list = []
    for header, docblock, line_offset in example_docblocks:
        test_src, test_want = read_exampleblock(docblock)
        testheader_list.append(header)
        testsrc_list.append(test_src)
        testwant_list.append(test_want)
        testlineoffset_list.append(line_offset)
        #print('Parsed header=%r' % header)
        #print('Parsed src=%r' % test_src)

    # Hack: append setups to all sources
    assert len(example_setups) <= 1, 'cant have more than 1 setup'
    if len(example_setups) == 1:
        testsrc_list = [example_setups[0] + '\n' + src for src in  testsrc_list]

    return testheader_list, testsrc_list, testwant_list, testlineoffset_list


#@debug_decor
def get_doctest_examples(func_or_class):
    """
    get_doctest_examples

    Depth 3)
    called by get_module_doctest_tup

    Args:
        func_or_class (function)

    Returns:
        tuple (list, list): example_list, want_list

    CommandLine:
        python -m utool.util_tests --test-get_doctest_examples

    Example0:
        >>> # ENABLE_DOCTEST
        >>> from utool.util_tests import *  # NOQA
        >>> func_or_class = get_doctest_examples
        >>> tup  = get_doctest_examples(func_or_class)
        >>> testsrc_list, testwant_list, testlinenum_list, func_lineno, docstr = tup
        >>> result = str(len(testsrc_list) + len(testwant_list))
        >>> print(testsrc_list)
        >>> print(testlinenum_list)
        >>> print(func_lineno)
        >>> print(testwant_list)
        >>> print(result)
        6

    Example1:
        >>> # ENABLE_DOCTEST
        >>> from utool.util_tests import *  # NOQA
        >>> import utool as ut
        >>> func_or_class = ut.tryimport
        >>> tup = get_doctest_examples(func_or_class)
        >>> testsrc_list, testwant_list, testlinenum_list, func_lineno, docstr = tup
        >>> result = str(len(testsrc_list) + len(testwant_list))
        >>> print(testsrc_list)
        >>> print(testlinenum_list)
        >>> print(func_lineno)
        >>> print(testwant_list)
        >>> print(result)
        4

    Example2:
        >>> # DISABLE_DOCTEST
        >>> from utool.util_tests import *  # NOQA
        >>> import ibeis
        >>> func_or_class = ibeis.control.manual_annot_funcs.add_annots
        >>> tup = get_doctest_examples(func_or_class)
        >>> testsrc_list, testwant_list, testlinenum_list, func_lineno, docstr = tup
        >>> result = str(len(testsrc_list) + len(testwant_list))
        >>> print(testsrc_list)
        >>> print(testlinenum_list)
        >>> print(func_lineno)
        >>> print(testwant_list)
        >>> print(result)
        2
    """
    if isinstance(func_or_class, staticmethod):
        func_or_class = func_or_class.__func__
    import utool as ut
    if VERBOSE_TEST:
        print('[util_test][DEPTH 3] get_doctest_examples()')
        print('[util_test] + parsing %r for doctest' % (func_or_class))
        print('[util_test] - name = %r' % (func_or_class.__name__,))
        if hasattr(func_or_class, '__ut_parent_class__'):
            print('[util_test] - __ut_parent_class__ = %r' % (
                func_or_class.__ut_parent_class__,))
        #ut.embed()
    try:
        raise NotImplementedError('FIXME')
        #func_or_class._utinfo['orig_func']
        func_lineno = func_or_class.func_code.co_firstlineno
        # FIXME: doesn't handle decorators well
        #
        # ~~FIXME doesn't account for multiline function definitions
        # actually parse this out~~
        # TODO: rectify with util_insepct get_funcsource with stip def line
        sourcecode = inspect.getsource(func_or_class)
        match = ut.regex_get_match('def [^)]*\\):\n', sourcecode)
        if match is not None:
            num_funcdef_lines = match.group().count('\n')
        else:
            num_funcdef_lines = 1
    except Exception as ex:
        func_lineno = 0
        num_funcdef_lines = 1
        if ut.DEBUG2:
            ut.printex(ex, '[util-test] error getting function line number')

    docstr = ut.get_docstr(func_or_class)
    # Cache because my janky parser is slow
    #with ut.GlobalShelfContext('utool') as shelf:
    #    if False and docstr in shelf:
    #        testsrc_list, testwant_list = shelf[docstr]
    #    else:
    (testheader_list, testsrc_list, testwant_list,
     testlineoffset_list) = parse_doctest_from_docstr(docstr)
    testlinenum_list = [
        func_lineno + num_funcdef_lines + offset
        for offset in testlineoffset_list
    ]
    #       shelf[docstr] = testsrc_list, testwant_list
    if VERBOSE_TEST:
        print('[util_test] L found %d doctests' % (len(testsrc_list),))
    return testsrc_list, testwant_list, testlinenum_list, func_lineno, docstr
    # doctest doesnt do what i want. so I wrote my own primative but effective
    # parser.


def get_module_doctest_tup(testable_list=None, check_flags=True, module=None,
                           allexamples=None, needs_enable=None, N=0,
                           verbose=True, testslow=False):
    """
    Parses module for testable doctesttups
    Depth 2)

    Returns:
        ModuleDoctestTup : (enabled_testtup_list, frame_fpath, all_testflags, module)
            enabled_testtup_list (list): a list of testtup
                testtup (tuple): (name, num, src, want, flag) describes a valid doctest in the module
                    name  (str): test name
                    num   (str): test number of the module / function / class / method
                    src   (str): test source code
                    want  (str): expected test result
                    flag  (str): a valid commandline flag to enable this test
            frame_fpath (str):
                module fpath that will be tested
            module (module):
                the actual module that will be tested
            all_testflags (list):
                the command line arguments that will enable different tests
            exclude_inherited (bool): does not included tests defined in other modules

    Args:
        testable_list (list): a list of functions (default = None)
        check_flags (bool): (default = True)
        module (None): (default = None)
        allexamples (None): (default = None)
        needs_enable (None): (default = None)
        N (int): (default = 0)
        verbose (bool):  verbosity flag(default = True)
        testslow (bool): (default = False)

    Returns:
        tuple: mod_doctest_tup

    CommandLine:
        python -m utool.util_tests --exec-get_module_doctest_tup

    Example:
        >>> # ENABLE_DOCTEST
        >>> from utool.util_tests import *  # NOQA
        >>> import utool as ut
        >>> testable_list = [ut.util_import.package_contents]
        >>> check_flags = False
        >>> module = ut.util_import
        >>> allexamples = False
        >>> needs_enable = False
        >>> N = 0
        >>> verbose = True
        >>> testslow = False
        >>> mod_doctest_tup = get_module_doctest_tup(testable_list, check_flags, module, allexamples, needs_enable, N, verbose, testslow)
        >>> result = ('mod_doctest_tup = %s' % (ut.list_str(mod_doctest_tup, nl=4),))
        >>> print(result)
    """
    #+------------------------
    if VERBOSE_TEST:
        print('[util_test.get_module_doctest tup][DEPTH 2] get_module_doctest tup()')
    import utool as ut  # NOQA
    if needs_enable is None:
        needs_enable = not ut.get_argflag('--enableall')
        #needs_enable = True
    TEST_ALL_EXAMPLES = allexamples or ut.get_argflag(('--allexamples', '--all-examples'))
    parse_testables = True
    force_enable_testnames = []
    if isinstance(testable_list, types.ModuleType):
        # hack
        module = testable_list
        testable_list = []
        testable_name_list = []
    elif testable_list is None:
        testable_list = []
        testable_name_list = []
    else:
        testable_name_list = [ut.get_funcname(func) for func in testable_list]
        parse_testables = False
    #L________________________
    #+------------------------
    # Inspect caller module for testable names
    if module is None:
        frame_fpath = '???'
        try:
            frame = ut.get_caller_stack_frame(N=N)
            main_modname = '__main__'
            frame_name  = frame.f_globals['__name__']
            frame_fpath = frame.f_globals['__file__']
            if frame_name == main_modname:
                module = sys.modules[main_modname]
                entry_modname = ut.get_modname_from_modpath(module.__file__)
                #ut.embed()
                if entry_modname in ['kernprof', 'kernprof-script']:
                    # kernprof clobbers the __main__ variable.
                    # workaround by reimporting the module name
                    import importlib
                    modname = ut.get_modname_from_modpath(frame_fpath)
                    module = importlib.import_module(modname)
        except Exception as ex:
            print(frame.f_globals)
            ut.printex(ex, keys=['frame', 'module'])
            raise
        allexamples = False
    else:
        frame_fpath = module.__file__
        allexamples = True
    #L________________________
    #+------------------------
    # Get testable functions
    if parse_testables:
        try:
            if verbose or VERBOSE_TEST and ut.NOT_QUIET:
                print('[util_test.get module_doctest_tup] Iterating over module funcs')
                print('[util_test.get module_doctest_tup] module =%r' % (module,))

            for key, val in ut.iter_module_doctestable(module,
                                                       include_inherited=False):
                if isinstance(val, staticmethod):
                    docstr = inspect.getdoc(val.__func__)
                else:
                    docstr = inspect.getdoc(val)
                #docstr = ut.ensure_unicode(docstr)
                # FIXME:
                # BUG: We need to verify that this function actually belongs to this
                # module. In util_type ndarray is imported and we try to parse it
                docstr = ut.ensure_unicode(docstr)
                if docstr is not None and docstr.find('Example') >= 0:
                    testable_name_list.append(key)
                    testable_list.append(val)
                else:
                    if VERBOSE_TEST and ut.NOT_QUIET:
                        if docstr.find('Example') >= 0:
                            print('[util_dev] Ignoring (disabled) : %s' % key)
                        else:
                            print('[util_dev] Ignoring (no Example) : %s' % key)
                        #print('[util_dev] DOCTEST DISABLED: %s' % key)
        except Exception as ex:
            print('FAILED')
            print(docstr)
            ut.printex(ex, keys=['frame'])
            raise
    #if verbose:
    #    for val in testable_list:
    #        print('[util_dev] DOCTEST ENABLED: %s' % val)
    #L________________________
    #+------------------------
    # Get testable function examples
    test_sentinals = [
        'ENABLE_DOCTEST',
        #'ENABLE_TEST',
        #'ENABLE_DOCTEST',
        #'ENABLE_UTOOL_DOCTEST',
        #'UTOOL_TEST',
        #'UTOOLTEST'
    ]
    if testslow or ut.get_argflag(('--testall', '--testslow', '--test-slow')):
        test_sentinals.append('SLOW_DOCTEST')
    if testslow or ut.get_argflag(('--testall', '--testunstable')):
        test_sentinals.append('UNSTABLE_DOCTEST')
    # FIND THE TEST NAMES REQUESTED
    # Grab sys.argv enabled tests
    valid_prefix_list = ['--exec-', '--test-']
    for arg in sys.argv:
        for prefix in valid_prefix_list:
            if arg.startswith(prefix):
                testname = arg[len(prefix):].split(':')[0].replace('-', '_')
                force_enable_testnames.append(testname)
                # TODO: parse out requested number up here
                break
    #print(force_enable_testnames)
    def _get_testable_name(testable):
        import utool as ut
        if isinstance(testable, staticmethod):
            testable = testable.__func__
        try:
            testable_name = testable.func_name
        except AttributeError as ex1:
            try:
                testable_name = testable.__name__
            except AttributeError as ex2:
                ut.printex(ex1, ut.list_str(dir(testable)))
                ut.printex(ex2, ut.list_str(dir(testable)))
                raise
        return testable_name

    sorted_testable = sorted(list(set(testable_list)), key=_get_testable_name)
    # Append each testable example
    if VERBOSE_TEST:
        print('Vars:')
        print(' * needs_enable = %r' % (needs_enable,))
        print(' * force_enable_testnames = %r' % (force_enable_testnames,))
        indenter = ut.Indenter('[CHECK_EX]')
        print('len(sorted_testable) = %r' % (len(sorted_testable),))
        indenter.start()
    # PARSE OUT THE AVAILABLE TESTS FOR EACH REQUEST
    local_testtup_list = []
    for testable in sorted_testable:
        testname = _get_testable_name(testable)
        testname2 = None
        if isinstance(testable, staticmethod):
            testable = testable.__func__
        if hasattr(testable, '__ut_parent_class__'):
            # HACK for getting classname.funcname
            testname2 = testable.__ut_parent_class__.__name__ + '.' + testname
            #print('TESTNAME2')
            #print('testname2 = %r' % (testname2,))
        examples, wants, linenums, func_lineno, docstr = get_doctest_examples(testable)
        if len(examples) > 0:
            for testno , srcwant_tup in enumerate(zip(examples, wants)):
                src, want = srcwant_tup
                src_ = ut.regex_replace('from __future__ import.*$', '', src)
                test_disabled = not any([src_.find(s) >= 0 for s in test_sentinals])
                if needs_enable and test_disabled:
                    if testname not in force_enable_testnames:
                        # HACK
                        if testname2 not in force_enable_testnames:
                            #print(force_enable_testnames)
                            #print(testname2)
                            if VERBOSE_TEST:
                                print(' * skipping: %r / %r' % (testname, testname2))
                                #print(src)
                                #print(' * skipping')
                            continue
                        #else:
                        #    testname = testname2
                #ut.embed()
                #. FIXME: you probably should only add one version of the testname to the list,
                # and classname prefixes should probably be enforced
                if testname2 is not None:
                    if VERBOSE_TEST:
                        print(' * HACK adding testname=%r to local_testtup_list' % (testname,))
                    #local_testtup = (testname2, testno, src_, want)
                    local_testtup = ((testname2, testname), testno, src_, want)
                    local_testtup_list.append(local_testtup)
                else:
                    if VERBOSE_TEST:
                        print(' * adding testname=%r to local_testtup_list' % (testname,))
                    local_testtup = (testname, testno, src_, want)
                    local_testtup_list.append(local_testtup)
        else:
            print('WARNING: no examples in %r for testname=%r' % (frame_fpath, testname))
            if verbose:
                print(testable)
                print(examples)
                print(wants)
                print(docstr)
        if VERBOSE_TEST:
            print(' --')
    if VERBOSE_TEST:
        indenter.stop()
    #L________________________
    #+------------------------
    # Get enabled (requested) examples
    if VERBOSE_TEST:
        print('\n-----\n')
        indenter = ut.Indenter('[CHECK_ENABLED]')
        indenter.start()
        print('Need to find which examples are enabled')
        print('len(local_testtup_list) = %r' % (len(local_testtup_list),))
        #print('local_testtup_list = %r' % (local_testtup_list,))
        print('local_testtup_list.T[0:2].T = %s' % ut.list_str(ut.get_list_column(local_testtup_list, [0, 1])))
        #print('(local_testtup_list) = %r' % (local_testtup_list,))
    all_testflags = []
    enabled_testtup_list = []
    distabled_testflags  = []
    subx = ut.get_argval('--subx', type_=int, default=None,
                         help_='Only tests the subxth example')
    for local_testtup in local_testtup_list:
        (nametup, num, src, want) = local_testtup
        if not isinstance(nametup, tuple):
            nametup = (nametup,)
        valid_flags = []
        exec_mode = None
        for prefix, name in ut.iprod(valid_prefix_list, nametup):
            #prefix = '--test-'
            flag1 = prefix + name + ':' + str(num)
            flag2 = prefix + name
            flag3 = prefix + name.replace('_', '-') + ':' + str(num)
            flag4 = prefix + name.replace('_', '-')
            valid_flags += [flag1, flag2, flag3, flag4]
            if VERBOSE_TEST:
                print('Checking for flags*: ' + flag1)
                #print(' checking sys.argv for:\n %s' % (ut.list_str(valid_flags),))
            testflag = ut.get_argflag(valid_flags)
            # TODO: run in exec mode
            exec_mode = prefix == '--exec-'  # NOQA
            if testflag:
                break

        testenabled = TEST_ALL_EXAMPLES  or not check_flags or testflag
        if subx is not None and subx != num:
            continue
        all_testflags.append(flag3)
        if testenabled:
            if VERBOSE_TEST:
                print('... enabling test')
            testtup = TestTuple(name, num, src, want, flag1,
                                frame_fpath=frame_fpath,
                                exec_mode=exec_mode)
            enabled_testtup_list.append(testtup)
        else:
            if VERBOSE_TEST:
                print('... disableing test')
            distabled_testflags.append(flag1)
    if VERBOSE_TEST:
        indenter.stop()

    if ut.get_argflag('--list'):
        # HACK: Should probably just return a richer structure
        print('testable_name_list = %s' % (ut.list_str(testable_name_list),))

    mod_doctest_tup = ModuleDoctestTup(enabled_testtup_list, frame_fpath,
                                       all_testflags, module)
    #L________________________
    return mod_doctest_tup


def doctest_was_requested():
    """ lets a  __main__ codeblock know that util_test should do its thing """
    valid_prefix_list = ['--exec-', '--test-']
    return any([any([arg.startswith(prefix) for prefix in valid_prefix_list]) for arg in sys.argv])


def make_run_tests_script_text(test_headers, test_argvs, quick_tests=None,
                               repodir=None, exclude_list=[]):
    """
    Autogeneration function

    TODO move to util_autogen or just depricate

    Examples:
        >>> from utool.util_tests import *  # NOQA
        >>> import utool  # NOQA
        >>> testdirs = ['~/code/ibeis/test_ibs*.py']
    """
    import utool as ut
    from os.path import relpath, join, dirname  # NOQA

    exclude_list += ['__init__.py']

    # General format of the testing script

    script_fmtstr = ut.codeblock(
        r'''
        #!/bin/bash
        # Runs all tests
        # Win32 path hacks
        export CWD=$(pwd)
        export PYMAJOR="$(python -c "import sys; print(sys.version_info[0])")"

        # <CORRECT_PYTHON>
        # GET CORRECT PYTHON ON ALL PLATFORMS
        export SYSNAME="$(expr substr $(uname -s) 1 10)"
        if [ "$SYSNAME" = "MINGW32_NT" ]; then
            export PYEXE=python
        else
            if [ "$PYMAJOR" = "3" ]; then
                # virtual env?
                export PYEXE=python
            else
                export PYEXE=python2.7
            fi
        fi
        # </CORRECT_PYTHON>

        PRINT_DELIMETER()
        {{
            printf "\n#\n#\n#>>>>>>>>>>> next_test\n\n"
        }}

        export TEST_ARGV="{test_argvs} $@"

        {dirdef_block}

        # Default tests to run
        set_test_flags()
        {{
            export DEFAULT=$1
        {testdefault_block}
        }}
        set_test_flags OFF
        {testdefaulton_block}

        # Parse for bash commandline args
        for i in "$@"
        do
        case $i in --testall)
            set_test_flags ON
            ;;
        esac
        {testcmdline_block}
        done

        BEGIN_TESTS()
        {{
        cat <<EOF
        {runtests_bubbletext}
        EOF
            echo "BEGIN: TEST_ARGV=$TEST_ARGV"
            PRINT_DELIMETER
            num_passed=0
            num_ran=0
            export FAILED_TESTS=''
        }}

        RUN_TEST()
        {{
            echo "RUN_TEST: $@"
            export TEST="$PYEXE $@ $TEST_ARGV"
            $TEST
            export RETURN_CODE=$?
            echo "RETURN_CODE=$RETURN_CODE"
            PRINT_DELIMETER
            num_ran=$(($num_ran + 1))
            if [ "$RETURN_CODE" == "0" ] ; then
                num_passed=$(($num_passed + 1))
            fi
            if [ "$RETURN_CODE" != "0" ] ; then
                export FAILED_TESTS="$FAILED_TESTS\n$TEST"
            fi
        }}

        END_TESTS()
        {{
            echo "RUN_TESTS: DONE"
            if [ "$FAILED_TESTS" != "" ] ; then
                echo "-----"
                printf "Failed Tests:"
                printf "$FAILED_TESTS\n"
                printf "$FAILED_TESTS\n" >> failed_shelltests.txt
                echo "-----"
            fi
            echo "$num_passed / $num_ran tests passed"
        }}

        #---------------------------------------------
        # START TESTS
        BEGIN_TESTS

        {quicktest_block}

        {test_block}

        #---------------------------------------------
        # END TESTING
        END_TESTS
        ''')

    testcmdline_fmtstr = ut.codeblock(
        r'''
        case $i in --notest{header_lower})
            export {testflag}=OFF
            ;;
        esac
        case $i in --test{header_lower})
            export {testflag}=ON
            ;;
        esac
        ''')

    header_test_block_fmstr = ut.codeblock(
        r'''

        #---------------------------------------------
        #{header_text}
        if [ "${testflag}" = "ON" ] ; then
        cat <<EOF
        {header_bubble_text}
        EOF
        {testlines_block}
        fi
        ''')

    #specialargv = '--noshow'
    specialargv = ''
    testline_fmtstr = 'RUN_TEST ${dirvar}/{fpath} {specialargv}'
    testline_fmtstr2 = 'RUN_TEST {fpath} {specialargv}'

    def format_testline(fpath, dirvar):
        if dirvar is None:
            return testline_fmtstr2.format(fpath=fpath, specialargv=specialargv)
        else:
            return testline_fmtstr.format(dirvar=dirvar, fpath=fpath, specialargv=specialargv)

    default_flag_line_list = []
    defaulton_flag_line_list = []
    testcmdline_list = []
    dirdef_list = []
    header_test_block_list = []

    known_tests = ut.ddict(list)

    # Tests to always run
    if quick_tests is not None:
        quicktest_block = '\n'.join(
            ['# Quick Tests (always run)'] +
            ['RUN_TEST ' + testline for testline in quick_tests])
    else:
        quicktest_block = '# No quick tests'

    # Loop over different test types
    for testdef_tup in test_headers:
        header, default, modname, dpath, pats, testcmds = testdef_tup
        # Build individual test type information
        header_upper =  header.upper()
        header_lower = header.lower()
        testflag = header_upper + '_TEST'

        if modname is not None:
            dirvar = header_upper + '_DIR'
            dirdef = ''.join([
                'export {dirvar}=$($PYEXE -c "',
                'import os, {modname};',
                'print(str(os.path.dirname(os.path.dirname({modname}.__file__))))',
                '")']).format(dirvar=dirvar, modname=modname)
            dirdef_list.append(dirdef)
        else:
            dirvar = None

        # Build test dir
        #dirvar = header_upper + '_DIR'
        #dirdef = 'export {dirvar}={dirname}'.format(dirvar=dirvar, dirname=dirname)
        #dirdef_list.append(dirdef)

        # Build command line flags
        default_flag_line = 'export {testflag}=$DEFAULT'.format(testflag=testflag)

        if default:
            defaulton_flag_line = 'export {testflag}=ON'.format(testflag=testflag)
            defaulton_flag_line_list.append(defaulton_flag_line)

        testcmdline_fmtdict = dict(header_lower=header_lower,
                                        testflag=testflag,)
        testcmdline = testcmdline_fmtstr.format(**testcmdline_fmtdict)

        #ut.ls(dpath)

        # VERY HACK BIT OF CODE

        # Get list of tests from patterns
        if testcmds is None:
            if modname is not None:
                module = __import__(modname)
                repo_path = dirname(dirname(module.__file__))
            else:
                repo_path = repodir
            dpath_ = ut.unixpath(util_path.unixjoin(repo_path, dpath))

            if header_upper == 'OTHER':
                # Hacky way to grab any other tests not explicitly seen in this directory
                _testfpath_list = list(set(ut.glob(dpath_, '*.py')) - set(known_tests[dpath_]))
                #_testfpath_list = ut.glob(dpath_, '*.py')
                #set(known_tests[dpath_])
            else:
                _testfpath_list = ut.flatten([ut.glob(dpath_, pat) for pat in pats])

            def not_excluded(x):
                return not any([x.find(exclude) > -1 for exclude in exclude_list])

            _testfpath_list = list(filter(not_excluded, _testfpath_list))

            known_tests[dpath_].extend(_testfpath_list)
            #print(_testfpath_list)
            testfpath_list = [util_path.unixjoin(dpath, relpath(fpath, dpath_))
                              for fpath in _testfpath_list]

            testline_list = [format_testline(fpath, dirvar) for fpath in testfpath_list]
        else:
            testline_list = testcmds

        testlines_block = ut.indentjoin(testline_list).strip('\n')

        # Construct test block for this type
        header_text = header_upper + ' TESTS'
        headerfont = 'cybermedium'
        header_bubble_text =  ut.indent(ut.bubbletext(header_text, headerfont).strip())
        header_test_block_dict = dict(
            testflag=testflag,
            header_text=header_text,
            testlines_block=testlines_block,
            header_bubble_text=header_bubble_text,)
        header_test_block = header_test_block_fmstr.format(**header_test_block_dict)

        # Append to script lists
        header_test_block_list.append(header_test_block)
        default_flag_line_list.append(default_flag_line)
        testcmdline_list.append(testcmdline)

    runtests_bubbletext = ut.bubbletext('RUN TESTS', 'cyberlarge')

    test_block = '\n'.join(header_test_block_list)
    dirdef_block = '\n'.join(dirdef_list)
    testdefault_block = ut.indent('\n'.join(default_flag_line_list))
    testdefaulton_block = '\n'.join(defaulton_flag_line_list)
    testcmdline_block = '\n'.join(testcmdline_list)

    script_fmtdict = dict(
        quicktest_block=quicktest_block,
        runtests_bubbletext=runtests_bubbletext,
        test_argvs=test_argvs, dirdef_block=dirdef_block,
        testdefault_block=testdefault_block,
        testdefaulton_block=testdefaulton_block,
        testcmdline_block=testcmdline_block,
        test_block=test_block,)
    script_text = script_fmtstr.format(**script_fmtdict)

    return script_text


def find_doctestable_modnames(dpath_list=None, exclude_doctests_fnames=[], exclude_dirs=[]):
    """
    Tries to find files with a call to ut.doctest_funcs in the __main__ part
    """
    import utool as ut
    fpath_list, lines_list, lxs_list = ut.grep('doctest_funcs',
                                               dpath_list=dpath_list,
                                               include_patterns=['*.py'],
                                               exclude_dirs=exclude_dirs,
                                               recursive=True)
    exclude_doctests_fnames = set(exclude_doctests_fnames)
    def is_not_excluded(fpath):
        return basename(fpath) not in exclude_doctests_fnames
    doctest_modpath_list = list(filter(is_not_excluded, fpath_list))
    doctest_modname_list = list(map(ut.get_modname_from_modpath, doctest_modpath_list))
    return doctest_modname_list


def find_untested_modpaths(dpath_list=None, exclude_doctests_fnames=[], exclude_dirs=[]):
    import utool as ut
    fpath_list, lines_list, lxs_list = ut.grep('>>> # ENABLE_DOCTEST',
                                               dpath_list=dpath_list,
                                               include_patterns=['*.py'],
                                               exclude_dirs=exclude_dirs,
                                               recursive=True,
                                               inverse=True)
    exclude_doctests_fnames = set(list(exclude_doctests_fnames) + ['__init__.py'])
    def is_not_excluded(fpath):
        fname = basename(fpath)
        return (not fname.startswith('_')) and fname not in exclude_doctests_fnames
    doctest_modpath_list = list(filter(is_not_excluded, fpath_list))
    #doctest_modname_list = list(map(ut.get_modname_from_modpath, doctest_modpath_list))
    return doctest_modpath_list


def show_was_requested():
    """
    returns True if --show is specified on the commandline or you are in
    IPython (and presumably want some sort of interaction
    """
    import plottool as pt
    return pt.show_was_requested()
    #import utool as ut
    #return ut.get_argflag('--show') or ut.inIPython()


class ExitTestException(Exception):
    pass


def quit_if_noshow():
    import utool as ut
    if not (ut.get_argflag(('--show', '--save')) or ut.inIPython()):
        raise ExitTestException('This should be caught gracefully by ut.run_test')


def show_if_requested():
    import plottool as pt
    pt.show_if_requested(N=2)


def main_function_tester(module, ignore_prefix=[], ignore_suffix=[],
                         test_funcname=None):
    """
    Allows a shorthand for __main__ packages of modules to run tests with
    unique function names
    """
    import utool as ut
    print('[utool] main_function_tester')

    test_funcname = ut.get_argval(
        ('--test-func', '--tfunc', '--tf', '--testfunc'),
        type_=str, default=test_funcname,
        help_='specify a function to doctest')
    print('test_funcname = %r' % (test_funcname,))

    if test_funcname is not None:
        globals_ = {}
        #locals_ = {}
        ut.inject_colored_exceptions()
        print('[utool] __main__ Begin Function Test')
        if isinstance(module, six.string_types):
            module = ut.import_modname(module)
        modname_list = ut.package_contents(module, ignore_prefix=ignore_prefix,
                                           ignore_suffix=ignore_suffix)
        # Get only the modules already imported
        have_modnames = [modname for modname in modname_list
                         if modname in sys.modules]
        #missing_modnames = [modname for modname in modname_list
        #                    if modname not in sys.modules]
        module_list = ut.dict_take(sys.modules, have_modnames)
        # Search for the module containing the function
        test_func = None
        test_module = None
        test_classname = None
        if test_funcname.find('.') != -1:
            test_classname, test_funcname = test_funcname.split('.')
        if test_funcname.find(':') != -1:
            test_funcname, testno = test_funcname.split(':')
            testno = int(testno)
        else:
            testno = 0
        if test_classname is None:
            for module_ in module_list:
                #test_funcname = 'find_installed_tomcat'
                if test_funcname in module_.__dict__:
                    test_module = module_
                    test_func = test_module.__dict__[test_funcname]
                    break
        else:
            for module_ in module_list:
                #test_funcname = 'find_installed_tomcat'
                if test_classname in module_.__dict__:
                    test_module = module_
                    test_class = test_module.__dict__[test_classname]
                    test_func = test_class.__dict__[test_funcname]

        if test_func is not None:
            func_globals = meta_util_six.get_funcglobals(test_func)
            globals_.update(func_globals)
            testsrc = ut.get_doctest_examples(test_func)[0][testno]
            try:
                if ut.get_argflag(('--cmd', '--embed')):
                    testsrc += '\nimport utool as ut; ut.embed()'  # TODO RECTIFY WITH EXEC DOCTEST
                code = compile(testsrc, '<string>', 'exec')
                print('testsrc = \n%s' % (ut.indent(testsrc, '>>> '),))
                exec(code, globals_)  # , locals_)
            except ExitTestException:
                print('Test exited before show')
                pass
            retcode = 0
            print('Finished function test. exiting')
            sys.exit(retcode)
        else:
            print('Did not find any function named %r ' % (test_funcname,))
            print('Searched ' + ut.list_str([mod.__name__
                                             for mod in module_list]))
            sys.exit(0)


if __name__ == '__main__':
    """
    CommandLine:
        python -c "import utool, utool.util_tests; utool.doctest_funcs(utool.util_tests)"
        python -m utool.util_tests
        python -m utool.util_tests --allexamples
        python -m utool.util_tests

        python -c "import utool; utool.doctest_funcs(module=utool.util_tests, needs_enable=False)"
        /model/preproc/preproc_chip.py --allexamples
    """
    import multiprocessing
    import utool as ut  # NOQA
    multiprocessing.freeze_support()
    #doctest_funcs()
    ut.doctest_funcs()
