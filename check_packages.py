#!/usr/bin/env python

import os
import subprocess
import sys


def is_travis():
    return (('TRAVIS' in os.environ) and
            (os.environ.get('TRAVIS') == 'true'))


def is_travis_push():
    return (('TRAVIS_EVENT_TYPE' in os.environ) and
            (os.environ.get('TRAVIS_EVENT_TYPE') == 'push'))


def is_travis_pr():
    return (('TRAVIS_EVENT_TYPE' in os.environ) and
            (os.environ.get('TRAVIS_EVENT_TYPE') == 'pull_request'))


def get_travis_pr_base_branch():
    if 'TRAVIS_BRANCH' not in os.environ:
        raise EnvironmentError('TRAVIS_BRANCH not found')
    return os.environ.get('TRAVIS_BRANCH')


def get_travis_pr_request_branch():
    if 'TRAVIS_PULL_REQUEST_BRANCH' not in os.environ:
        raise EnvironmentError('TRAVIS_PULL_REQUEST_BRANCH not found')
    return os.environ.get('TRAVIS_PULL_REQUEST_BRANCH')


def get_git_dir():
    git_dir = subprocess.check_output(['git', 'rev-parse', '--git-dir'])
    return os.path.abspath(git_dir)


def unshallow_git_if_shallow():
    subprocess.check_call(['git', 'config', 'remote.origin.fetch', '+refs/heads/*:refs/remotes/origin/*'])
    if os.path.exists(os.path.join(get_git_dir(), 'shallow')):
        subprocess.check_call(['git', 'fetch', '--unshallow'])


def git_diff(base, request):
    return subprocess.check_output(['git', 'diff', base, request])


def main(argv):
    unshallow_git_if_shallow()
    if is_travis():
        if is_travis_pr():
            print git_diff(get_travis_pr_base_branch(), get_travis_pr_request_branch())
        elif is_travis_push():
            print 'PUSH'
    print 'Done.'


if __name__ == '__main__':
    sys.exit(main(sys.argv))
