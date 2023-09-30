# autorename

## Synopsis

Do you keep a directory tree full of files that you clipped from the Internet
that you want to keep, but they all have nonsensical and unhelpful names that
makes the whole thing turn into a big pile? If so, this script is for you!

This script renames the files in a directory to a new name based on the
file's modification time and md5 hash for specific recognized extensions.

Perfect for turning an unwieldy tree of bizarrely-named files into one with
files that at least sort in the order they were created.

Features:

* Renames files to a name based on the file's modification time and md5 hash.
  For example:
      Copy of IMAGE-1 (2).JPG -> 2020-01-01-98ecf8427e.jpg

  The first 10 characters of the md5 hash are used to avoid collisions:

        d41d8cd98f00b204e9800998ecf8427e
        ^^^^^^^^^^......................
  
  (The front of the hash is used just like git, as opposed to the back of the
  hash like GPG.)

* Recognizes specific file extensions and renames them accordingly. Skips the
  rest.

* Can be run in a dry-run mode to see what it would do without actually doing
  it.

* Skips files that start with prefixes that look like dates and words, such as
  `2020-01-01 My Picture.jpg` or `2020-01-XX My Picture.jpg` so that if you did
  name any files to get them "close enough", they won't get renamed.

* Deletes all those pesky `.DS_Store` files that macOS likes to create.

## Usage

You can call the script with arguments including directory names and file
names:

    autorename.py [--commit] <files | directories...>

For example:

First, run in dryrun mode (default) to see what it would do:

    python ./autorename.py ~/Clippings
  
Then, run with `--commit` to actually rename the files:

    python ./autorename.py --commit ~/Clippings
