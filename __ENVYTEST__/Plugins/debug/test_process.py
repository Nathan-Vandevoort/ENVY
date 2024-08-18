import time, sys


class Process:
    def __init__(self):
        counter = 0
        while counter <= 25:
            print(f'{counter * 2}%', flush=True)
            counter += 1
            time.sleep(.5)
        print('FINISHED', flush=True)
        sys.exit(0)


if __name__ == '__main__':
    Process()

