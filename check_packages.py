#!/usr/bin/env python

import os
import subprocess
import sys


def get_git_dir():
    git_dir = subprocess.check_output(['git', 'rev-parse', '--git-dir'])
    return os.path.abspath(git_dir)


def unshallow_git_if_shallow():
    subprocess.check_call(['git', 'config', 'remote.origin.fetch', '"+refs/heads/*:refs/remotes/origin/*"'])
    if os.path.exists(os.path.join(get_git_dir(), 'shallow')):
        subprocess.check_call(['git', 'fetch', '--unshallow'])


def main(argv):
    unshallow_git_if_shallow()
    subprocess.check_call(['printenv'])
    print 'Done.'


if __name__ == '__main__':
    sys.exit(main(sys.argv))
