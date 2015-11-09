#!/usr/bin/python
import sys
import datetime
import calendar
import re
import readline

with open("todo.txt", "r") as f:
    file = f.readlines()

weekdays = ['u', 'm', 't', 'w', 'r', 'f', 's']
today = datetime.date.today().strftime("%Y %m %d %w")
today = [int(i) for i in list(filter(None, today.split(' ')))]
month_lengths = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
if today[0] % 4 == 0:
    month_lengths[1] = 29

def add(words):
    created = datetime.date.today().strftime("%Y-%m-%d")
    s = ' '.join(words)
    task = "%s %s\n" % (created, s)
    file.append(task)

def remove_task(task, linenum):
    followthrough = input('Task: {}\nDelete? (Y/n)'.format(task.strip()))
    if followthrough == '' or followthrough.lower() == 'y':
        removed = file.pop(linenum)
        print('Removed: ' + removed.strip())

def prefill_input(prompt, prefill):
    readline.set_startup_hook(lambda: readline.insert_text(prefill))
    try:
        result = input(prompt)
    finally:
        readline.set_startup_hook()
    return result

def edit(task):
    task = prefill_input('Edit task: ', task.strip())
    return task + '\n'

def do(task):
    completed = datetime.date.today().strftime("%Y-%m-%d")
    return "x %s %s" % (completed, task)

def undo(task):
    if task.startswith('x '):
        return task[13:]
    else:
        print('This task was never completed')
        return task

def schedule(task, date):

    future_num = re.search('3\d{7}\s', task)
    if future_num:
        task = unset_future(task)

    if re.search('\d{4}-\d{1,2}-\d{1,2}\s\d{4}-\d{1,2}-\d{1,2}', task):
        print("This task is already scheduled")
        return


    # catch various date formats, set them up for processing
    if re.match('\d{1,2}$', date):
        year, month, day = None, None, int(date)
    elif re.match('\d{1,2}-\d{1,2}$', date):
        year, month, day = None, tuple([int(i) for i in date.split('-')])
    elif re.match('\d{4}-\d{1,2}-\d{1,2}$', date):
        year, month, day = tuple([int(i) for i in date.split('-')])
    elif date in weekdays:
        year, month = None, None
        daynum = weekdays.index(date)
        if daynum > today[3]:
            offset = daynum - today[3]
        else:
            offset = 7 - (today[3] - daynum)
        day = today[2] + offset
        if day > month_lengths[today[1]-1]:
            day -= month+length[today[1]-1]
    else:
        print('invalid date format')
        return

    # increment month if day is lower than today
    if day < today[2] and month == None:
        month = today[1] + 1
        if month > 12:
            month = 1

    # set unset months and years now that we've dealt with monthless cases
    if not month: month = today[1]
    if not year: year = today[0]

    # if month lower than today's, due next year.
    if month < today[1]:
        year = today[0] + 1

    # handle edge cases where impossible dates are entered.
    if month > 12:
        print("Month must be 12 or below")
        return
    if day > month_lengths[month-1]:
        print("Not that many days in the month")
        return

    due = '{}-{:0=2d}-{:0=2d}'.format(year, month, day)

    if task.startswith('('): # insert behind priority if one is set
        return '%s%s %s' % (task[:4], due, task[4:])
    else:
        return '%s %s' % (due, task)

def unschedule(task):
    dates = re.search('\d{4}-\d{1,2}-\d{1,2}\s\d{4}-\d{1,2}-\d{1,2}', task)
    if dates:
        return task[:dates.start()] + task[dates.start()+11:]
    else:
        print("Task isn't scheduled")

def postpone():
    pass

def prioritize(task, priority='A'):
    if re.match('\([A-Z]\)\s', task):
        print("Task already prioritized")
        #change to deprioritize
        return
    return '({}) {}'.format(priority, task)

def unprioritize(task):
    if re.match('\([A-Z]\)\s', task):
        return task[4:]
    else:
        print('Task not prioritized')
        return task

def get_contexts():
    contexts = set([])
    for line in file:
        for c in re.findall('@\w+', line):
            contexts.add(c)
    return contexts

