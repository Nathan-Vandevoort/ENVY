from anytree import NodeMixin
from envy.lib.jobs import enums


class JobItem(NodeMixin):
    def __init__(self, parent=None, children=None, **kwargs):
        super().__init__()
        self._label = ''
        self._progress = 0
        self._status = enums.Status.PENDING
        self._computer = 'N/A'
        self._info = ''
        self._data = [self._label, self._progress, self._status, self._computer, self._info]

        if children:
            self.children = children

        self.parent = parent
        self.configure_data(kwargs)

    @property
    def label(self):
        return self._label

    @label.setter
    def label(self, value):
        self._label = str(value)
        self._data[0] = str(value)

    @property
    def progress(self):
        return self._progress

    @progress.setter
    def progress(self, value):
        self._progress = value
        self._data[1] = f'{value}%'

    @property
    def status(self):
        return self._status

    @status.setter
    def status(self, value):
        self._status = value
        self._data[2] = value

    @property
    def computer(self):
        return self._computer

    @computer.setter
    def computer(self, value):
        self._computer = value
        self._data[3] = value

    @property
    def info(self):
        return self._info

    @info.setter
    def info(self, value):
        self._info = value
        word_split = value.split()
        counter = 0
        output_string = []
        for word in word_split:
            counter += len(word)
            if counter > 45:
                output_string.append('\n')
                counter = 0
            output_string.append(word)
        self._data[4] = ' '.join(output_string)

    def data(self, column: int) -> any:
        return self._data[column]

    def configure_data(self, kwargs):
        self.__dict__.update(kwargs)

        for key in kwargs:
            setattr(self, key, kwargs[key])

    def child(self, row):
        child_count = len(self.children)
        if row >= child_count:
            row = child_count - 1
        return self.children[row]

    def child_count(self):
        return len(self.children)

    def columnCount(self):
        return len(self._data)

    def set_data(self, column, value):
        self._data[column] = value

    def row(self):
        if self.parent is not None:
            return self.parent.children.index(self)
        return 0

    def __repr__(self):
        return str(self.label)
