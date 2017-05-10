#!/usr/bin/env python

import os
import re
import subprocess
import sys
import yaml


PACKAGE_PATTERN = re.compile(r'[_a-z]+')


def is_travis():
    return (('TRAVIS' in os.environ) and
            (os.environ.get('TRAVIS') == 'true'))


def is_travis_push():
    return (('TRAVIS_EVENT_TYPE' in os.environ) and
            (os.environ.get('TRAVIS_EVENT_TYPE') == 'push'))


def is_travis_pr():
    return (('TRAVIS_EVENT_TYPE' in os.environ) and
            (os.environ.get('TRAVIS_EVENT_TYPE') == 'pull_request'))


def get_travis_pr_commit_range():
    if 'TRAVIS_COMMIT_RANGE' not in os.environ:
        raise EnvironmentError('TRAVIS_COMMIT_RANGE not found')
    return os.environ.get('TRAVIS_COMMIT_RANGE')


def get_travis_pr_base_branch():
    if 'TRAVIS_BRANCH' not in os.environ:
        raise EnvironmentError('TRAVIS_BRANCH not found')
    return os.environ.get('TRAVIS_BRANCH')


def get_travis_pr_request_branch():
    if 'TRAVIS_PULL_REQUEST_BRANCH' not in os.environ:
        raise EnvironmentError('TRAVIS_PULL_REQUEST_BRANCH not found')
    return os.environ.get('TRAVIS_PULL_REQUEST_BRANCH')


def git_dir():
    path = subprocess.check_output(['git', 'rev-parse', '--git-dir']).strip()
    return os.path.abspath(path)


def toplevel_dir():
    path = subprocess.check_output(['git', 'rev-parse', '--show-toplevel']).strip()
    return os.path.abspath(path)


def unshallow_git_if_shallow():
    subprocess.check_call(['git', 'config', 'remote.origin.fetch', '+refs/heads/*:refs/remotes/origin/*'])
    if os.path.exists(os.path.join(git_dir(), 'shallow')):
        subprocess.check_call(['git', 'fetch', '--unshallow'])


def git_diff(commit_range):
    return subprocess.check_output(['git', 'diff', commit_range])


def get_package_name_from_path(path):
    root, ext = os.path.splitext(os.path.basename(path))
    return root if (os.path.isfile(path) and ext == '.yml' and PACKAGE_PATTERN.match(root)) else None


def get_package_data(path):
    with open(path) as f:
        return yaml.load(f)


def check_package_data(data):
    return (('url' in data) and
            isinstance(data['url'], str) and
            # TODO: Confirm valid URL.
            ('authors' in data) and
            isinstance(data['authors'], list))


def check_all_packages_valid():
    packages_path = os.path.join(toplevel_dir(), 'packages')

    # If packages/ does not exist, it is okay.
    if not os.path.isdir(packages_path):
        return True

    for package_file_relative_path in os.listdir(packages_path):
        package_file_path = os.path.join(packages_path, package_file_relative_path)
        package_name = get_package_name_from_path(package_file_path)

        # If invalid entry (file / dir) exists in packages, it is not accepted.
        if not package_name:
            return False

        # An exception may be raised, which is considered just failing.
        package_data = get_package_data(package_file_path)

        if not check_package_data(package_data):
            return False

    return True


def main(argv):
    assert(check_all_packages_valid())

    unshallow_git_if_shallow()
    if is_travis():
        if is_travis_pr():
            print git_diff(get_travis_pr_commit_range())
        elif is_travis_push():
            print '(The build is based on push.)'

    print 'Done.'


if __name__ == '__main__':
    sys.exit(main(sys.argv))
