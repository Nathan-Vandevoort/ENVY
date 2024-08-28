import sys
import prep_env
import config_bridge as config
from mainWindow import MainWindow
from qasync import QApplication, QEventLoop

app = QApplication(sys.argv)
loop = QEventLoop(app)
window = MainWindow(event_loop=loop)
window.show()
loop.run_forever()
sys.exit(app.exec())