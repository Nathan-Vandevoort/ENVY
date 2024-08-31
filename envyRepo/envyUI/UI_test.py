import envyRepo.prep_env
import envy.config_bridge as config
import sys
import os
#import qdarkstyle
from .mainWindow import MainWindow
from qasync import QApplication, QEventLoop
import faulthandler
faulthandler.enable()
os.environ['QT_DEBUG_PLUGINS'] = '1'

app = QApplication(sys.argv)
loop = QEventLoop(app)
#app.setStyleSheet(qdarkstyle.load_stylesheet_pyside6())
window = MainWindow(loop, app)
window.show()
loop.run_forever()
sys.exit(app.exec())