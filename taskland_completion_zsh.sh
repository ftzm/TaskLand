#compdef tdp
executable="/path/to/your/taskland.py"

view_cmds=(
    'bc:View tasks organized by context'
    'bp:View tasks organized by project'
    'vc:View tasks with the given context(s)'
    'vp:View tasks with the given projects(s)'
    'any:View tasks whose descriptions contain any of the given strings'
    'all:View tasks whose descriptions contain all of the given strings'
    'excl:View tasks whose descriptions contain none of the given strings'
    'next:View the next task to be done'
    'today:view tasks due up to and including today'
    'week:View tasks due up to and including a week from today'
    'until:View tasks due up to and including a given date'
    'reverse:View tasks in reverse order'
    "hide:Don't show components of tasks signified by the following codes"
    'nocolor:Pretty-print tasks with color-coded components'
    'nest:Pretty-print tasks with sub-task ordering'
    'h:Print a header above each group of dates'
    )

action_cmds=(
    'a:Add a task'
    'edit:Edit a task description'
    'do:Mark a task as completed'
    "rm:Remove a task (not marked done, repeat task not created)"
    's:Schedule task (DD, MM-DD, YYYY-MM-DD, m/t/w/r/f/s/u)'
    'us:Unschedule a task'
    'pr:Prioritize a task'
    'upr:Unprioritize a task'
    'c:Assign a task context(s)'
    'uc:Remove the first context from the targeted task'
    'ucn:Remove the nth context from the targeted task'
    'p:Assign a task project(s)'
    'up:Remove the first project from the targeted task'
    'upn:Remove the nth project from the targeted task'
    'sub:Assign task as a subtask to another task'
    'usub:Unassign task as a subtask to another task'
    'con:Contract a parent task such that its children are hidden in nest view'
    'exp:Expand a parent task such that its children are no longer hidden in nest view'
    'setabove:Sort a task before another task'
    'setbelow:Sort a task after another task'
    'rep:Make a task repeat on the specified schedule'
    'urep:Stop a task from repeating'
    )

_view_cmds() {
    local commands; commands=( $view_cmds )
    _describe -t commands 'tdp command' commands "$@"
}

_action_cmds() {
    local commands; commands=( $action_cmds )
    _describe -t commands 'tdp command' commands "$@"
}

_all_cmds() { local commands; commands=( ${view_cmds[@]} ${action_cmds[@]} )
    _describe -t commands 'tdp command' commands "$@"
}

_hide_flags() {
    local commands; commands=(
    'n:Line number'
    'x:X on finished task'
    'pr:Priority'
    'dn:Date of completion'
    'd:Due date'
    'a:Date of creation'
    'o:Order code'
    'p:Projects'
    'c:Contexts'
    'p_id:Parent ID'
    'c_id:Child ID'
    'r:Repeat code'
    't:Task text'
)
    _describe -t commands 'tdp command' commands "$@"
}

_get_projects() {
    local completions
    completions="$(${executable} pp)"
    completions=( "${(ps:\n:)completions}" )
    _describe -t completions 'projects' completions "$@"
}

_get_contexts() {
    local completions
    completions="$(${executable} pc)"
    completions=( "${(ps:\n:)completions}" )
    _describe -t completions 'projects' completions "$@"
}

assess_mode() {
    commands=(bc bp vc vp any all excl next today week until reverse trim nocolor nest h)
    for c in "${commands[@]}"; do
        if [ "$c" = "$1" ]; then
            _arguments '*: :_view_cmds'
            return
        fi
    done
    _arguments '*: :_action_cmds'
}

case "$words[-2]" in
    *[0-9]*)
        isdigit=true
        ;;
    *)
        isdigit=false
        ;;
esac
if [ ${#words[@]} -gt 2 ] && [ "$isdigit" = true ]; then
    keyword="$words[-3]"
else
    keyword="$words[-2]"
fi
case "$keyword" in
    taskland)
        _arguments '*: :_all_cmds'
        ret=0
        ;;
    p|vp)
        _arguments '*: :_get_projects'
        ret=0
        ;;
    c|vc)
        _arguments '*: :_get_contexts'
        ret=0
        ;;
    trim)
        _arguments '*: :_trim_flags'
        ret=0
        ;;
    *)
        assess_mode "$words[2]"
        ret=0
        ;;
esac


