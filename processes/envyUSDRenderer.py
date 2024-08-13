#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
envyUSDRenderer.py: The render process for usd render jobs via houdini's husk utility
"""

__author__ = "Nathan Vandevoort"
__copyright__ = "Copyright 2024, Nathan Vandevoort"
__version__ = "1.0.0"


import os
import sys
import atexit
import time
import envyProcessHandler as eph
import json
from config import Globals
from envyUtils.core import makeDir, checkActiveComputers, getComputerName, addQuotes, resetRenderJob
from envyUtils.logUtils import createDirectories


ENVYPATH = Globals.ENVYPATH
RENDERINPUT = Globals.RENDERINPUT
HUSKPATH = Globals.HUSKPATH
HCMDPATH = HUSKPATH.split('/')
HCMDPATH.pop()
HBINPATH = makeDir('/').join(HCMDPATH)
HCMDPATH = makeDir('/'.join(HCMDPATH)) + 'hcmd.exe'
JOBPATH = Globals.JOBPATH


class EnvyUSDRenderer:
    def __init__(self):
        self.usdJobsPath = JOBPATH
        self.processHandler = eph.ProcessHandler(parentProcess='EUSD')
        atexit.register(self.exitFunction)
        self.processName = 'HCMD'
        while True:
            self.currentRenderJob = None
            self.numHcmdLines = 0
            self.hcmdStdout = ''

            # evaluate render jobs
            attemptCount = 0
            while self.currentRenderJob == None or self.currentRenderJob is None:
                self.currentRenderJob = self.evaluateRenderJobs()
                if attemptCount > 60:  # exit condition
                    self.write("Exit condition reached")
                    sys.exit(0)
                    break
                attemptCount += 1
                time.sleep(.1)

            self.write(f"Current Render Job: {self.currentRenderJob}")
            root, extension = os.path.splitext(self.currentRenderJob)
            self.inProgressName = f"{root}_EnvyInProgress_{getComputerName()}{extension}"
            self.completedName = f"{root}_EnvyCompleted_{extension}"

            # attempt to rename in progress file
            try:
                self.write('RenderJob: ' + str(self.currentRenderJob))
                os.rename(self.currentRenderJob, self.inProgressName)
            except FileNotFoundError as fileNotFoundErr:
                self.write(f"Skipping {self.currentRenderJob} {str(fileNotFoundErr)}")
                continue
            except PermissionError:
                self.write(f"Skipping {self.currentRenderJob}")
                continue
            except FileExistsError:
                try:
                    os.remove(self.inProgressName)
                    continue
                except Exception:
                    try:
                        os.remove(self.currentRenderJob)
                        continue
                    except Exception:
                        continue
            except Exception as err:
                self.write("Critical Error Occured")
                self.write(str(err))
                break

            # open hcmd
            with open(self.inProgressName, 'r') as job:
                arguments = json.load(job)
                job.close()
            args = []
            del arguments['Purpose']
            for argument in arguments:
                args.append(argument)
                args.append(str(arguments[argument]))

            # launch hcmd
            counter = 0
            while counter <= 50:
                if counter == 50:
                    raise Exception(f"Timed Out while attempting to launch hcmd")
                try:
                    self.processName = self.launchHcmd()
                    break
                except Exception:
                    time.sleep(2)
                counter += 1

            # send hcmd render command
            self.writeToHcmd('husk ' + ' '.join(args))
            self.write('attempting to end EUSD_HCMD')
            self.processHandler.endProcess('EUSD_HCMD')

            try:
                os.remove(self.inProgressName)
            except Exception as err:
                self.write(f"Error occured while attempting to finish render job -> {str(err)}")
                break
            self.write(f'Completed: {self.currentRenderJob}')

    def evaluateRenderJobs(self):
        activeComputers = []
        try:
            activeComputers = checkActiveComputers(removeComputers=False, status="Rendering")
        except Exception as err:
            self.write(f"EvaluateRenderJobs -> {str(err)}")
            return None

        if len(activeComputers) != 0:
            activeComputers.append("ThisIsASentinalValueAndShouldBeImpossibleToFind")
            try:  # try to remove own computer
                activeComputers.pop(activeComputers.index(getComputerName().upper()))
            except Exception as err:
                self.write(f"Error occured while evaluatingRenderJobs -> {str(err)}")
                return None

        renderJobs = os.walk(self.usdJobsPath)
        for (root, dirs, files) in renderJobs:
            for file in files:
                self.write(file)
                renamedFile = None
                fileName, extension = os.path.splitext(file)

                # skip if extension is not .NV
                if extension.upper() != '.NV':
                    self.write('skip')
                    continue

                # skip if purpose is not envyusdrender
                values = {}
                with open(root + file, 'r') as nvFile:
                    values = json.load(nvFile)
                    nvFile.close()
                if 'Purpose' not in values:
                    continue
                if values['Purpose'] != 'EnvyUSDRenderer':
                    continue

                # skip if envy completed in file
                if "_EnvyCompleted_" in file:
                    continue

                # skip if envy in progress is in file
                if "_EnvyInProgress_" in file:
                    skip = False  # flag variable to checking this file if its not the file name
                    for computer in activeComputers:
                        if computer.upper() in file.upper():
                            skip = True
                    if skip == True:
                        continue
                    else:
                        try:
                            self.write(f"Resetting renderJob -> {file}")
                            resetRenderJob(root + file)
                        except Exception:
                            try:
                                os.remove(root + file)
                            except Exception:
                                pass

                self.write(f"returning {root + file}")
                return root + file

    def write(self, s, *args):
        print(str(s) + ' ' + str(*args), flush=True)

    def launchHcmd(self):
        hcmdPath = HCMDPATH
        processName = 'hcmd'
        self.processHandler.startProcess(hcmdPath, processName, 'Program')
        self.write(f"Launched hcmd")
        time.sleep(.5)
        self.hcmdStdout = f"{self.processHandler.getLogDir()}EUSD_HCMD_stdout.txt"

        # only moveon once hython has fully initialized
        initialized = False
        while initialized == False:
            if self.countLines() == self.numHcmdLines:
                time.sleep(.25)
                continue
            else:
                self.numHcmdLines += 1
                return f"EUSD_{processName}"

    def writeToHcmd(self, s, wait=True):
        # Write to Hython and wait to move on until hython has put out a newline
        self.processHandler.write(self.processName, s)
        self.write(s)

        if wait == True:
            # Wait for new line
            while self.countLines() == self.numHcmdLines:
                time.sleep(.25)
            time.sleep(.5)
            self.numHcmdLines = self.countLines()

    def countLines(self):
        cwd = os.getcwd()
        # Read stdout file
        with open(self.hcmdStdout, 'r') as stdout:
            fileContents = stdout.read()
            stdout.close()

        # get the number of new lines
        numLines = fileContents.count(f'{cwd}>')

        """
        THIS IS A BAD FIX for arnold not giving the shell back

        """
        if ('|  Arnold shutdown' in fileContents):
            numLines += 1

        return numLines

    def exitFunction(self):
        self.write(f"termination signal received, waiting for hcmd process to complete before exiting")

        time.sleep(5)
        self.processHandler.endProcesses()

        self.write(f"hcmd process no longer exists, terminating EnvyUSDRenderer")

        sys.exit(0)


def createUSDRenderJobs(fromPath=RENDERINPUT, enableTiled=False, tileCount=3, renderDelegate='BRAY_HdKarma', verbosity=3, args=None):

    if args is None:
        args = {}

    filesTuple = os.walk(makeDir(fromPath))
    usdFiles = []
    for root, dirs, files in filesTuple:
        for file in files:
            name, extension = os.path.splitext(file)
            validExtensions = [".USD", ".USDA", ".USDC", ".USDZ"]
            if extension.upper() in validExtensions:
                usdFiles.append(root + file)
    if not os.path.isdir(fromPath):  # create renderjob directory
        createDirectories(filePath=fromPath)

    counter = 0
    for usdFile in usdFiles:

        # set tileCount to 1 if there is no tiling
        if enableTiled == False:
            tileCount = 1

        if '_EnvyCompleted_' in usdFile or '_EnvyInProgress_' in usdFile:
            continue

        # evaluate args
        argsDict = {'Purpose': 'EnvyUSDRenderer'}

        for count in range(tileCount ** 2):
            name, _ = os.path.splitext(usdFile)
            name = name.split('/').pop()
            jobName = f"{makeDir(JOBPATH)}{name}_EnvyTile{count}.NV"
            nameSplit = name.split('.')
            frameNumber = nameSplit.pop()
            name = '.'.join(nameSplit)

            with open(jobName, 'w') as job:  # make job file
                job.close()
            with open(jobName, 'a') as job:  # write argsDict to job file
                root, extension = os.path.splitext(usdFile)
                argsDict['--usd-input'] = addQuotes(root + '_EnvyCompleted_' + extension)
                argsDict['-R'] = renderDelegate
                argsDict['-V'] = verbosity
                argsDict['--frame'] = int(frameNumber)
                if enableTiled == True:
                    argsDict['--tile-count'] = f"{tileCount} {tileCount}"
                    argsDict['--tile-index'] = {count}
                    argsDict['--tile-suffix'] = f"{name}.{str(count).zfill(4)}.{frameNumber}.exr\n"
                argsDict.update(args)
                json.dump(argsDict, job)
        root, extension = os.path.splitext(usdFile)
        os.rename(usdFile, root + '_EnvyCompleted_' + extension)
        counter += 1

    return counter


if __name__ == "__main__":
    EnvyUSDRenderer()