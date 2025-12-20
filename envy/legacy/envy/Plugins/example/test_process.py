import time, sys, json

"""
This file is intended to emulate a render process. It will print a percentage for each frame and then print FINISHED frame# when its done with a frame
You would most likely not be able to edit the called process directly
"""

class Process:
    def __init__(self, tasks: dict):
        self.tasks = tasks
        for task in tasks:
            counter = 0
            while counter <= 25:
                print(f'{counter * 4}%', flush=True)
                counter += 1
                time.sleep(.1)
            print(f'FINISHED {self.tasks[task]}', flush=True)
        sys.exit(0)


if __name__ == '__main__':
    a, tasks = sys.argv
    tasks = json.loads(tasks)
    Process(tasks)

