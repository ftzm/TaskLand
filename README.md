#TaskLand

Taskland is a Python-based, command-line application to manage tasks. It aims to capture the whole landscape of your productivity--in other words, your tasks for today, next week, and at the last stage of a months-long project. Advanced scheduling, flexible prioritization, and multiple view-modes make it easy to focus on current tasks while keeping future work organized.

<br>
<p align="center">
  <img src="https://github.com/ftzm/TaskLand/blob/master/taskland.gif?raw=true">
</p>
## Features

Taskland sports the following features, among others:

- projects
- contexts
- task scheduling
- flexible task repition
- subtasks
- colorized output
- view by any date range
- filter by task text, project, context
- Zsh autocompletion
- Compatible with Todo.txt

## Installation

- simply clone the folder into the directory of your choice.
- cd into the folder, and run "chmod +x taskland.py"

At this point you can run the application using the absolute path, but it is recommended to set up an alias. Something short like `t` make running the application very convenient.

#### Setting up an alias in Bash:

- Add the following line anywhere in your .bashrc:
```bash
alias t="/path/to/your/taskland.py"
```
- Reload your .bashrc by running the following command:
```bash
. ~/.bashrc
```
#### Setting up an alias in Zsh:

- Add the following line anywhere in your .zshrc
```bash
alias t=/path/to/your/taskland.py
```
- Reload your .zshrc by running the following command:
```bash
. ~/.zshrc
```
#### Setting up Autosuggestion in Zsh
TaskLand also includes an autocompletion script for Zsh. This will suggest commands as well as projects and contexts already used in the list. To install:

- Copy taskland_completion_zsh.sh to /home/youruser/.zsh/completions
- Rename the file to _taskland
- edit _taskland such that the path in the second line points to your taskland.py
- add the following lines to the bottom of your .zshrc:
```bash
fpath = (~/.zsh/completions $fpath) # only add this is not already present
compdef _taskland /path/to/your/taskland.py:taskland
```
- run the following line:
```bash
. ~/.zshrc; autoload -U compinit && compinit; rehash
```
## Usage

There are two types of commands: View commands, which print the task list in various ways, and action commands, which make changes to the task list.

#### View Commands

View commands are relatively straightforward. The majority essentially filter the task list, for example by limiting the tasks shown to those scheduled before a certain date or containing certain words. View commands can be combined, so you can do things like viewing only those tasks scheduled this week belonging to a particular project. There are also some view commands that change the way the tasks are printed. More info on those is provided later.

#### Action Commands

To run the application with one action command, the order is as follow: command target (argument). For example, "do 7" will mark the 7th task as done, while "setabove 7 5" will move the 7th task above the 5th task.

multiple commands can be combined if they apply to the same task. To do so, provide the target task number first (before any commands), and then leave the target number out of all following commands. For example, "7 c home p cleaning pr a" will assign the context "home", the project "cleaning" and the priority "A" to task number 7.

