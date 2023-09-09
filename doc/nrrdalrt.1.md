---
title: NRRDALRT
section: 1
header: User Manual
footer: nrrdalrt 0.0.2
date: January 3, 2022
---
# NAME
nrrdalrt - Task and event notification for **nrrdtask** and **nrrddate**.

# SYNOPSIS
**nrrdalrt** *command* [*OPTION*]...

# DESCRIPTION
**nrrdalrt** is a notification daemon that reads reminders from **nrrdtask** and **nrrddate** and generates desktop notifications and reminder emails for tasks and calendar events.

# OPTIONS
**-h**, **--help**
: Display help information.

**-c**, **--config** *file*
: Use a non-default configuration file.

# COMMANDS
**nrrdalrt** provides the following commands.

**config**
: Edit the **nrrdalrt** configuration file.

**start**
: Start the daemon.

**stop**
: Stop the daemon.

**version**
: Show application version information.

# FILES
**~/.config/nrrdalrt/config**
: Default configuration file

# AUTHORS
Written by Sean O'Connell <https://sdoconnell.net>.

# BUGS
Submit bug reports at: <https://github.com/sdoconnell/nrrdalrt/issues>

# SEE ALSO
Further documentation and sources at: <https://github.com/sdoconnell/nrrdalrt>