def set_context(task, context):
    if '@' + context in task:
        print("That context is already assigned")
        return task
    insert_before = re.search('S:|O:', task)
    if insert_before:
        return '{}@{} {}'.format(task[:insert_before.start()], \
                context, task[insert_before.start():])
    else:
        return task[:-1] + ' @' + context + task[-1:]

def set_context_guided(task):
    pass

def unset_context(task, num=1):
    contexts = [m for m in re.finditer('@\w+', task)]
    if num > len(contexts):
        print("Not that many contexts")
        return task
    start = contexts[num-1].start()
    end = contexts[num-1].end()
    return task[:start-1] + task[end:]

def get_projects():
    projects = set([])
    for line in file:
        for c in re.findall('\+\w+', line):
            projects.add(c)
    return projects

def set_project(task, project):
    if '+' + project in task:
        print("That project is already assigned")
        return task
    insert_before = re.search('@\w+|S:|O:', task)
    if insert_before:
        return '{}+{} {}'.format(task[:insert_before.start()], \
                project, task[insert_before.start():])
    else:
        return task[:-1] + ' +' + context + task[-1:]

def set_project_guided():
    pass

def unset_project(task, num=1):
    projects = [m for m in re.finditer('\+\w+', task)]
    if num > len(projects):
        print("Not that many projects")
        return task
    start = projects[num-1].start()
    end = projects[num-1].end()
    return task[:start-1] + task[end:]

def view_list():
    """print all lines in file"""
    for i, line in enumerate(file):
        print("%d %s" % (i, line.strip()))

def reorder():
    """Placeholder for complex reorder op"""
    file.sort()

def view(match, exclude=False):
    """
    Filter function. prints only lines including first argument and
    excluding second argument
    """
    if exclude:
        lines = [l for l in file if exclude not in l]
    else:
        lines = file
    for i, line in enumerate(lines):
        if match in line:
            print("%d %s" % (i, line.strip()))

def view_today():
    #change to print all before tomorrow. not containing @future
    """Print all tasks containing the current date"""
    lines = ['%d %s' % (i, l) for i, l in enumerate(file)]
    today_int = int('{}{:0=2d}{:0=2d}'.format(today[0], today[1], today[2]))
    for line in lines:
        if '@future' in line:
            continue
        due = re.search('\d{4}-\d{2}-\d{2}', line)
        if due:
            due_int = int(due.group().replace('-', ''))
            if due_int <= today_int:
                print(line.strip())


def project_view():
    """For every project, prints every task containing that tag"""
    facade = ['%d %s' % (i, l) for i, l in enumerate(file)]
    projects = sorted(list(get_projects()))
    for project in projects:
        print(project)
        for line in facade:
            if project in line:
                print(line.strip())

def view_children():
    facade = ['%d %s' % (i, l) for i, l in enumerate(file)]

    # make list of parent nums and line stings tuples
    parents = []
    for line in facade:
        parent = re.search('P:\d+', line)
        if parent:
            num = line[parent.start()+2:parent.end()]
            parents.append((num, line))

    # sort parents so that they are dealt with top to bottom,
    # with child-parents coming after their parents so they aren't moved
    # after their children in the next sorting step.

    # put top level parents at top
    insert_point = 0
    i = 0
    while i < len(parents):
        if 'C:' not in parents[i][1]:
            parents.insert(insert_point, parents.pop(i))
            insert_point += 1
        i += 1
    sorted = insert_point  # number of entries from top that are sorted
    # iterate over sorted tasks, looking for all unsorted children parents
    # put each child task under parent
    i = 0
    while i < sorted: #iterate over all sorted tasks
        child_tag = 'C:' + str(parents[i][0])
        insert_point = i + 1
        j = sorted  # number of sorted = index of first unsorted
        while j < len(parents): # iterate over unsorted tasks
            if child_tag in parents[j][1]:
                parents.insert(insert_point, parents.pop(j))
                insert_point += 1
            j += 1
        i += 1

    # rearrange children to follow their parents
    for id, line in parents:
        #pop children from facade
        children = []
        list_length = len(facade)
        i = 0
        while i < list_length:
            if 'C:'+id in facade[i]:
                children.append(facade.pop(i))
                list_length -= 1
            else:
                i += 1
        # find where to insert and insert all children
        insert_point = facade.index(line) + 1
        for child in children:
            facade.insert(insert_point, child)
            insert_point += 1

    #pretty indented print
    hierarchy = []
    closed_id = 0
    for line in facade:
        # closed/open indicator, set switch to hide following tasks
        parent_tag = re.search('P:\w+', line)
        if parent_tag:
            parent_tag = line[parent_tag.start():parent_tag.end()]
            if 'c' not in parent_tag:
                line = '\033[31m+\033[39m ' + line
            else:
                line = '\033[31m-\033[39m ' + line
                closed_id = parent_tag[2:-1]
        #align non plus or minused tasks
        else:
            line = '  ' + line
        #calc indent level based on degree of nested child tags
        child_code = re.search('C:\w+', line)
        if child_code:
            child_code = line[child_code.start()+2:child_code.end()]
            if child_code not in hierarchy:
                hierarchy.append(child_code)
            else:
                hierarchy = hierarchy[:hierarchy.index(child_code)+1]
            indents = hierarchy.index(child_code)+1
            line = "   " * indents + line
        else:
            hierarchy = []
        if closed_id not in hierarchy:
            print(line[:-1])