Additionally, commands can be run on a task as it is being added. First enter the "add" command followed by the task text. After the task text enter a space-separated comma, then  enter one or more action commands without specifying a target number (the added task functions as the target). For example: "add run tests , sub 10" will add a task with the text "run tests", and immediately set it as a sub-task for task number 10 (the effects of which are seen in [nest view](#nest)). In some cases this means there are two ways of achieving the same effect: "add empty trash , p home" and "add empty trash @home" are equivalent.

#### Shell Mode

It can be tedious to repeatedly make a change to the list and re-print it to see the effect. For that reason, TaskLand has a "shell mode". This is invoked by proving the argument `shell` followed by any valid combination of view commands. This will print the task list with the provided view commands and prompt for an action command. After entering an action command the list will be re-printed and the prompt reproduced. Exit by pressing `enter` without any input.

### List of View Functions
| Command | Description |
| :---: | :--- |
|`bc`|Group tasks together by shared contexts. Tasks with multiple contexts will appea with every context group they belong to.|
|`bp`|Group tasks together by shared projects. Tasks with multiple projects will appea with every project group they belong to.|
|`vc`|Only show those tasks that possess all the contexts given after 'vc'.|
|`vp`|Only show those tasks that possess all the projects given after 'vp'.|
|`any`|Only show tasks that contain at least one of the provided words.|
|`all`|Only show tasks that contain all of the provided strings.|
|`excl`|Only show tasks that do not contain any of the provided string.|
|`next`|Show the next task to be completed.|
|`today`|Show tasks due today or previously.|
|`week`|Show tasks due this week.|
|`until`|View tasks that are due up to and including the specified date. Use the date code specified [here](#date-codes)|
|`reverse`|Print the tasks in reverse order. Useful if your task list is so long it doesn't fit into the terminal screen.|
|`hide`|Hide components of the task line. Components are denoted with the codes listed [here](#task-line-component-codes)|
|`nocolor`|As the name suggests, prints tasks without colorization.|
|<h6 id="nest"> </h6>`nest`|prints the tasks in nested mode. If a task is set as a sub-task of another task, it will be positioned underneath that task with a small indentation. Usefuly for keeping track of large projects.|
|`h`|Print headers above each group of tasks due on the same date. Quickly see when tasks are due.|

### List of Action Commands
| Command | Description |
| :---: | --- |
|`add`|Add a task with the accompanying text. As an exception to the rule regarding multi-word arguments, task text does *not* need to be enclosed in quotation marks.|
|`edit`|Edit a task's text. The original text will be provided for your editing pleasure.|
|`rm`|Remove a task without completing it.|
|`do`|Complete a task, marking it with an 'x' in front and attaching the date of its completion.|
|`undo`|If a task has been marked as done and has yet to be archived, unmark it as done. Note: this command does not undo any previous command, it only removes the effects running 'do' on a task.|
|`sc`|Schedule a task. Use the date code format specified [here](#date-codes)|
|`usc`|Undo scheduling.|
|`pr`|Attach a priority to a task. The provided priority must be a single letter.|
|`upr`|Remove a priority from a task.|
|`c`|Add a context to a task.|
|`uc`|Remove the first or only context from a task.|
|`ucn`|If there are multiple contexts, specify which is to removed by providing a number (2 for the second, etc).|
|`p`|Add a project to a task.|
|`up`|Remove the first or only project from a task.|
|`upn`|If there are multiple projects, specify which is to removed by providing a number (2 for the second, etc).|
|`sub`|Make the target task a subtask of another task (specified by its task number). The effect of this can be seen in [nest view](#nest).|
|`usub`|undo making a task a subtask.|
|`con`|contract a task, so that its subtasks are hidden in [nest view](#nest).|
|`exp`|expand a contracted task so its subtasks are visible in nestview [nest view](#nest).|
|`rep`|Set a task to repeat. On completion, it will be recreated and scheduled for a date in the future specified by the format of its repeat tag. The format is as shown [here](#repeat-format)|
|`urep`|Remove a repition tag from a task.|
|`setabove`|Move a task above another task in the list. The other task is designated by its task number, and both tasks must either share a due date or not be scheduled.|
|`setbelow`|Move a task below another task in the list. The other task is designated by its task number, and both tasks must either share a due date or not be scheduled.|

#### Date Codes
dates can be provded in the following formats:

| Code | Meaning |
| :---: | :--- |
|`m`|Monday|
|`t`|Tuesday|
|`w`|Wednesday|
|`r`|Thursday|
|`f`|Friday|
|`s`|Saturday|
|`u`|Sunday|
|`n`|today ('n' for now)|
|`DD`|The next occurence of that day of the month, be it the current or following month.|
|`MM-DD`|Specify both the day and the month.|
|`YYYY-MM-DD`|Specify full date.|

#### Repeat Format
- __Repeat on certain weekdays:__ combine any number the following letter, representing the days from Monday to Sunday: m,t,w,r,f,s,u. On completion, the task will be rescheduled on the next weekday that has its representative letter in the tag.
- __Repeat a fixed number of days after completion:__ represented by combining the letter a and a number representing the day. For example, 'a3' will cause a task to be rescheduled 3 days after it was actually completed, regardless of when it was originally scheduled to be completed.
- __Repeat a fixed number of days after original scheduling:__ represented by the letter e and the number of days after which to repeat. For example, a task with the repeat tag 'e10' will be rescheduled 10 days after its original due date, even if completed late. If the task is completed so late that its new due date would still be in the past, the same number is added again under the due date is in the future.

#### Task Line Component Codes
| Code | Component |
| :---: | :--- |
|`n`|The task number|
|`x`|The 'x' of finished tasks|
|`pr`|The task priority|
|`dn`|The date a task was done|
|`d`|The date a task is (was) due|
|`t`|The task text|
|`p`|The task's projects|
|`c`|The task's contexts|
|`r`|The task's repitition tag|
|`a`|The tag showing when the task was added|
|`o`|The ordering tag (hidden by default)|
|`p_id`|The tag assigned to a task which is a parent in nested mode (hidden by default)|
|`c_id`|The tag assigned to a task which is a child in nested mode (hidden by default)|

## Settings

A config.rc will be automatically created on first run.

The format is as follows: fields are separated by their value by an equal sign--no spaces. Two fields, default_command and default_view, contain commands. These should be formatted that same as they are on the command line: separated by space, with multi-word arguments wrapped by quotation marks.

Below is the default configuration file with explanations of each field:

```bash
# Location of the todo-list file:
list_location=todo.txt
# What command to run when no commands are specified:
default_command=h
# Which fields to hide by default:
default_view=hide "o p_id c_id"
# How many days to wait before automatically archiving finished tasks
archive_delay=2
# Whether or not to archive automatically ('true' for true):
archive_automatically=false
# Location of archive file:
archive_location=archive.txt
```

## To-Do (oh, the irony)
- Package properly and include install script
- Bash Autocompletion

