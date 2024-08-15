import time


class Debug_Plugin:
    def __init__(self, job):
        time.sleep(10)
        print('FINISHED')


if __name__ == '__main__':
    Debug_Plugin()