def unset_parent(task):
    """takes task string argument, return string without parent tag"""
    tag = re.search('P:\d+', task)
    start = tag.start()
    end = tag.end()
    return task[:start-1] + task[end:]

def set_parent(task):
    if 'P:' in task:
        print("Already set as parent")
    parent_ids = []
    for line in file:
        for c in re.findall('P:\d+', line):
            parent_ids.append(int(c[2:]))
    parent_id = 0
    i = 1
    while parent_id == 0:
        if i not in parent_ids:
            parent_id = i
        else:
            i += 1
    insert_before = re.search('O:', task)
    if insert_before:
        return '{}P:{} {}'.format(task[:insert_before.start()], \
                parent_id, task[insert_before.start():])
    else:
        return task[:-1] + ' P:' + str(parent_id) + task[-1:], parent_id

def evaluate_parent(id):
    """check for children matching the parent id,
    if none then remove parent tag.
    """
    children = 0
    for line in file:
        if 'C:' + str(id) in line:
            children += 1
            # because func is called from child tag removal method before line
            # written, there will be at least 1 child remaining in the file.
            # that's why the loop returns on >1 instead of >0
            if children > 1:
                return
    for i, line in enumerate(file):
        if "P:" + str(id) in line:
            task = unset_parent(line)
            linenum = i
            break
    file[linenum] = task


def unset_child(task):
    tag = re.search('C:\w+', task)
    start = tag.start()
    end = tag.end()
    id = task[start+2:end]
    evaluate_parent(id)
    return task[:start-1] + task[end:]

def set_child(task, parent_linenum):

    #get parent line from linenum
    parent = file[int(parent_linenum)]

    #get if parent is already parent get id, else set as parent
    parent_tag = re.search('P:\d+', parent)
    if parent_tag:
        parent_id = parent[parent_tag.start()+2:parent_tag.end()]
    else:
        file[int(parent_linenum)], parent_id = set_parent(parent)

    child_tag = 'C:' + str(parent_id)
    if child_tag in task:
        return task
    if 'C:' in task:
        task = unset_child(task)
    insert_before = re.search('P:|O:', task)
    if insert_before:
        return '{}{} {}'.format(task[:insert_before.start()], \
                child_tag, task[insert_before.start():])
    else:
        return task[:-1] + ' ' + child_tag + task[-1:]

def contract(task):
    parent_tag = re.search('P:\d+(?!c)', task)
    if parent_tag:
        return task[:parent_tag.end()]+'c'+task[parent_tag.end():]
    return task

def expand(task):
    parent_tag = re.search('P:\d+c', task)
    if parent_tag:
        return task[:parent_tag.end()-1]+task[parent_tag.end():]
    else:
        return task

def future_unset(task):
    future_num = re.search('3\d{7}\s', task)
    if future_num:
        start = future_num.start()
        end = future_num.end()
        return task[:start] + task[end:]
    else:
        return task

def future_find_last_num():
    for i in range(len(file)-1, -1, -1):
        last_future_num = re.search('3\d{7}\s', file[i])
        if last_future_num:
            return int(last_future_num.group()[1:])
    return None

