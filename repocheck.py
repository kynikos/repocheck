#!/usr/bin/env python

# repocheck - Check the status of code repositories under a root directory.
# Copyright (C) 2015 Dario Giovannetti <dev@dariogiovannetti.net>
#
# This file is part of repocheck.
#
# repocheck is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# repocheck is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with repocheck.  If not, see <http://www.gnu.org/licenses/>.

import sys
import argparse
import os
from subprocess import Popen, PIPE


class RepoCheck:
    def __init__(self, update_remotes=False, rootdirs=('./', ),
                 followlinks=False, nested_repos=True, rel_paths=False):
        # __init__'s arguments must match the argparse attributes and their
        #  default values
        # Having a separate class allows using it as a library from another
        #  script
        self.INSTALLED_VCS = (_Git, )
        self.repos = {}
        # TODO: It should also work if executed from within a folder inside a
        #       repository (bug #6)
        for rootdir in rootdirs:
            for reldirpath, dirnames, filenames in os.walk(
                    rootdir, followlinks=followlinks):
                for Repo in self.INSTALLED_VCS:
                    if Repo.DOTDIR in dirnames:
                        repo = Repo(reldirpath, update_remotes, rel_paths)
                        self.repos[repo.absdirpath] = repo
                        break
                else:
                    continue
                if not nested_repos:
                    dirnames.clear()


class _Repository:
    COMMAND = None
    DOTDIR = None

    def __init__(self, reldirpath, update_remotes, rel_paths):
        self.absdirpath = os.path.abspath(reldirpath)
        # Use the absolute path so that the correct repo name
        #  is displayed even if called from the root folder
        #  of a repository
        self.displayname = reldirpath if rel_paths else os.path.basename(
                                                            self.absdirpath)

        if update_remotes:
            print('Updating {} remotes...'.format(self.displayname))
            self.do_update_remotes()

        self.uncommitted, self.untracked = self.get_pending_changes()
        self.current_branch = self.get_current_branch()
        self.remote_to_branches = {}
        self.branch_to_remotes_to_status = {}
        self.branch_stats = {'=': 0, '>': 0, '<': 0, '#': 0, '}': 0, '{': 0}

        for remote, branch in self.iter_remote_branches():
            try:
                self.remote_to_branches[remote].append(branch)
            except KeyError:
                self.remote_to_branches[remote] = [branch, ]
            try:
                self.branch_to_remotes_to_status[branch]
            except KeyError:
                self.branch_to_remotes_to_status[branch] = {remote: None}
            else:
                self.branch_to_remotes_to_status[branch][remote] = None

        for branch in self.iter_local_branches():
            try:
                remotes_to_status = self.branch_to_remotes_to_status[branch]
            except KeyError:
                # The branch hasn't been pushed to any remote
                self.branch_to_remotes_to_status[branch] = {}
                self.branch_stats['}'] += 1
            else:
                for remote in remotes_to_status:
                    remote_branch = '/'.join((remote, branch))
                    localahead = self.count_commits_ahead(branch,
                                                          remote_branch)
                    remoteahead = self.count_commits_ahead(remote_branch,
                                                           branch)
                    remotes_to_status[remote] = (localahead, remoteahead)
                    if localahead > 0:
                        if remoteahead > 0:
                            self.branch_stats['#'] += 1
                        else:
                            self.branch_stats['>'] += 1
                    else:
                        if remoteahead > 0:
                            self.branch_stats['<'] += 1
                        else:
                            self.branch_stats['='] += 1

        for branch in self.branch_to_remotes_to_status:
            for remote in self.branch_to_remotes_to_status[branch]:
                if self.branch_to_remotes_to_status[branch][remote] is None:
                    self.branch_stats['{'] += 1

    def _exec(self, *args):
        process = Popen([self.COMMAND] + list(args), stdout=PIPE,
                        cwd=self.absdirpath)
        return process.stdout.read().decode()


