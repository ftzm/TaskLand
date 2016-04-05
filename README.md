# tdp
Python prototype for a CLI, plain-text task list manager with advanced functionality

## Features

This application is in a state of major flux. A user guide will be published once all major functionality has been inplemented and the interface formlized.


## Usage

### View Functions

#### bc - view by context
Group tasks together by shared contexts. Tasks with multiple contexts will appea with every context group they belong to.

#### bp - view by project
Group tasks together by shared projects. Tasks with multiple projects will appea with every project group they belong to.

#### vc - filter by contexts
Only show those tasks that possess all the contexts given after 'vc' (up to 9).

#### vp - filter by projects
Only show those tasks that possess all the projects given after 'vp' (up to 9).

#### any - filter by any of the provided words
Only show tasks that contain at least one of the provided words (up to 9).

#### all - filter by all of the provided strings
Only show tasks that contain all of the provided strings (up to 9).

#### excl - filter out tasks with the provided strings
Only show tasks that do not contain any of the provided string (up to 9).

#### next
Show the task at the top of the list
