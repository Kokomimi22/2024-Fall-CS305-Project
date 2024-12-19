from PyQt5.QtCore import QObject, pyqtSignal


class MeetingCardsGroupHandler(QObject):

    meeting_joined = pyqtSignal(int, str)

    def __init__(self, view, app):
        super().__init__()
        self.view = view
        self.app = app
        self.meetings = []
        self.meeting_card_map = {}

        # connect signal
        self.view.scroll_area_entered.connect(self.flush_meeting_cards)

        # initial flush
        self.flush_meeting_cards()

    # test function
    def flush(self):
        print('flushing meeting cards')

    def flush_meeting_cards(self):
        next_meetings, details = self.app.get_meetings()
        add_meetings = list(set(next_meetings) - set(self.meetings))
        remove_meetings = list(set(self.meetings) - set(next_meetings))
        for meeting_id in add_meetings:
            meeting_name = details[meeting_id]['conference_name']
            meeting_creator = details[meeting_id]['manager_id']
            self.addMeetingCardByID(meeting_id, meeting_name, meeting_creator)
        for meeting_id in remove_meetings:
            self.removeMeetingCardByID(meeting_id)
        self.meetings = next_meetings

    def addMeetingCardByID(self, meeting_id, meeting_name, meeting_creator):
        # update meeting card view
        card = self.view.addConferenceCard(meeting_name, meeting_id, meeting_creator)
        # update meeting card map
        self.meeting_card_map[meeting_id] = card
        # connect signal
        card.conf_joined.connect(self.meeting_joined)

    def removeMeetingCardByID(self, meeting_id):
        # update meeting card view
        self.view.removeConferenceCard(self.meeting_card_map[meeting_id])
        # update meeting card map
        del self.meeting_card_map[meeting_id]
        # disconnect signal