class _Git(_Repository):
    COMMAND = 'git'
    DOTDIR = '.git'

    def do_update_remotes(self):
        self._exec('remote', 'update')

    def get_pending_changes(self):
        uncommitted = []
        untracked = []
        for line in self._exec('status', '--porcelain').splitlines():
            if line.startswith('?'):
                untracked.append((line[:2], line[3:]))
            else:
                uncommitted.append((line[:2], line[3:]))
        return (uncommitted, untracked)

    def get_current_branch(self):
        return self._exec('rev-parse', '--abbrev-ref', 'HEAD').strip()

    def iter_local_branches(self):
        return (branch[2:] for branch in self._exec('branch', '--no-color'
                                                    ).splitlines())

    def iter_remote_branches(self):
        for line in self._exec('branch', '--remotes', '--no-color'
                               ).splitlines():
            remote, branch = line[2:].split('/', maxsplit=1)
            # It's important to also look for a space after 'HEAD'
            if branch[:5] != 'HEAD ':
                yield (remote, branch)

    def count_commits_ahead(self, branch_ahead, branch_behind):
        # 'git rev-list' with the '..' notation actually only tells which
        #  commits are in branch_ahead but not in branch_behind, which means
        #  that the two branches may be diverging, and the reverse command
        #  should be executed too
        return len(self._exec('rev-list',
                   '..'.join((branch_behind, branch_ahead))).splitlines())


class _Mercurial(_Repository):
    # TODO: Implement and add to RepoCheck.INSTALLED_VCS
    #       Also update README.md
    #       (bug #7)
    pass


class _Subversion(_Repository):
    # TODO: Implement and add to RepoCheck.INSTALLED_VCS
    #       Also update README.md
    #       (bug #7)
    pass


