#!/usr/bin/env python3
'''module for reading pndbuild files'''
import os

class PNDBUILDException(Exception):
    '''Exception raised when PNDBUILD module related failure occured'''
    pass

def _find_bash():
    '''find system bash path'''
    bash = None
    dirs = [dre or "." for dre in os.environ.get("PATH", "").split(":")]
    if not dirs:
        dirs = ['/bin', '/usr/bin']
    for dre in dirs:
        exe = os.path.join(dre, 'bash')
        if os.path.exists(exe):
            bash = exe
            break
    return bash

def _parse_set_value(value):
    '''parse value returned by bash's set'''
    import re, shlex
    value = value.strip()
    if (value[0] == '"' and value[-1] == '"') or \
       (value[0] == "'" and value[-1] == "'"):
        value = value[1:-1]
    elif value[0] == '(' and value[-1] == ')':
        value = re.sub(r'\[[0-9]*\]=', '', value)[1:-1]
        value = shlex.split(value)
    return value

def read(path):
    '''read PNDBUILD file and return variables'''
    if os.path.basename(path) != 'PNDBUILD':
        raise PNDBUILDException('Must be a PNDBUILD file')

    bash = _find_bash()
    if not bash:
        raise PNDBUILDException('Bash does not exist in system')

    oldpath = os.getcwd()
    dirname = os.path.dirname(path)
    if dirname:
        os.chdir(dirname)

    pndbuild = {}
    command = ['env', '-i', 'PATH=""',
               '{}'.format(bash), '-rc', 'source PNDBUILD; set -o posix; set']

    import subprocess
    proc = subprocess.Popen(command, stdout=subprocess.PIPE)
    for line in proc.stdout:
        (key, _, value) = line.decode('UTF-8').partition("=")
        if key == '_' or not value or key.isupper():
            continue
        pndbuild[key] = _parse_set_value(value)

    proc.communicate()
    os.chdir(oldpath)
    return pndbuild

def readgz(path):
    '''read PNDBUILD from tar.gz'''
    dirname = os.path.dirname(path)
    basename = os.path.basename(path)
    split = basename.rsplit('.', 1)
    if split:
        basename = split[0]

    print(basename)
    if not basename or os.path.exists(basename):
        raise PNDBUILDException('Invalid path or path exists')

    def find(name, path):
        '''find file in path'''
        for root, dummy_dirs, files in os.walk(path):
            if name in files:
                return os.path.join(root, name)

    import tarfile, shutil
    fle = tarfile.open(path, 'r:gz')

    extpath = basename
    if dirname:
        extpath = os.path.join(dirname, extpath)
    fle.extractall(extpath)

    pndbuildpath = find('PNDBUILD', extpath)
    if not pndbuildpath:
        shutil.rmtree(extpath)
        raise PNDBUILDException('PNDBUILD was not found inside archive')

    recipedic = {}
    data = None
    try:
        recipedic = read(pndbuildpath)
        with open(pndbuildpath, 'r') as fle2:
            data = fle2.read()
    except Exception as exc:
        shutil.rmtree(extpath)
        raise exc

    shutil.rmtree(extpath)
    return (recipedic, data)

if __name__ == '__main__':
    import sys, pprint
    PND = read(sys.argv[1])
    pprint.pprint(PND)

#  vim: set ts=8 sw=4 tw=0 :
