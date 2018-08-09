# Klondike diff

This project is my go at creating an improved diff algorithm, inspired by the Patience diff algorithm of Bram Cohen.

The main focus is improving the readability of the diff output. The main changes are:

- Whitespace changes and repeated characters (e.g. '=========') have reduced influence.
- Short lines are neglected, reducing wrong line matches, with for example only brackets.
- Blocks with changes are interleaved, making it easer to see line differences.
- In colored diff output the unchanged parts of changed lines are displayed in gold.

## Usage

    klondiff file_a file_b

Use with pager:

    klondiff file_a file_b | less -R

Use with git:

For incidental use make a symlink to `git-klondiff` somewhere in your path, e.g. ~/bin/, then you can use

    git klondiff

To use klondiff by default set your configuration (assuming ~/bin/klondiff is a symlink to patiencediff.py)

    git config --global diff.external ~/bin/klondiff

## Why Klondike?

[Klondike](https://en.wikipedia.org/wiki/Klondike_(solitaire)) is a version of Patience, and brings the gold to the surface in diffs with many junk changes.

Piers Titus van der Torren