class Viewer:
    def __init__(self, repos):
        self.repos = repos

    @staticmethod
    def get_colors(no_colors):
        # TODO: Move to lib.py.console-colors repository
        if no_colors:
            RED = REDBOLD = GREEN = GREENBOLD = YELLOW = YELLOWBOLD = BLUE = \
                BLUEBOLD = PURPLE = PURPLEBOLD = CYAN = CYANBOLD = WHITE = \
                WHITEBOLD = RESET = ''
        else:
            RED = "\033[0;31m"
            REDBOLD = "\033[1;31m"
            GREEN = "\033[0;32m"
            GREENBOLD = "\033[1;32m"
            YELLOW = "\033[0;33m"
            YELLOWBOLD = "\033[1;33m"
            BLUE = "\033[0;34m"
            BLUEBOLD = "\033[1;34m"
            PURPLE = "\033[0;35m"
            PURPLEBOLD = "\033[1;35m"
            CYAN = "\033[0;36m"
            CYANBOLD = "\033[1;36m"
            WHITE = "\033[0;37m"
            WHITEBOLD = "\033[1;37m"
            RESET = "\033[0m"
        return (RED, REDBOLD, GREEN, GREENBOLD, YELLOW, YELLOWBOLD, BLUE,
                BLUEBOLD, PURPLE, PURPLEBOLD, CYAN, CYANBOLD, WHITE,
                WHITEBOLD, RESET)

    @classmethod
    def print_legend(cls, no_colors=False):
        RED, REDBOLD, GREEN, GREENBOLD, YELLOW, YELLOWBOLD, BLUE, \
            BLUEBOLD, PURPLE, PURPLEBOLD, CYAN, CYANBOLD, WHITE, \
            WHITEBOLD, RESET = cls.get_colors(no_colors)
        print("""Workspace symbols:
    {red}*{reset}: modified, but uncommitted file
    {cyan}?{reset}: untracked file
Branch symbols:
    {green}={reset}: local branch in sync with the remote
    {red}>{reset}: local branch ahead of the remote
    {cyan}<{reset}: local branch behind the remote
    {red}#{reset}: local branch diverging from the remote
    {red}}}{reset}: local branch never pushed to the remote
    {green}{{{reset}: remote branch never fetched""".format(
                                green=GREEN, cyan=CYAN, red=RED, reset=RESET))

    def display_results(self, expanded=False, all_=False, no_colors=False):
        # display_results's arguments must match the argparse attributes and
        #  their default values
        INDENT = ' ' * 4
        RED, REDBOLD, GREEN, GREENBOLD, YELLOW, YELLOWBOLD, BLUE, \
            BLUEBOLD, PURPLE, PURPLEBOLD, CYAN, CYANBOLD, WHITE, \
            WHITEBOLD, RESET = self.get_colors(no_colors)

        def color(text, COLOR):
            return ''.join((COLOR, text, RESET))

        displayf = self._display_expanded if expanded else self._display_short

        for repopath in sorted(self.repos.keys()):
            displayf(self.repos[repopath], all_, INDENT, color, RED, REDBOLD,
                     GREEN, GREENBOLD, YELLOW, YELLOWBOLD, BLUE, BLUEBOLD,
                     PURPLE, PURPLEBOLD, CYAN, CYANBOLD, WHITE, WHITEBOLD,
                     RESET)

    def _display_expanded(self, repo, all_, INDENT, color, RED, REDBOLD, GREEN,
                          GREENBOLD, YELLOW, YELLOWBOLD, BLUE, BLUEBOLD,
                          PURPLE, PURPLEBOLD, CYAN, CYANBOLD, WHITE, WHITEBOLD,
                          RESET):
        workspace = []
        branches = []
        action_required = False

        for status, filepath in repo.uncommitted:
            workspace.append('{} {}'.format(color(status, RED), filepath))
            action_required = True
        for status, filepath in repo.untracked:
            workspace.append('{} {}'.format(color(status, CYAN), filepath))
            action_required = True

        if len(repo.remote_to_branches) > 1:
            for branch in sorted(repo.branch_to_remotes_to_status.keys()):
                branchstr = color(branch, GREEN) \
                            if branch == repo.current_branch \
                            else branch
                if len(repo.branch_to_remotes_to_status[branch]) == 0:
                    branches.append('{} {}'.format(color('}', RED), branchstr))
                    action_required = True
                else:
                    for remote in sorted(repo.branch_to_remotes_to_status[
                                                                    branch]):
                        status = repo.branch_to_remotes_to_status[branch][
                                                                        remote]
                        if status is None:
                            if all_:
                                branches.append('{} {} ({})'.format(color('{',
                                                GREEN), branchstr, remote))
                        else:
                            if status[0] > 0:
                                if status[1] > 0:
                                    branches.append('{} {} ({}) {}'.format(
                                        color('#', RED), branchstr, remote,
                                        color('|'.join((str(status[0]),
                                              str(status[1]))), YELLOW)))
                                else:
                                    branches.append('{} {} ({}) {}'.format(
                                        color('>', RED), branchstr, remote,
                                        color(str(status[0]), YELLOW)))
                                action_required = True
                            elif status[1] > 0:
                                branches.append('{} {} ({}) {}'.format(
                                    color('<', CYAN), branchstr, remote,
                                    color(str(status[1]), YELLOW)))
                                action_required = True
                            elif all_:
                                branches.append('{} {} ({})'.format(
                                    color('=', GREEN), branchstr, remote))
        else:
            for branch in sorted(repo.branch_to_remotes_to_status.keys()):
                branchstr = color(branch, GREEN) \
                            if branch == repo.current_branch \
                            else branch
                if len(repo.branch_to_remotes_to_status[branch]) == 0:
                    branches.append('{} {}'.format(color('}', RED), branchstr))
                    action_required = True
                else:
                    remote = tuple(repo.branch_to_remotes_to_status[branch
                                                                    ].keys()
                                   )[0]
                    status = repo.branch_to_remotes_to_status[branch][remote]
                    if status is None:
                        if all_:
                            branches.append('{} {}'.format(color('{', GREEN),
                                            branchstr))
                    else:
                        if status[0] > 0:
                            if status[1] > 0:
                                branches.append('{} {} {}'.format(color('#',
                                                                        RED),
                                                branchstr, color('|'.join((
                                                    str(status[0]),
                                                    str(status[1]))), YELLOW)))
                            else:
                                branches.append('{} {} {}'.format(color('>',
                                                                        RED),
                                                branchstr, color(
                                                    str(status[0]), YELLOW)))
                            action_required = True
                        elif status[1] > 0:
                            branches.append('{} {} {}'.format(
                                color('<', CYAN),
                                branchstr, color(str(status[1]),
                                                 YELLOW)))
                            action_required = True
                        elif all_:
                            branches.append('{} {}'.format(
                                color('=', GREEN), branchstr))

        if action_required:
            print(color(repo.displayname, REDBOLD))
            if workspace:
                for line in workspace:
                    print(INDENT * 2 + line)
            for line in branches:
                print(INDENT + line)
        elif all_:
            print(color(repo.displayname, GREENBOLD))
            if workspace:
                for line in workspace:
                    print(INDENT * 2 + line)
            for line in branches:
                print(INDENT + line)

    def _display_short(self, repo, all_, INDENT, color, RED, REDBOLD, GREEN,
                       GREENBOLD, YELLOW, YELLOWBOLD, BLUE, BLUEBOLD,
                       PURPLE, PURPLEBOLD, CYAN, CYANBOLD, WHITE, WHITEBOLD,
                       RESET):
        workspace = []
        branches = []
        action_required = False

        if repo.uncommitted:
            workspace.append(color('{}*'.format(len(repo.uncommitted)), RED))
            action_required = True
        if repo.untracked:
            workspace.append(color('{}?'.format(len(repo.untracked)), CYAN))
            action_required = True

        if all_:
            for type_ in ('=', '{'):
                if repo.branch_stats[type_] > 0:
                    branches.append(color(''.join((str(repo.branch_stats[type_]
                                                       ), type_)), GREEN))
        if repo.branch_stats['<'] > 0:
            branches.append(color(''.join((str(repo.branch_stats['<']), '<')),
                            CYAN))
            action_required = True
        for type_ in ('>', '#', '}'):
            if repo.branch_stats[type_] > 0:
                branches.append(color(''.join((str(repo.branch_stats[type_]),
                                      type_)), RED))
                action_required = True

        if all_:
            if action_required:
                print('{} {}'.format(color(repo.displayname, REDBOLD),
                                     ' '.join(workspace + branches)))
            else:
                print('{} {}'.format(repo.displayname,
                                     ' '.join(workspace + branches)))
        elif action_required:
            print('{} {}'.format(repo.displayname,
                                 ' '.join(workspace + branches)))


