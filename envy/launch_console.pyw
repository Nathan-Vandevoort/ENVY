import utils.config_bridge as config
import envyRepo.prep_env
import os
import sys
REPOPATH = config.Config.REPOPATH
sys.path.append(os.path.join(REPOPATH, os.path.pardir))
import qdarkstyle
from envyRepo.envyUI.mainWindow import MainWindow
from qasync import QApplication, QEventLoop
from PySide6.QtWidgets import QSplashScreen
from PySide6.QtGui import QPixmap

#import faulthandler
#faulthandler.enable()
#os.environ['QT_DEBUG_PLUGINS'] = '1'

app = QApplication(sys.argv)

loop = QEventLoop(app)
app.setStyleSheet(qdarkstyle.load_stylesheet_pyside6())
window = MainWindow(loop, app)
window.show()
loop.run_forever()
sys.exit(app.exec())
