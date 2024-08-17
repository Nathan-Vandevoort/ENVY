import time, sys


class Process:
    def __init__(self):
        counter = 0
        while counter <= 50:
            print(f'{counter * 2}%')
            counter += 1
            time.sleep(.5)
        print('FINISHED')
        sys.exit(0)


if __name__ == '__main__':
    Process()