def main():
    cliparser = argparse.ArgumentParser(description="repocheck - Check the "
                                        "status of code repositories under a "
                                        "root directory.", add_help=True)
    cliparser.add_argument('-u', '--update-remotes', action='store_true',
                           help='fetch updates for the remotes before '
                                'checking a repository')
    cliparser.add_argument('-a', '--all', action='store_true',
                           help='show all repositories and branches even when '
                                'they require no action')
    cliparser.add_argument('-e', '--expanded', action='store_true',
                           help='print detailed information for every '
                                'repository')
    cliparser.add_argument('-p', '--rel-paths', action='store_true',
                           help='print the relative paths to the repositories '
                                'instead of just their names')
    cliparser.add_argument('-l', '--follow-links', action='store_true',
                           help='follow links to directories (*warning:* this '
                                'can lead to infinite recursion if a link '
                                'points to an ancestor directory of itself)')
    cliparser.add_argument('-n', '--no-nested-repos', action='store_true',
                           help='do not look for repositories in repository '
                                'subdirectories')
    cliparser.add_argument('-L', '--legend', action='store_true',
                           help='display a legend for the used symbols and '
                                'exit')
    cliparser.add_argument('--no-colors', action='store_true',
                           help='do not use colors in the output')
    cliparser.add_argument('rootdirs', nargs='*', default=('./', ),
                           metavar='PATH',
                           help='root directories from which search '
                                'recursively for repositories; if no paths '
                                'are given, the working directory is used')
    cliargs = cliparser.parse_args()
    if cliargs.legend:
        Viewer.print_legend(cliargs.no_colors)
        sys.exit()
    repocheck = RepoCheck(cliargs.update_remotes, cliargs.rootdirs,
                          cliargs.follow_links, not cliargs.no_nested_repos,
                          cliargs.rel_paths)
    Viewer(repocheck.repos).display_results(cliargs.expanded, cliargs.all,
                                            cliargs.no_colors)


if __name__ == '__main__':
    main()
