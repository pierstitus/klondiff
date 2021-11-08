# Klondike diff

This project is my go at creating an improved diff algorithm, inspired by the Patience diff algorithm of Bram Cohen.

The main focus is improving the readability of the diff output. The main changes are:

- Whitespace changes and repeated characters (e.g. '=========') have reduced influence.
- Short lines are neglected, reducing wrong line matches, with for example only brackets.
- Blocks with changes are interleaved, making it easer to see line differences.
- In colored diff output the unchanged parts of changed lines are displayed in gold.
- Changes in indentation have colored background.

**Warning: this software is not well tested yet, use at you own risk!**

## Example

![example](https://github.com/pierstitus/klondiff/blob/master/example.png)

Comparison of commit c07c0923 of this repository:

![comparison](https://github.com/pierstitus/klondiff/blob/master/comparison.png)

As you can see the resulting diff is not necessarily smaller, though it is more true to the real changes.

## Install (on Linux and the like)

Clone this repo somewhere on your computer, and make symlinks to klondiff and
git-klondiff in e.g. `~/bin` or `~/.local/bin` — some directory in your `$PATH`
(run `echo $PATH` to see where your shell looks up your commands). For example:

    ln -s ~/myclones/klondiff/klondiff ~/bin/klondiff
    ln -s ~/myclones/klondiff/git-klondiff ~/bin/git-klondiff

Klondiff requires python3 and patiencediff; to install the latter use e.g. pip
(`pip3 install patiencediff`) or apt-get the `python3-patiencediff` package on
debian/ubuntu/etc.

To run with python2 change python3 to python on the first line of klonpatiencediff.py.

## Usage

    klondiff file_a file_b

Use with pager:

    klondiff file_a file_b | less -R

Use with git:

For incidental use, make a symlink to `git-klondiff` as described above, then you can use

    git klondiff

To use klondiff by default set your configuration (assuming `~/bin/klondiff` is your symlink to `klondiff`)

    git config --global diff.external ~/bin/klondiff

To use klondiff for `git show`, `git format-patch` and other `git log` friends use `--ext-diff`

    git show --ext-diff

For `git format-patch` you'd want to disable color, which is not implemented yet.

## Why the name Klondike?

[Klondike](https://en.wikipedia.org/wiki/Klondike_(solitaire)) is a version of Patience, and brings the gold to the surface in diffs with many junk changes.

Piers Titus van der Torren
