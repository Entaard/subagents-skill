def ready(task, passed):
    return any(item in passed for item in task["dependencies"])
