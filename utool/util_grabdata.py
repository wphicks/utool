from __future__ import absolute_import, division, print_function
from os.path import dirname, split, join, splitext, exists, realpath, basename, commonprefix
import sys
import zipfile
import tarfile
import urllib
import time
from . import util_path
from . import util_cplat
from .util_inject import inject
print, print_, printDBG, rrr, profile = inject(__name__, '[grabdata]')


__QUIET__ = '--quiet' in sys.argv
BadZipfile = zipfile.BadZipfile


def unarchive_file(archive_fpath):
    print('Unarchive: %r' % archive_fpath)
    if tarfile.is_tarfile(archive_fpath):
        return untar_file(archive_fpath)
    elif zipfile.is_zipfile(archive_fpath):
        return unzip_file(archive_fpath)
    else:
        raise AssertionError('unknown archive format')


def untar_file(targz_fpath):
    tar_file = tarfile.open(targz_fpath, 'r:gz')
    output_dir = dirname(targz_fpath)
    archive_namelist = [mem.path for mem in tar_file.getmembers()]
    _extract_archive(tar_file, archive_namelist, output_dir)


def unzip_file(zip_fpath, force_commonprefix=True):
    zip_file = zipfile.ZipFile(zip_fpath)
    output_dir  = dirname(zip_fpath)
    archive_namelist = zip_file.namelist()
    if force_commonprefix and commonprefix(archive_namelist) == '':
        name, ext = splitext(basename(zip_fpath))
        output_dir = join(output_dir, name)
    _extract_archive(zip_file, archive_namelist, output_dir)


def _extract_archive(archive_file, archive_namelist, output_dir):
    for member in archive_namelist:
        (dname, fname) = split(member)
        dpath = join(output_dir, dname)
        util_path.ensurepath(dpath)
        if not __QUIET__:
            print('[utool] Unarchive ' + fname + ' in ' + dpath)
        archive_file.extract(member, path=output_dir)


def download_url(url, filename):
    # From http://blog.moleculea.com/2012/10/04/urlretrieve-progres-indicator/
    start_time_ptr = [0]
    def reporthook(count, block_size, total_size):
        if count == 0:
            start_time_ptr[0] = time.time()
            return
        duration = time.time() - start_time_ptr[0]
        if duration == 0:
            duration = 1E-9
        progress_size = int(count * block_size)
        speed = int(progress_size / (1024 * duration))
        percent = int(count * block_size * 100 / total_size)
        sys.stdout.write('\r...%d%%, %d MB, %d KB/s, %d seconds passed' %
                         (percent, progress_size / (1024 * 1024), speed, duration))
        sys.stdout.flush()
    print('[utool] Downloading url=%r to filename=%r' % (url, filename))
    urllib.urlretrieve(url, filename=filename, reporthook=reporthook)


def fix_dropbox_link(dropbox_url):
    """ Dropbox links should be en-mass downloaed from dl.dropbox """
    return dropbox_url.replace('www.dropbox', 'dl.dropbox')


def split_archive_ext(path):
    special_exts = ['.tar.gz', '.tar.bz2']
    for ext in special_exts:
        if path.endswith(ext):
            name, ext = path[:-len(ext)], path[-len(ext):]
            break
    else:
        name, ext = splitext(path)
    return name, ext


def grab_file_url(file_url, ensure=True, appname='utool', download_dir=None):
    file_url = fix_dropbox_link(file_url)
    fname = split(file_url)[1]
    # Download zipfile to
    if download_dir is None:
        download_dir = util_cplat.get_app_resource_dir(appname)
    # Zipfile should unzip to:
    fpath = join(download_dir, fname)
    if ensure:
        util_path.ensurepath(download_dir)
        if not exists(fpath):
            # Download testdata
            print('[utool] Downloading file %s' % fpath)
            download_url(file_url, fpath)
    util_path.assert_exists(fpath)
    return fpath


def grab_zipped_url(zipped_url, ensure=True, appname='utool', download_dir=None):
    """
    Input zipped_url - this must look like:
    http://www.spam.com/eggs/data.zip
    eg:
    https://dl.dropboxusercontent.com/s/of2s82ed4xf86m6/testdata.zip
    """
    zipped_url = fix_dropbox_link(zipped_url)
    zip_fname = split(zipped_url)[1]
    data_name = split_archive_ext(zip_fname)[0]
    # Download zipfile to
    if download_dir is None:
        download_dir = util_cplat.get_app_resource_dir(appname)
    # Zipfile should unzip to:
    data_dir = join(download_dir, data_name)
    if ensure:
        util_path.ensurepath(download_dir)
        if not exists(data_dir):
            # Download and unzip testdata
            zip_fpath = realpath(join(download_dir, zip_fname))
            print('[utool] Downloading archive %s' % zip_fpath)
            download_url(zipped_url, zip_fpath)
            unarchive_file(zip_fpath)
            util_path.delete(zip_fpath)  # Cleanup
    util_path.assert_exists(data_dir)
    return data_dir
