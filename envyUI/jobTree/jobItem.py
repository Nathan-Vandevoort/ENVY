from envyJobs import enums

class JobItem:
    def __init__(self, parent=None):
        """
        Initializer for the job items
        self._data
            index 0 = Name
            index 1 = Progress
            index 2 = Status
            index 3 = ID
        :param data:
        :param parent:
        """
        self._data = ['', 0, enums.Status.PENDING, -1]
        self._parent = parent
        self._children = []

    def appendChild(self, child):
        self._children.append(child)

    def child(self, row):
        child_count = self.child_count()
        if row >= child_count:
            row = child_count - 1
        return self._children[row]

    def child_count(self):
        return len(self._children)

    def set_name(self, name: str):
        self._data[0] = name

    def get_name(self) -> str:
        return self._data[0]

    def set_progress(self, progress: int):
        self._data[1] = progress

    def get_progress(self) -> int:
        return self._data[1]

    def set_status(self, status: enums.Status):
        self._data[2] = status

    def get_status(self) -> enums.Status:
        return self._data[2]

    def set_ID(self, ID: int):
        self._data[3] = ID

    def get_ID(self) -> int:
        return self._data[3]

    def columnCount(self):
        return len(self._data)

    def data(self, column: int):
        return self._data[column]

    def set_data(self, column, value):
        self._data[column] = value

    def parent(self):
        return self._parent

    def row(self):
        if self._parent:
            return self._parent._children.index(self)
        return 0

    def __str__(self):
        return self._data[0]