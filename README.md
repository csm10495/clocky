# Clocky

Clocky is a pseudo-port of GNU Time, written in Python. The output generally looks like `time`.

Certain format codes may not work exactly like they do in GNU `time`.

# Installation

This will install the clocky cli:

```
pip install clocky
```

# Usage

Clocky can be run via `clocky` or `python -m clocky`

<!-- MARKDOWN-AUTO-DOCS:START (CODE:src=./help_output.txt) -->
<!-- The below code snippet is automatically added from ./help_output.txt -->
```txt
usage: clocky [-h] [-p] [-o OUTPUT] [-f FORMAT] [-a] [-v] [-q] [-V] [-g] ...

A pseudo-port of GNU time to Python. You can look at the man page of time to
get some info about the args here. Certain format codes are not supported and
will return a ? in place of an actual value.

positional arguments:
  cmd                   The command to time.

options:
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
  -g                    A clocky-specific extension. When set, tries to act
                        similar to gnu time in terms of output. Otherwise by
                        default (without -f) clocky acts like bash's time
                        command.
```
<!-- MARKDOWN-AUTO-DOCS:END -->

# Simple Example

Clocky can be used to time function execution (just like the time command):

```
> clocky echo "Hello World"
Hello World

real    0m0.007s
user    0m0.000s
sys     0m0.000s
```
