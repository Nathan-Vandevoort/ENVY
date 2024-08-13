#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
nodeSolver.py: A vectorized particle solver intended to be used for envys nodegraph view contains NodeSolver object as well as all data objects
"""

__author__ = "Nathan Vandevoort"
__copyright__ = "Copyright 2024, Nathan Vandevoort"
__version__ = "1.0.0"

import numpy as np


# np.set_printoptions(precision=3, suppress=True, formatter={'float': ' {: 0.3f}'.format}, linewidth=200)

class NodeSolver():

    def __init__(self, bounds=None):

        if bounds is None:
            bounds = [800, 600]

        self.bounds = np.array(bounds)
        self.POSITIONS = np.array([[0, 0]]).astype(float)
        self.VELOCITIES = np.array([[0, 0]]).astype(float)
        self.NODES = []
        self.NODENAMES = {}
        self.DISTANCES = np.array([[0]]).astype(float)
        self.ATTRACT = np.array([[0]]).astype(float)
        self.REPEL = np.array([[0]]).astype(float)
        self.NODEDIRECTIONS = np.array([[0, 0]]).astype(float)
        self.DRAG = .95
        self.BOUNCEDAMP = .8
        self.nodeSize = 6
        self.INERTIASCALE = .1
        self.gravity = np.array([0, 1]) * .1
        self.mousePos = np.array([0, 0])
        self.mouseForceFactor = 0
        self.highestSpeed = 0

    def addNode(self, name: str, P = None, V = None):

        if V is None:
            V = [0, 0]

        if P is None:
            P = [0, 0]

        P = np.array(P)
        V = np.array(V)

        if name in self.NODENAMES:
            raise NameError('Node name already exists')

        newNode = Node(name)

        if len(self.NODES) == 0:  # first node so overwrite the existing indices
            self.POSITIONS[0] = P
            self.VELOCITIES[0] = V
            self.NODES = [newNode]
            self.NODENAMES[name] = 0
            self.DISTANCES[0, 0] = 0
            self.NODEDIRECTIONS[0, 0] = 0
            self.ATTRACT[0, 0] = 0
            self.REPEL[0, 0] = 0
            return newNode

        # add to all the lists
        self.POSITIONS = np.append(self.POSITIONS, [P], axis=0)
        self.VELOCITIES = np.append(self.VELOCITIES, [V], axis=0)
        self.NODES.append(newNode)
        self.NODENAMES[name] = len(self.NODES) - 1

        # Append to DISTANCES, ATTRACT, and REPEL matrices
        newRow = np.zeros((1, self.DISTANCES.shape[1]))  # Match the number of columns with DISTANCES
        newColumn = np.zeros(
            (self.DISTANCES.shape[0] + 1, 1))  # Match the number of rows with DISTANCES after adding newRow

        self.ATTRACT = np.pad(self.ATTRACT, pad_width=1, mode='constant', constant_values=1)

        self.REPEL = np.pad(self.REPEL, pad_width=1, mode='constant', constant_values=1)

        return newNode

    def calculateDistanceMatrix(self):

        # Calculate the squared differences along each dimension
        diff_squared = np.sum(np.absolute(self.POSITIONS[:, np.newaxis, :] - self.POSITIONS[np.newaxis, :, :]), axis=-1)

        # Take the square root to get the Euclidean distances
        self.DISTANCES = np.sqrt(diff_squared)

    def calculateNodeDirectionMatrix(self):
        self.NODEDIRECTIONS = np.subtract(self.POSITIONS[:, None], self.POSITIONS)
        self.NODEDIRECTIONS = self.NODEDIRECTIONS / np.linalg.norm(self.NODEDIRECTIONS, axis=-1, keepdims=True)

    def update(self):

        # calculate new matrices
        self.calculateDistanceMatrix()
        self.calculateNodeDirectionMatrix()

        # attract / repel
        if len(self.NODES) >= 2:
            attractionMask = self.DISTANCES.clip(min=0, max=self.nodeSize * 10)
            attractionMask = attractionMask / (self.nodeSize * 10)

            repelMask = self.DISTANCES.clip(min=0, max=self.nodeSize)
            repelMask = repelMask / self.nodeSize

            #self.VELOCITIES += self.calculateAttractionVectors(mask=attractionMask)
            self.VELOCITIES += self.calculateRepelVectors(mask=(1 - repelMask)) * 2

        # mouse repel
        if self.mouseForceFactor > 0:
            self.mouseForceFactor -= .1
            self.mouseForceFactor = max(0, self.mouseForceFactor)
            mouseDirection, mouseRepelMask = self.calculatePointDirections(self.mousePos)
            mouseRepelMask = mouseRepelMask.clip(min=0, max=self.nodeSize * 10)
            mouseRepelMask = mouseRepelMask / (self.nodeSize * 10)
            mouseRepelMask = np.expand_dims(mouseRepelMask, 1)
            self.VELOCITIES += (-mouseDirection * (1 - mouseRepelMask))

        # updated highestSpeed
        self.highestSpeed = np.max(np.sqrt(np.sum(self.VELOCITIES ** 2, axis=1)))

        self.borderBounce()
        self.POSITIONS += self.VELOCITIES

        self.VELOCITIES *= self.DRAG

    def calculatePointDirections(self, point):
        directions = point - self.POSITIONS
        return (np.nan_to_num(directions / np.linalg.norm(directions, axis=-1, keepdims=True), nan=0),
                np.nan_to_num(np.sqrt(np.sum(directions ** 2, axis=1)), nan=0))

    def calculateAttractionVectors(self, mask=None):
        nodeDirections = self.NODEDIRECTIONS

        if isinstance(mask, type(None)):
            mask = np.ones(self.DISTANCES.shape, dtype=float)

        nodeDirections = np.multiply(nodeDirections, np.expand_dims(mask, 2))

        return np.nanmean(nodeDirections, axis=0)

    def calculateRepelVectors(self, mask=[]):
        nodeDirections = self.NODEDIRECTIONS

        if isinstance(mask, type(None)):
            mask = np.ones(self.DISTANCES.shape, dtype=float)

        nodeDirections = np.multiply(nodeDirections, np.expand_dims(mask, 2))

        return np.nanmean(nodeDirections, axis=1)

    def buildEmptyMask(self):
        return np.zeros(self.DISTANCES.shape, dtype=float)

    def printAttribs(self):

        print(f'Positions:\n {self.POSITIONS}\n')
        print(f'Velocities:\n {self.VELOCITIES}\n')
        print(f'Nodes:\n {self.NODES}\n')
        print(f'NodeNames:\n {self.NODENAMES}\n')
        print(f'Distances:\n {self.DISTANCES}\n')
        print(f'Attract:\n {self.ATTRACT}\n')
        print(f'Repel:\n {self.REPEL}\n')

    def updateBounds(self, bound):

        self.bound = bound

    def borderBounce(self):

        integratedPositions = self.POSITIONS + self.VELOCITIES

        tooLow = np.argwhere(integratedPositions[:, 1] > self.bounds[1] - self.nodeSize)
        tooHigh = np.argwhere(integratedPositions[:, 1] < self.nodeSize)
        tooRight = np.argwhere(integratedPositions[:, 0] > self.bounds[0] - self.nodeSize)
        tooLeft = np.argwhere(integratedPositions[:, 0] < self.nodeSize)

        for i in tooLow:
            p = self.POSITIONS[i][0]
            v = self.VELOCITIES[i][0]
            normal = np.array([0, -1])
            reflectionVector = v - 2 * np.dot(v, normal) * normal * self.BOUNCEDAMP
            self.VELOCITIES[i] = np.array(reflectionVector) + np.array([0, -.1])

        for i in tooHigh:
            p = self.POSITIONS[i][0]
            v = self.VELOCITIES[i][0]
            normal = np.array([0, 1])
            reflectionVector = v - 2 * np.dot(v, normal) * normal * self.BOUNCEDAMP
            self.VELOCITIES[i] = np.array(reflectionVector) + np.array([0, .1])

        for i in tooRight:
            p = self.POSITIONS[i][0]
            v = self.VELOCITIES[i][0]
            normal = np.array([-1, 0])
            reflectionVector = v - 2 * np.dot(v, normal) * normal * self.BOUNCEDAMP
            self.VELOCITIES[i] = np.array(reflectionVector) + np.array([-.1, 0])

        for i in tooLeft:
            p = self.POSITIONS[i][0]
            v = self.VELOCITIES[i][0]
            normal = np.array([1, 0])
            reflectionVector = v - 2 * np.dot(v, normal) * normal * self.BOUNCEDAMP
            self.VELOCITIES[i] = np.array(reflectionVector) + np.array([.1, 0])

    def borderPush(self):

        tooLow = np.argwhere(self.POSITIONS[:, 1] > self.bounds[1] - self.nodeSize)
        tooHigh = np.argwhere(self.POSITIONS[:, 1] < self.nodeSize)
        tooRight = np.argwhere(self.POSITIONS[:, 0] > self.bounds[0] - self.nodeSize)
        tooLeft = np.argwhere(self.POSITIONS[:, 0] < self.nodeSize)

        tooFarLists = [tooLow, tooHigh, tooRight, tooLeft]
        reflectionVectors = [np.array([0, -1]), np.array([0, 1]), np.array([-1, 0]), np.array([1, 0])]

        centerPos = np.array([self.bounds[0] / 2, self.bounds[1] / 2])

        for i, tooList in enumerate(tooFarLists):
            reflectionVector = reflectionVectors[i]
            for j in tooList:
                j = j[0]
                p = self.POSITIONS[j]
                v = self.VELOCITIES[j]

                toCenter = np.subtract(centerPos, p)
                distanceFromCenter = np.linalg.norm(v)

                adjustedReflectionVector = (toCenter / distanceFromCenter) + reflectionVector

                self.VELOCITIES[j] = (adjustedReflectionVector / np.linalg.norm(
                    adjustedReflectionVector)) * np.linalg.norm(v)

    def getSimulationData(self):

        data = SimulationData()
        data.setPositions(self.POSITIONS.tolist())
        data.setNodes(self.NODES)
        data.setNodeNames(self.NODENAMES)
        data.setHighestSpeed(self.highestSpeed)

        return data

    def addForce(self, force):
        self.VELOCITIES += np.array(force) * self.INERTIASCALE

    def updateMouse(self, pos):
        self.mousePos = np.array(pos)
        self.mouseForceFactor = self.mouseForceFactor + .1
        self.mouseForceFactor = min(self.mouseForceFactor, .5)


class Node:
    def __init__(self, name: str, P=None, V=None):
        if V is None:
            V = [0, 0]

        if P is None:
            P = [0, 0]

        self.name = name
        self.initialP = P
        self.initialV = V
        self.attracted = []
        self.repelled = []


class SimulationData:

    def __init__(self):
        self.positions = []
        self.nodes = []
        self.nodeNames = {}
        self.highestSpeed = 0

    def setPositions(self, positions):
        self.positions = positions

    def setNodes(self, nodes):
        self.nodes = nodes

    def setNodeNames(self, nodeNames):
        self.nodeNames = nodeNames

    def setHighestSpeed(self, speed):
        self.highestSpeed = speed
