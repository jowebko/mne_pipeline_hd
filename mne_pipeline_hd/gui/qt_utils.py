# -*- coding: utf-8 -*-
"""
Pipeline-GUI for Analysis of MEG data
based on: https://doi.org/10.3389/fnins.2018.00006
@author: Martin Schulz
@email: mne.pipeline@gmail.com
@github: marsipu/mne_pipeline_hd
"""
import smtplib
import ssl
import sys
import traceback
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from PyQt5.QtCore import QRunnable, Qt, pyqtSlot
from PyQt5.QtWidgets import QDesktopWidget, QDialog, QGridLayout, QLabel, QLineEdit, QMessageBox, QPushButton


class Worker(QRunnable):
    """
    Worker thread

    Inherits from QRunnable to handler worker thread setup, signals and wrap-up.

    :param callback: The function callback to run on this worker thread. Supplied args and
                     kwargs will be passed through to the runner.
    :type callback: function
    :param args: Arguments to pass to the callback function
    :param kwargs: Keywords to pass to the callback function

    """

    def __init__(self, fn, signal_class, *args, **kwargs):
        super().__init__()

        # Store constructor arguments (re-used for processing)
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signal_class = signal_class

    @pyqtSlot()
    def run(self):
        """
        Initialise the runner function with passed args, kwargs.
        """

        # Retrieve args/kwargs here; and fire processing using them
        try:
            result = self.fn(*self.args, **self.kwargs)
        except:
            # Todo: Logging in Worker-Class
            # logging.error('Ups, something happened:')
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]
            self.signal_class.error.emit((exctype, value, traceback.format_exc(limit=-10)))
        finally:
            self.signal_class.finished.emit()  # Done


class ErrorDialog(QDialog):
    def __init__(self, parent, err):
        if parent:
            super().__init__(parent)
        else:
            super().__init__()
        self.err = err
        self.setWindowTitle('An Error ocurred!')

        self.init_ui()
        if parent:
            self.open()
        else:
            self.show()
        self.center()
        self.raise_win()

    def init_ui(self):
        layout = QGridLayout()

        self.label = QLabel()
        self.formated_tb_text = self.err[2].replace('\n', '<br>')
        self.html_text = f'<b><big>{self.err[1]}</b></big><br>{self.formated_tb_text}'
        self.label.setText(self.html_text)
        layout.addWidget(self.label, 0, 0, 1, 2)

        self.name_le = QLineEdit()
        self.name_le.setPlaceholderText('Enter your Name (optional)')
        layout.addWidget(self.name_le, 1, 0)

        self.email_le = QLineEdit()
        self.email_le.setPlaceholderText('Enter your E-Mail-Adress (optional)')
        layout.addWidget(self.email_le, 1, 1)

        self.send_bt = QPushButton('Send Error-Report')
        self.send_bt.clicked.connect(self.send_report)
        layout.addWidget(self.send_bt, 2, 0)

        self.close_bt = QPushButton('Close')
        self.close_bt.clicked.connect(self.close)
        layout.addWidget(self.close_bt, 2, 1)

        self.setLayout(layout)

    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def raise_win(self):
        if sys.platform == 'win32':
            # on windows we can raise the window by minimizing and restoring
            self.showMinimized()
            self.setWindowState(Qt.WindowActive)
            self.showNormal()
        else:
            # on osx we can raise the window. on unity the icon in the tray will just flash.
            self.activateWindow()
            self.raise_()

    def send_report(self):
        msg_box = QMessageBox.question(self, 'Send an E-Mail-Bug-Report?',
                                       'Do you really want to send an E-Mail-Report?',
                                       QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if msg_box == QMessageBox.Yes:
            port = 465
            adress = 'mne.pipeline@gmail.com'
            password = '24DecodetheBrain7!'

            context = ssl.create_default_context()

            message = MIMEMultipart("alternative")
            message['Subject'] = str(self.err[1])
            message['From'] = adress
            message["To"] = adress

            message_body = MIMEText(f'<b><big>{self.name_le.text()}</b></big><br>'
                                    f'<i>{self.email_le.text()}</i><br><br>'
                                    f'<b>{sys.platform}</b><br>{self.formated_tb_text}', 'html')
            message.attach(message_body)
            try:
                with smtplib.SMTP_SSL('smtp.gmail.com', port, context=context) as server:
                    server.login('mne.pipeline@gmail.com', password)
                    server.sendmail(adress, adress, message.as_string())
                QMessageBox.information(self, 'E-Mail sent', 'An E-Mail was sent to mne.pipeine@gmail.com\n'
                                                             'Thank you for the Report!')
            except OSError:
                QMessageBox.information(self, 'E-Mail not sent', 'Sending an E-Mail is not possible on your OS')
