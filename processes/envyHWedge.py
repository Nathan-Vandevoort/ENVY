#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
envyHWedge.py: The process responsible for launching a prepared houdini envionrment and then communicating with it
"""

__author__ = "Nathan Vandevoort"
__copyright__ = "Copyright 2024, Nathan Vandevoort"
__version__ = "1.0.0"


import json
import os
import sys
import signal
import atexit
import envyProcessHandler as eph
import time
from config import Globals
from envyUtils.core import getComputerName, checkActiveComputers, makeDir, resetRenderJob

JOBPATH = Globals.JOBPATH


class EnvyHWedge:

    def __init__(self):
        self.jobPath = JOBPATH
        self.processHandler = eph.ProcessHandler(parentProcess="EHW")
        self.hythonStdout = ""
        self.hythonProcess = ""
        signal.signal(signal.SIGTERM, self.sigterm_handler)
        atexit.register(self.exitFunction)

        # Running Loop
        while True:
            self.hWedgeJob = None
            self.numHythonLines = 0

            # Evaluate HWedgeJobs
            counter = 0
            while self.hWedgeJob is None or self.hWedgeJob == None:
                self.hWedgeJob = self.evaluateWedgeJobs()

                # stop running loop and exit if all jobs have been ran
                counter += 1
                files = next(os.walk(self.jobPath))[2]
                if counter > len(files) * 2:  # exit condition
                    break

            # Build in progress and completed name
            root, extension = os.path.splitext(self.hWedgeJob)
            self.inProgressName = f"{root}_EnvyInProgress_{getComputerName()}{extension}"
            self.completedName = f"{root}_EnvyCompleted_{extension}"

            # Try to rename job file
            try:
                os.rename(self.hWedgeJob, self.inProgressName)
            except FileNotFoundError:
                self.write(f"Skipping {self.inProgressName}")
                continue
            except PermissionError:
                self.write(f"Skipping {self.inProgressName}")
                continue
            except FileExistsError:
                try:
                    os.remove(self.inProgressName)
                    self.write(f"Removing -> {self.inProgressName}")
                    continue
                except Exception:
                    try:
                        os.remove(self.inProgressName)
                        self.write(f"Removing -> {self.inProgressName}")
                        continue
                    except Exception:
                        continue
            except Exception as err:
                self.write(f"Critical Error Occured -> {str(err)}")
                break

            # Read the Job file
            with open(self.inProgressName, 'r') as job:
                jobInstructions = job.read()
                job.close()

            self.write(f"CacheJob: {self.inProgressName}")

            # delete in progress file
            os.remove(self.inProgressName)

            jobInstructions = json.loads(jobInstructions)
            del jobInstructions['Message_Purpose']

            # parse Job instructions
            for key in jobInstructions:
                # Get Target Button Node and set parm name
                targetButtonNode = jobInstructions[key][0]
                targetButtonNodeSplit = targetButtonNode.split('/')
                self.targetButtonParmName = targetButtonNodeSplit.pop()
                self.targetButtonNode = '/'.join(targetButtonNodeSplit)
                self.jobInstructions = jobInstructions[key][1]

            # Try and launch hython wait and try again if process already exists
            counter = 0
            while counter <= 50:
                if counter == 50:
                    raise Exception(f"Timed Out while attempting to launch Hython")
                try:
                    self.processName = self.launchHython()
                    break
                except Exception:
                    time.sleep(2)
                counter += 1

            # set project and load hip
            self.writeToHython(f"hou.putenv('JOB', '{self.jobInstructions['JOB']}')")
            self.writeToHython(f"hou.hipFile.load('{self.jobInstructions['HIP']}')")
            del self.jobInstructions['HIP']
            del self.jobInstructions['JOB']

            # iterate over parameter changes and update parameters
            for parm in self.jobInstructions:
                # Isolate node
                parmSplit = parm.split('/')
                parmName = parmSplit.pop()
                parmNode = '/'.join(parmSplit)
                self.writeToHython(f"parmNode = hou.node('{parmNode}')")

                # Isolate Parm and set value
                value = self.jobInstructions[parm]

                # add quotes to value
                value = f"'{str(value)}'"

                # set the value of the parm
                self.writeToHython(f"targetParm = parmNode.parm('{parmName}')")
                self.writeToHython(f"targetParm.setExpression({value}, language=hou.exprLanguage.Hscript)")
                self.writeToHython(f"targetParm.pressButton()")

            self.writeToHython(f"targetNode = hou.node('{self.targetButtonNode}')")
            self.writeToHython(f"targetParm = targetNode.parm('{self.targetButtonParmName}')")
            self.writeToHython(f"targetParm.pressButton()")

            # Close Hython process
            ignore = False
            try:
                self.processHandler.endProcess(self.processName)
            except eph.InvalidProcessException as ipe:
                self.write(f"Hython process doesnt seem to exist -> {ipe}")
                ignore = True
            except Exception as err:
                if ignore == False:
                    self.write(f"Error occurred while closing Hython Process -> {err}")
                    exit()

    def writeToHython(self, s, wait=True):
        # Write to Hython and wait to move on until hython has put out a newline
        self.processHandler.write(self.processName, s)
        self.write(s)

        if wait == True:
            # Wait for new line
            while self.countLines() == self.numHythonLines:
                time.sleep(.25)
            time.sleep(.5)
            self.numHythonLines = self.countLines()

    def evaluateWedgeJobs(self):
        # get Active Computers
        activeComputers = []
        try:
            activeComputers = checkActiveComputers(removeComputers=False, status="Caching")
        except Exception as err:
            self.write(f'Failed while getActiveComputers -> {str(err)}')

        # make sure that there is at least one active computer
        if len(activeComputers) != 0:
            # Try to remove own computer from list of active computers
            activeComputers.append("ThisIsASentinalValueAndShouldBeImpossibleToFind")
            try:
                activeComputers.pop(activeComputers.index(getComputerName().upper()))
            except Exception as err:
                self.write(f"Error occurred while evaluateWedgeJobs -> {str(err)}")

        # evaluate hWedgeJobs and make sure that they are .EHW files
        hWedgeJobs = os.walk(makeDir(self.jobPath))
        print(hWedgeJobs)
        for (root, dirs, files) in hWedgeJobs:
            for file in files:
                renamedFile = None
                fileName, extension = os.path.splitext(file)

                # skip files that arent .EHW
                if extension.upper() != '.NV':
                    continue

                # skip files which are marked envy completed
                if "_EnvyCompleted_" in fileName:
                    continue

                # skip files if their purpose isnt EnvyHWedge
                fileInstructions = {}
                try:
                    with open(root + file, 'r') as nvFile:
                        fileInstructions = json.load(nvFile)
                        nvFile.close()
                except Exception:
                    continue
                if fileInstructions['Message_Purpose'] != 'EnvyHWedge':
                    continue

                # skip files which are marked in progress
                # also skip or pickup file marked with this computers name depending on decided behavior
                if "_EnvyInProgress_" in fileName:
                    # make sure the job isnt a currently working computer
                    skip = False  # flag value to skip if the job is
                    for computer in activeComputers:
                        if computer.upper() in file.upper():
                            skip = True
                    if skip == True:
                        continue
                    else:
                        # reset the job
                        try:
                            self.write(f"Resetting HWedgeJob -> {file}")
                            resetRenderJob(root + file)
                        except Exception:
                            try:
                                os.remove(root + file)
                            except Exception:
                                pass
                # return job
                return root + file
        return None

    def launchHython(self):
        hythonPath = Globals().HYTHONPATH
        processName = 'HYTHON'
        try:
            self.processHandler.startProcess(hythonPath, processName, 'Program')
            self.write(f"Launched Hython")
        except Exception as err:
            self.write(f"Error Occured while launching Hython {str(err)}")
        time.sleep(.5)
        self.hythonStdout = f"{self.processHandler.getLogDir()}EHW_{processName}_stdout.txt"

        # only moveon once hython has fully initialized
        initialized = False
        while initialized == False:
            if self.countLines() == self.numHythonLines:
                time.sleep(.25)
                continue
            else:
                self.numHythonLines += 1
                return f"EHW_{processName}"

    def countLines(self):
        # Read stdout file
        with open(self.hythonStdout, 'r') as stdout:
            fileContents = stdout.read()
            stdout.close()

        # get the number of new lines and then return those new lines as a list
        numLines = fileContents.count('>>>')
        return numLines

    def write(s, *args):
        print(str(s) + ' ' + str(*args), flush=True)

    def sigterm_handler(self, signum, frame):
        self.write(f"termination signal received, waiting for HWedge process to complete before exiting handler")

        time.sleep(5)
        self.processHandler.endProcesses()
        self.write(f"Hython process no longer exists, terminating EnvyHWedge")

        sys.exit(0)

    def exitFunction(self):
        self.write(f"termination signal received, waiting for Hython process to complete before exiting")

        time.sleep(5)
        self.processHandler.endProcesses()

        self.write(f"Hython process no longer exists, terminating EnvyHWedge")

        sys.exit(0)


EnvyHWedge()