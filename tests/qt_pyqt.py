import sys
from PyQt5 import QtWidgets

app = QtWidgets.QApplication(sys.argv)
button = QtWidgets.QPushButton("Hello")
button.setFixedSize(400, 400)
button.show()
app.exec_()
