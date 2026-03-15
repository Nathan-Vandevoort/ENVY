from collections.abc import MutableSet
from typing import TypeVar, Generic, Any, Iterator

T = TypeVar("T")


class KeyedSet(MutableSet, Generic[T]):
    """
    KeyedSet acts as a set but also allows for operations based on a key attribute.

    For example:
        my_set = KeyedSet('name', MyDataClass)
        my_set.add(my_dataclass_instance_01)
        my_set.add(my_dataclass_instance_02)
        my_set.discard(my_dataclass_instance_01)
        my_set.discard('dataclass02')
    """

    def __init__(self, key_attr: str, cls: type[T]) -> None:
        self._key_attr = key_attr
        self._spec: type[T] = cls

        self._data: dict[Any, T] = {}

    def add(self, value: T) -> None:
        if not isinstance(value, self._spec):
            raise ValueError(f"value is not of type {self._spec!r}")

        key = self._get_key(value)
        self._data[key] = value

    def discard(self, value: T) -> None:
        # If the object itself is passed in use it's _key_attr as the key. Otherwise assume the key was passed in.
        key = self._get_key(value) if isinstance(value, type(self._spec)) else value
        if key in self._data:
            del self._data[key]

    def get(self, value: Any) -> T | None:
        key = self._get_key(value) if isinstance(value, type(self._spec)) else value
        return self._data.get(key)

    def _get_key(self, item: T) -> Any:

        key = getattr(item, self._key_attr, None)
        if not key:
            raise AttributeError(f"Object {item!r} does not have attribute {self._key_attr!r}")
        return key

    def __contains__(self, x: object) -> bool:
        if isinstance(x, self._spec):
            return self._get_key(x) in self._data
        return x in self._data

    def __len__(self) -> int:
        return len(self._data)

    def __iter__(self) -> Iterator[T]:
        return iter(self._data.values())
