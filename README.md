# Klondike diff

This project is my go at creating an improved diff algorithm, inspired by the Patience diff algorithm of Bram Cohen.

The main focus is improving the readability of the diff output. The main changes are:

- Whitespace changes and repeated characters (e.g. '=========') have reduced influence.
- Blocks with changes are interleaved, making it easer to see line differences.
- In colored diff output the unchanged parts of changed lines are displayed in gold.

## Usage

    klondiff file_a file_b

Use with pager:

    klondiff file_a file_b | less -R

Use with git: (assuming you have a symlink named klondiff to patiencediff.py in ~/bin/)

    GIT_EXTERNAL_DIFF=~/bin/klondiff git diff

## Why Klondike?

Klondike is a version of Patience, and brings the gold to the surface in diffs with many junk changes.
