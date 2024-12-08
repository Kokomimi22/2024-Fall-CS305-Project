from view.meetingscreen import MeetingInterfaceBase

class MeetingController:
    closed = MeetingInterfaceBase.close_signal
    def __init__(self, meetingUI, app):
        self.meetingUI = meetingUI
        self.app = app
        self.chatArea = self.meetingUI.chatArea
        self.isOwned = False
        self.user_view = None

        self.displayArea = [] # grid layout
        self.pos_map = {} # {user_id: pos}

        # connect signal
        self.meetingUI.close_signal.connect(self.handle_close)

    def handle_close(self, flag):
        # self.messageBox.show()
        self.quit()

    def quit(self):
        self.app.quit_conf()
        self.app.switch_ui('main')
        self.close()