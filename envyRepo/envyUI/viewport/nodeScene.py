from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QGraphicsScene
from PySide6.QtGui import QColor
from envyRepo.envyUI.viewport.nodeItem import NodeItem
import random
import numpy as np

#  possible idea is to always have the spacial partitions be sized to the whole screen and just move the nodes to where the window is

class Tile:
    def __init__(self, x: int, y: int, length: int):
        self.child_count = 0
        self.min_bound = (x, y)
        self.max_bound = (x + length, y + length)
        self.index = 0
        self._nodes = set()
        self.color = None

    def add_node(self, node: NodeItem):
        self._nodes.add(node)
        self.child_count += 1

    def remove_node(self, node: NodeItem):
        self._nodes.remove(node)
        self.child_count -= 1

    def get_nodes(self) -> set:
        return self._nodes

    def __repr__(self):
        return f'Tile: {self.index}'

class NodeScene(QGraphicsScene):
    def __init__(self):
        super().__init__()

        self.running = False
        self.nodes = {}
        self.setItemIndexMethod(QGraphicsScene.NoIndex)

        # ---------------------------------- space partitions ------------------------------------ #
        self.num_tiles_x = 0
        self.num_tiles_y = 0
        self.tiles = []
        self.tile_size = 10
        self.node_radius = 6

        # ---------------------------------- target positions ------------------------------------- #
        self.lab_target_positions = {}
        self.job_target_positions = {}

        # -------------------------------- running loop ---------------------------------- #
        np.seterr(divide='ignore')

        self.time_step = 0
        self.execution_timer = QTimer()
        self.execution_timer.timeout.connect(self.update_partitions)

    def start(self):
        self.running = True
        self.execution_timer.start(20)
        self.build_spatial_partitions()

    def build_spatial_partitions(self):
        self.tiles = []
        self.num_tiles_x = int(self.width() // self.tile_size)
        self.num_tiles_y = int(self.height() // self.tile_size)

        for i, y in enumerate(range(self.num_tiles_y)):
            for j, x in enumerate(range(self.num_tiles_x)):
                new_tile = Tile(x * self.tile_size, y * self.tile_size, self.tile_size)
                new_tile.index = (y * self.num_tiles_x) + x
                new_tile.color = QColor.fromHslF(random.random(), 1, .5, 1)
                self.tiles.append(new_tile)

        for i, node_name in enumerate(self.nodes):
            node = self.nodes[node_name]
            tile = self.get_partition_by_coordinates(node.P[0], node.P[1])

            if tile is None:
                node.setX(0)
                node.setY(0)
                tile = self.get_partition_by_coordinates(node.P[0], node.P[1])

                if tile is None:
                    del self.nodes[node_name]

            tile.add_node(node)
            node.tile_index = tile.index

        self.update()

    def addItem(self, item):
        super().addItem(item)
        parent_tile = self.tiles[0]
        parent_tile.add_node(item)
        self.update()

    def removeItem(self, item):
        super().removeItem(item)
        parent_tile = self.get_partition_by_coordinates(int(item.x()), int(item.y()))
        parent_tile.remove_node(item)
        self.update()

    def update_position(self, item: NodeItem) -> tuple:
        if self.time_step == 0:
            item.v *= item.damp
        new_P = (item.P + item.v)

        if new_P[0] > self.width():  # right side collision
            slope = item.v[1] / item.v[0]
            new_P = np.array([self.width(), (-(slope * item.P[0] - item.P[1]) + slope * self.width())]).astype(float)
            new_v = np.multiply(item.v, np.array([1, -1]).astype(float)) * -1
            item.v = new_v

        if new_P[0] < 0:  # left side collision
            new_P = np.array([0, -((item.v[1] / item.v[0]) * item.P[0] - item.P[1])]).astype(float)
            new_v = np.multiply(item.v, np.array([1, -1]).astype(float)) * -1
            item.v = new_v

        if new_P[1] > self.height():  # top collision
            slope = item.v[1] / item.v[0]
            new_P = np.array([(self.height() + (slope * item.P[0] - item.P[1])) / slope, self.height()]).astype(float)
            new_v = np.multiply(item.v, np.array([-1, 1]).astype(float)) * -1
            item.v = new_v

        if new_P[1] < 0:
            slope = item.v[1] / item.v[0]
            new_P = np.array([(slope * item.P[0] - item.P[1]) / slope, 0]).astype(float)
            new_v = np.multiply(item.v, np.array([-1, 1]).astype(float)) * -1
            item.v = new_v

        new_P = np.nan_to_num(new_P, nan=0.0)
        new_tile = self.get_partition_by_coordinates(int(new_P[0]), int(new_P[1]))
        if new_tile is not None:
            new_tile, _ = new_tile
            for node in new_tile._nodes:
                if node == item:
                    continue

                hit_dir = node.P - new_P
                dist_from_node = np.linalg.norm(hit_dir)
                if dist_from_node < 2 * self.node_radius:
                    hit_angle = np.acos(np.clip(np.dot(item.v / np.linalg.norm(item.v), hit_dir / np.linalg.norm(hit_dir)), -1, 1))
                    hit_P = (np.cos(hit_angle) * dist_from_node) * (item.v / np.linalg.norm(item.v))
                    hit_P[np.isinf(hit_P)] = 0
                    normal = node.P - hit_P
                    normal /= np.linalg.norm(normal)
                    reflection_vector = item.v - 2 * (np.dot(item.v, normal)) * normal

                    node.v = -reflection_vector
                    node.P += node.v
                    item.v = reflection_vector
                    new_P += item.v

        item.setX(new_P[0])
        item.setY(new_P[1])
        return item.x(), item.y()

    def update_partitions(self):
        self.time_step = (self.time_step + 1) % 33

        for index, tile in enumerate(self.tiles):

            if tile.child_count == 0:
                continue

            change_set = set()
            for node in tile._nodes:
                #  update size
                if node.size < node.target_size:
                    node.add_size()

                if node.size > node.target_size:
                    node.subtract_size()

                new_x, new_y = self.update_position(node)
                new_tile = self.get_partition_by_coordinates(new_x, new_y)

                if new_tile is None:
                    continue

                new_tile, new_index = new_tile

                if tile != new_tile:
                    change_set.add((index, new_index, node))

                #node.color = new_tile.color

            for item in change_set:
                old_tile = self.tiles[item[0]]
                new_tile = self.tiles[item[1]]
                node = item[2]
                node.tile_index = item[1]
                old_tile.remove_node(node)
                new_tile.add_node(node)
        self.update()

    def get_partition_by_coordinates(self, x: int, y: int) -> (Tile, None):
        if x > self.width() or y > self.height() or x < 0 or y < 0:
            return None

        selection_x = int(x // self.tile_size)
        selection_y = int(y // self.tile_size) * self.num_tiles_y

        target_index = selection_y + selection_x

        if target_index > len(self.tiles) - 1:
            return None

        return self.tiles[target_index], target_index

    def add_computer(self, computer: str, data: dict) -> None:
        status = data['Status']
        job = data['Job']
        allocation = data['Allocation']

        new_node = NodeItem(self.node_radius, computer)
        new_node.computer = computer
        new_node.status = status
        new_node.job = job
        new_node.allocation = allocation

        self.nodes[computer] = new_node
        self.addItem(new_node)

    def remove_computer(self, computer_name: str) -> None:
        node = self.nodes[computer_name]
        del self.nodes[computer_name]
        self.removeItem(node)

    def pause(self):
        if self.execution_timer.isActive():
            self.execution_timer.stop()

    def play(self):
        if self.execution_timer.isActive() is False:
            self.execution_timer.start(20)

    def clear_computers(self):
        for node in self.nodes:
            self.remove_computer(node)

    @staticmethod
    def fit_range(value, old_min, old_max, new_min, new_max):
        return ((value - old_min) / (old_max - old_min)) * (new_max - new_min) + new_min