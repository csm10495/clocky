# Timey

Timey is a pseudo-port of GNU Time, written in Python

# Installation

This will install the timey cli:

```
pip install timey
```

# Usage

Timey can be run via `timey` or `python -m timey`

<!-- MARKDOWN-AUTO-DOCS:START (CODE:src=./help_output.txt) -->
<!-- The below code snippet is automatically added from ./help_output.txt -->
```txt
usage: timey [-h] [-p] [-o OUTPUT] [-f FORMAT] [-a] [-v] [-q] [-V] [-g] ...

A pseudo-port of GNU time to Python. You can look at the man page of time to
get some info about the args here.

positional arguments:
  cmd                   The command to time.

optional arguments:
  -h, --help            show this help message and exit
  -p                    Use the portable output format.
  -o OUTPUT, --output OUTPUT
                        Do not send the results to stderr, but overwrite the
                        specified file.
  -f FORMAT, --format FORMAT
                        Specify output format, possibly overriding the format
                        specified in the environment variable TIME.
  -a, --append          (Used together with -o.) Do not overwrite but append.
  -v, --verbose         Give very verbose output about all the program knows
                        about.
  -q, --quiet           Don't report abnormal program termination (where
                        command is terminated by a signal) or nonzero exit
                        status.
  -V, --version         Print version information on standard output, then
                        exit successfully.
  -g                    A timey-specific extension. When set, tries to act
                        similar to gnu time in terms of output. Otherwise by
                        default (without -f) timey acts like bash's time
                        command.
```
<!-- MARKDOWN-AUTO-DOCS:END -->
