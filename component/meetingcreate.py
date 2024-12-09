from PyQt5.QtCore import pyqtSignal, QObject

from view.homescreen import HomeInterface, MeetingConfigMessageBox


class MeetingCreate(QObject):

    meeting_created = pyqtSignal(dict) # emit meeting data to home controller

    def __init__(self, view: HomeInterface):
        super().__init__()
        self.view = view

        self.view.banner.createButton.clicked.connect(self.handle_create_meeting)

        self.form = {}


    def handle_create_meeting(self):
        mbox = MeetingConfigMessageBox(self.view)
        if mbox.exec():
            self.form['meeting_name'] = mbox.meetingName()
            self.form['meeting_type'] = mbox.meetingType()
            self._create_meeting()


    def _create_meeting(self):
        print('Creating meeting...')
        print(self.form)
        self.meeting_created.emit(self.form)
        # meetingcardgroup.add_meeting(self.form, owned=True)
        pass