def future_assign_num(task, num):
    if task.startswith('('): # insert behind priority if one is set
        return '%s3%s %s' % (task[:4], num, task[4:])
    else:
        return '3%s %s' % (num, task)

def future_set(task):
    future_num = re.search('3\d{7}\s', task)
    if future_num:
        task = future_unset(task)
    elif re.search('\d{4}-\d{1,2}-\d{1,2}\s\d{4}-\d{1,2}-\d{1,2}', task):
        task = unschedule(task)
    last_future_num = future_find_last_num()
    if last_future_num:
        future_num = last_future_num + 10000
        if last_future_num < 9999999:
            return future_assign_num(task, future_num)
    else:
        return future_assign_num(task, 1000000)



def future_order_after(task, linenum):
    pivot_task = file[linenum]
    pivot_order = re.search('3\d{7}\s', pivot_task)
    if pivot_order:
        pivot_order = int(pivot_order.group())
    else:
        print('pivot task not scheduled in fuzzy future')
        return task
    if not linenum + 1 < len(file):
        adjacent_task = file[linenum+1]
        adjacent_order = re.search('3\d{7}\s', pivot_task)
        if adjacent_order:
            adjacent_order = int(adjacent_order.group())
        else: adjacent_order = 39999999
    else:
        adjacent_order = 39999999

    half_diff = (adjacent_order - pivot_order) // 2
    order = pivot_order + half_diff

    return future_assign_num(task, order)

def set_before():
    pass

def main(argv):
    # argument-less functionality
    if not argv:
        view_today()
    # commands without target tasks
    elif argv[0] == "ls":
        view_list()
    elif argv[0] == "pv":
        project_view()
    elif argv[0] == "vc":
        view_children()
    elif argv[0] == "v":
        try:
            view(argv[1])
        except:
            print("You need a filter string")
    elif argv[0] == "a":
        try:
            add(argv[1:])
        except:
            print("you need to write a task")
    elif argv[0] == "sort":
        sort()
    elif argv[0] == "today":
        view_today()
    # commands that target tasks
    elif argv[0].isdigit():
        linenum = int(argv[0])
        task = file[linenum]
        if len(argv) == 1:
            print(task.strip())
            return
        if argv[1] == "do":
            file[linenum] = do(task)
        elif argv[1] == "undo":
            file[linenum] = undo(task)
        elif argv[1] == "e":
            file[linenum] = edit(task)
        elif argv[1] == "r":
            remove_task(task, linenum)
        elif argv[1] == "s":
            try:
                file[linenum] = schedule(task, argv[2])
            except:
                print("You need to supply a date")
        elif argv[1] == "us":
            file[linenum] = unschedule(task)
        elif argv[1] == 'p':
            try:
                file[linenum] = prioritize(task, argv[2])
            except:
                file[linenum] = prioritize(task)
        elif argv[1] == 'up':
            file[linenum] = unprioritize(task)
        elif argv[1] == "c":
   #         try:
                file[linenum] = set_context(task, argv[2])
    #        except:
    #            file[linenum] = set_context_guided(task)
        elif argv[1] == "uc":
            try:
                file[linenum] = unset_context(task, int(argv[2]))
            except:
                file[linenum] = unset_context(task)
        elif argv[1] == "pr":
   #         try:
                file[linenum] = set_project(task, argv[2])
    #        except:
    #            file[linenum] = set_context_guided(task)
        elif argv[1] == "upr":
            try:
                file[linenum] = unset_project(task, int(argv[2]))
            except:
                file[linenum] = unset_project(task)
        elif argv[1] == "sc":
            file[linenum] = set_child(task, int(argv[2]))
        elif argv[1] == "usc":
            file[linenum] = unset_child(task)
        elif argv[1] == "cn":
            file[linenum] = contract(task)
        elif argv[1] == "ex":
            file[linenum] = expand(task)
        elif argv[1] == "unfut":
            file[linenum] = future_unset(task)
        elif argv[1] == "sf":
            file[linenum] = future_set(task)
        elif argv[1] == "sa":
            file[linenum] = set_after(task, int(argv[2]))
    else:
        return

    # write changes to file
    if file:
        reorder()
        with open("todo.txt", "w") as f:
            for line in file:
                f.write(line)

if __name__ == "__main__":  # why do I use this
    main(sys.argv[1:])
