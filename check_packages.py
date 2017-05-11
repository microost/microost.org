#!/usr/bin/env python

import json
import os
import re
import subprocess
import sys
import urllib2
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


def get_travis_pr_number():
    if 'TRAVIS_PULL_REQUEST' not in os.environ:
        raise EnvironmentError('TRAVIS_PULL_REQUEST not found')
    if os.environ.get('TRAVIS_PULL_REQUEST') == 'false':
        raise EnvironmentError('TRAVIS_PULL_REQUEST is false')
    return int(os.environ.get('TRAVIS_PULL_REQUEST'))


def get_pr_author(pr_number):
    connection = urllib2.urlopen('https://api.github.com/repos/microost/microost.org/pulls/%d' % pr_number)
    pr_author = json.loads(connection.read().decode("utf-8"))['user']['login']
    connection.close()
    return pr_author


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


def git_diff_filenames(commit_range):
    filenames = subprocess.check_output(['git', 'diff', '--name-only', commit_range])
    return [filename.strip() for filename in filenames.split('\n') if len(filename.strip()) > 0]


def get_file_contents_on_revision(revision, relative_path):
    process = subprocess.Popen(['git', 'show', '%s:%s' % (revision, relative_path)],
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
    stdout_data, stderr_data = process.communicate()
    if stderr_data.startswith('fatal'):
        return None
    return stdout_data


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
            ('owners' in data) and
            isinstance(data['owners'], list))


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


def check_package_changes_authorized(filenames, pr_author, pr_base_branch, privileged_users):
    if pr_author in privileged_users:
        print '%s is a privileged user.' % pr_author
        return True

    packages = []
    for filename in filenames:
        if filename.startswith('packages/'):
            packages.append(filename)

    if len(packages) == 0:
        print 'No package is changed.'
        return True

    if len(packages) > 1:
        print 'Multiple packages are changed at the same time.'
        return False
    if len(filenames) > 1:
        print 'A package and other file(s) are changed at the same time.'
        return False

    base_package_data_str = get_file_contents_on_revision(pr_base_branch, packages[0])
    if not base_package_data_str:
        print 'Only one new package is added.'
        return True

    base_package_data = yaml.load()
    if pr_author in base_package_data['owners']:
        print 'Only one package is changed by an owner.'
        return True

    print 'Only one package is changed, but by a non-owner.'
    return False


def main(argv):
    assert(check_all_packages_valid())
    unshallow_git_if_shallow()
    if is_travis():
        if is_travis_pr():
            filenames = git_diff_filenames(get_travis_pr_commit_range())
            pr_number = get_travis_pr_number()
            print 'Changed files in the pull request #%d:' % pr_number
            for filename in filenames:
                print filename
            assert(check_package_changes_authorized(
                filenames, get_pr_author(pr_number), get_travis_pr_base_branch(), []))
        elif is_travis_push():
            print 'The build is not based on pull request.'

    print 'Done.'


if __name__ == '__main__':
    sys.exit(main(sys.argv))
