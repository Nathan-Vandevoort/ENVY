#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
envyRenderer.py: This process scans a directory for IFD's and then launches the appropriate command line renderer when found.
This process is also responsible for communication with that child process
"""

__author__ = "Nathan Vandevoort"
__copyright__ = "Copyright 2024, Nathan Vandevoort"
__version__ = "1.0.0"

import atexit
import os
import signal
import subprocess
import sys
import time

from config import Globals
from envyUtils.core import getComputerName, checkActiveComputers, resetRenderJob, makeDir, remQuotes

ENVYPATH = Globals.ENVYPATH
POLLINGRATE = Globals.POLLINGRATE
RENDERINPUT = Globals.RENDERINPUT
VRAYPATH = Globals.VRAYPATH
ARNOLDPATH = Globals.ARNOLDPATH
ARNOLDSHADERPATH = Globals.ARNOLDSHADERPATH
HUSKPATH = Globals.HUSKPATH
REDSHIFTPATH = Globals.REDSHIFTPATH
RENDERMANPATH = Globals.RENDERMANPATH


class EnvyRenderer:

    def __init__(self):
        _, fromPath, stdout, stderr = sys.argv
        self.creationflags = subprocess.CREATE_NO_WINDOW
        self.stdout = stdout
        self.stderr = stderr
        self.fromPath = fromPath
        self.renderProcess = None
        self.renderJob = None
        self.validExtensions = [
            '.VRSCENE',
            '.ASS',
            '.RIB',
            '.RS'
        ]
        signal.signal(signal.SIGTERM, self.sigterm_handler)
        atexit.register(self.exitFunction)
        while True:
            self.renderProcess = None
            self.renderJob = None
            counter = 0
            while self.renderJob is None or self.renderJob is None:
                self.renderJob = self.evaluateRenderJobs()
                counter += 1
                files = next(os.walk(self.fromPath))[2]
                if counter > len(files) * 2:  # exit condition
                    break
            root, extension = os.path.splitext(self.renderJob)
            self.inProgressName = f"{root}_EnvyInProgress_{getComputerName()}{extension}"
            self.completedName = f"{root}_EnvyCompleted_{extension}"
            try:
                self.write('RenderJob: ' + str(self.renderJob))
                self.renderProcess = self.pickRenderer(self.renderJob)
            except RenderInProgressError as fileNotFound:
                continue
            except Exception as err:
                self.write(str(err))
                break

            if self.renderProcess is None:
                self.write(
                    f"Pick Renderer returned nonetype: Maybe not all files in directory are envy renderable IFD's?")
                continue

            while self.renderProcess.poll() is None or self.renderProcess.poll() is None:
                time.sleep(2)

            self.write(str(self.renderProcess.poll()))

            try:
                os.rename(self.inProgressName, self.completedName)
            except Exception as err:
                try:
                    os.remove(self.completedName)
                    self.write(f"Removed {self.completedName} to resolve conflict")
                except Exception:
                    try:
                        os.remove(self.inProgressName)
                        self.write(f"Removed {self.inProgressName} to resolve conflict")
                    except Exception:
                        self.write(f"Error occured while renaming file to completed -> {str(err)}")
                        break
            self.write(f'Completed: {self.renderJob}')

    # os.remove(stdout)
    # os.remove(stderr)

    def pickRenderer(self, renderJob):
        suffix = renderJob.rstrip().split('.').pop()

        if suffix.upper() == 'VRSCENE':
            return self.renderVray(renderJob)

        if suffix.upper() == 'RS':
            return self.renderRedshift(renderJob)

        if suffix.upper() == 'ASS':
            return self.renderArnold(renderJob)

        if suffix.upper() == 'USD' or suffix.upper() == 'USDA' or suffix.upper() == 'USDC':
            return self.renderKarma(renderJob)

        if suffix.upper() == 'RIB':
            return self.renderRenderman(renderJob)

        return None

    def write(s, *args):
        print(str(s) + ' ' + str(*args), flush=True)

    def evaluateRenderJobs(self):
        activeComputers = []
        try:
            activeComputers = checkActiveComputers(removeComputers=False, status="Rendering")
        except Exception as err:
            self.write(f"EvaluateRenderJobs -> {str(err)}")

        if len(activeComputers) == 0:
            raise Exception(f"Error while evaluatingRenderJobs checkActiveComputers returned list with 0 length")

        activeComputers.append("ThisIsASentinalValueAndShouldBeImpossibleToFind")
        try:  # try to remove own computer
            activeComputers.pop(activeComputers.index(getComputerName().upper()))
        except Exception as err:
            self.write(f"Error occured while evaluatingRenderJobs -> {str(err)}")
            pass

        renderJobs = os.walk(self.fromPath)

        for (root, dirs, files) in renderJobs:
            for file in files:

                # skip if extension is invalid
                fileName, extension = os.path.splitext(file)
                if extension.upper() not in self.validExtensions:
                    continue

                if "_EnvyInProgress_" in file:
                    skip = False  # flag variable to checking this file if its not the file name
                    for computer in activeComputers:
                        if computer.upper() in file.upper():
                            skip = True
                    if skip:
                        continue
                    else:
                        try:
                            print(f"Resetting renderJob -> {file}")
                            resetRenderJob(root + file)
                        except Exception:
                            continue
                elif "_EnvyCompleted_" in file:
                    continue
                return makeDir(root) + file

    def renderVray(self, renderJob):  # renderJob should be whole file path
        root, extension = os.path.splitext(renderJob)  # name includes root
        try:
            os.rename(renderJob, self.inProgressName)
        except PermissionError:
            raise RenderInProgressError(f"Skipping {renderJob}")
        except FileNotFoundError:
            raise RenderInProgressError(f"Skipping {renderJob}")
        except FileExistsError:
            try:
                os.remove(self.inProgressName)
                raise RenderInProgressError(f"Removed {self.inProgressName}")
            except Exception:
                try:
                    os.remove(renderJob)
                    raise RenderInProgressError(f"Removed {renderJob}")
                except Exception:
                    return None
        except Exception as err:
            raise Exception(f"Error occured while attempting to render Vray -> {str(err)}")

        inputArg = f'-sceneFile="{self.inProgressName}"'

        renderProcess = None
        self.write("RenderString " + ' '.join([VRAYPATH, inputArg, "-autoClose=1", "-noFrameNumbers=1", "-display=0"]))
        try:
            with open(self.stdout, 'w') as stdout, open(self.stderr, 'w') as stderr:
                renderProcess = subprocess.Popen(' '.join([VRAYPATH, inputArg, "-autoClose=1", "-display=0"]),
                                                 stdout=stdout, stderr=stderr, creationflags=self.creationflags)
                atexit.register(renderProcess.terminate)
        except Exception as err:
            self.write(f"Error: {str(err)}")

        return renderProcess

    def renderKarma(self, renderJob):  # renderJob should be whole file path
        root, extension = os.path.splitext(renderJob)  # name includes root
        try:
            os.rename(renderJob, self.inProgressName)
        except PermissionError:
            raise RenderInProgressError(f"Skipping {renderJob}")
        except FileNotFoundError:
            raise RenderInProgressError(f"Skipping {renderJob}")
        except FileExistsError:
            try:
                os.remove(self.inProgressName)
                raise RenderInProgressError(f"Removed {self.inProgressName}")
            except Exception:
                try:
                    os.remove(renderJob)
                    raise RenderInProgressError(f"Removed {renderJob}")
                except Exception:
                    return None
        except Exception as err:
            raise Exception(f"Error occured while attempting to render Karma -> {str(err)}")

        inputArg = f'--usd-input "{self.inProgressName}"'

        renderProcess = None
        self.write("RenderString " + ' '.join([HUSKPATH, inputArg, "-R BRAY_HdKarma", "-V 3"]))
        try:
            with open(self.stdout, 'w') as stdout, open(self.stderr, 'w') as stderr:
                renderProcess = subprocess.Popen(' '.join([HUSKPATH, inputArg, "-R BRAY_HdKarma", "-V 3"]),
                                                 stdout=stdout, stderr=stderr, creationflags=self.creationflags)
                atexit.register(renderProcess.terminate)
        except Exception as err:
            self.write(f"Error: {str(err)}")

        return renderProcess

    def renderRedshift(self, renderJob):  # renderJob should be whole file path
        root, extension = os.path.splitext(renderJob)  # name includes root
        name = root.split('/').pop()

        try:
            os.rename(renderJob, self.inProgressName)
        except PermissionError as permissionError:
            raise RenderInProgressError(f"Skipping {renderJob}")
        except FileNotFoundError as fileNotFound:
            raise RenderInProgressError(f"Skipping {renderJob}")
        except FileExistsError:
            try:
                os.remove(self.inProgressName)
                raise RenderInProgressError(f"Removed {self.inProgressName}")
            except Exception:
                try:
                    os.remove(renderJob)
                    raise RenderInProgressError(f"Removed {renderJob}")
                except Exception:
                    return None
        except Exception as err:
            raise Exception(f"Error occured while attempting to render Redshift -> {str(err)}")

        inputArg = f'"{self.inProgressName}"'

        renderProcess = None
        self.write("RenderString " + ' '.join([REDSHIFTPATH, inputArg]))
        try:
            with open(self.stdout, 'w') as stdout, open(self.stderr, 'w') as stderr:
                renderProcess = subprocess.Popen(' '.join([REDSHIFTPATH, inputArg]), stdout=stdout, stderr=stderr,
                                                 creationflags=self.creationflags)
                atexit.register(renderProcess.terminate)
        except Exception as err:
            self.write(f"Error: {str(err)}")

        return renderProcess

    def renderRenderman(self, renderJob):
        root, extension = os.path.splitext(renderJob)  # name includes root
        name = root.split('/').pop()

        try:
            os.rename(renderJob, self.inProgressName)
        except PermissionError as permissionError:
            raise RenderInProgressError(f"Skipping {renderJob}")
        except FileNotFoundError as fileNotFound:
            raise RenderInProgressError(f"Skipping {renderJob}")
        except FileExistsError:
            try:
                os.remove(self.inProgressName)
                raise RenderInProgressError(f"Removed {self.inProgressName}")
            except Exception:
                try:
                    os.remove(renderJob)
                    raise RenderInProgressError(f"Removed {renderJob}")
                except Exception:
                    return None
        except Exception as err:
            raise Exception(f"Error occured while attempting to render Renderman -> {str(err)}")

        inputArg = f'{self.inProgressName}'

        renderProcess = None

        self.write("RenderString " + ' '.join([RENDERMANPATH, inputArg]))
        try:
            with open(self.stdout, 'w') as stdout, open(self.stderr, 'w') as stderr:
                renderProcess = subprocess.Popen(' '.join([RENDERMANPATH, inputArg, '-progress']), stdout=stdout,
                                                 stderr=stderr, creationflags=self.creationflags)
                atexit.register(renderProcess.terminate)
        except Exception as err:
            self.write(f"Error: {str(err)}")

        return renderProcess

    def renderArnold(self, renderJob):  # renderJob should be whole file path
        root, extension = os.path.splitext(renderJob)  # name includes root

        try:
            os.rename(renderJob, self.inProgressName)
        except PermissionError:
            raise RenderInProgressError(f"Skipping {renderJob}")
        except FileNotFoundError:
            raise RenderInProgressError(f"Skipping {renderJob}")
        except FileExistsError:
            try:
                os.remove(self.inProgressName)
                raise RenderInProgressError(f"Removed {self.inProgressName}")
            except Exception:
                try:
                    os.remove(renderJob)
                    raise RenderInProgressError(f"Removed {renderJob}")
                except Exception:
                    return None
        except Exception as err:
            raise Exception(f"Error occured while attempting to render Arnold -> {str(err)}")

        inputArg = f'{self.inProgressName}'

        renderProcess = None
        self.write("RenderString " + ' '.join(
            [ARNOLDPATH, inputArg, '-dw', '-l', ARNOLDSHADERPATH, '-dp', '-nocrashpopup', '-v', '2']))
        try:
            with open(self.stdout, 'w') as stdout, open(self.stderr, 'a') as stderr:
                renderProcess = subprocess.Popen(
                    [remQuotes(ARNOLDPATH), remQuotes(inputArg), '-dw', '-l', remQuotes(ARNOLDSHADERPATH),
                     '-dp', '-nocrashpopup', '-v', '2'], stdout=stdout, stderr=stderr, creationflags=self.creationflags)
                atexit.register(renderProcess.terminate)
        except Exception as err:
            self.write(f"Error while attempting to render with arnold: {str(err)}")

        return renderProcess

    def sigterm_handler(self, signum, frame):
        self.write(f"termination signal received, waiting for renderer process to complete before exiting handler")

        time.sleep(30)

        if isinstance(self.renderProcess, subprocess.Popen):
            for i in range(30):
                self.renderProcess.terminate()
                time.sleep(.5)
            self.renderProcess.kill()

        self.write(f"Render process no longer exists, terminating EnvyRenderer")

        sys.exit(0)

    def exitFunction(self):
        self.write(f"termination signal received, waiting for render process to complete before exiting")

        time.sleep(30)

        if isinstance(self.renderProcess, subprocess.Popen):
            for i in range(30):
                self.renderProcess.terminate()
                time.sleep(.5)
            self.renderProcess.kill()

        self.write(f"Render process no longer exists, terminating EnvyRenderer")

        sys.exit(0)


class RenderInProgressError(Exception):
    def __init__(self, message="Render already in progress"):
        self.message = message
        super().__init__(self.message)


renderer = EnvyRenderer()
