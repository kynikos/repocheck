# repocheck

This script gives status information for code repositories found recursively
under a root directory. In particular, it tells whether there are uncommitted
changes, untracked files, unpushed or unpulled commits.

Thanks to the `-u` option, it is also useful to fetch updates for all the
remotes in the encountered repositories.

See `repocheck -h` for usage instructions and the available options.

The `RepoCheck` class can also be imported from another Python script: after
instantiating it, the repository information can be accessed through the
`RepoCheck.repos` dictionary.

Only Git repositories are currently supported, but adding support for other
version control systems such as Mercurial or Subversion should not be hard, and
I will be glad to merge a pull request that implements that :)

The code has been written from scratch, but the idea was inspired by
[unpushed](https://github.com/nailgun/unpushed) and
[gitcheck](https://github.com/badele/gitcheck).

## Installation

repocheck is currently only packaged for Arch Linux in the AUR as
[repocheck-git](https://aur.archlinux.org/packages/repocheck-git/).

On other operating systems it must be installed with Python's manual tools.
Pull requests that add support for other operating systems are welcome!

## License

repocheck is distributed under the terms of the
[GNU General Public License v3.0](http://www.gnu.org/copyleft/gpl.html)
(see LICENSE).
