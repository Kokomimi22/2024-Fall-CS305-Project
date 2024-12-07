from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget
from qfluentwidgets import NavigationAvatarWidget, AvatarWidget, BodyLabel, CaptionLabel, RoundMenu, FluentIcon, Action


class ClickedNavigationAvatarWidget(NavigationAvatarWidget):
    '''
    override the click event
    '''

    def __init__(self, name: str, avatarPath: str, parent=None):
        super().__init__(name, avatarPath, parent)
        self.menu = None

    def mousePressEvent(self, e):
        super().mousePressEvent(e)
        if e.button() == Qt.LeftButton:
            self.createProfileWidget(e)

    class ProfileCard(QWidget):

        def __init__(self, avatarPath: str, name: str, email: str, parent=None):
            super().__init__(parent=parent)
            self.avatar = AvatarWidget(avatarPath, self)
            self.nameLabel = BodyLabel(name, self)
            self.emailLabel = CaptionLabel(email, self)

            self.setFixedSize(307, 82)
            self.avatar.setRadius(24)
            self.avatar.move(2, 6)
            self.nameLabel.move(64, 13)
            self.emailLabel.move(64, 32)

    def createProfileWidget(self, e, name='zhiyoko', email='shokokawaii@outlook.com', avatarPath='resources/shoko.png'):
        menu = RoundMenu(self)
        card = self.ProfileCard(avatarPath, name, email, menu)
        menu.addWidget(card, selectable=False)

        menu.addSeparator()
        menu.addActions([
            Action(FluentIcon.PEOPLE, 'Manage Account'),
            Action(FluentIcon.CANCEL, 'Logout'),
        ])
        menu.addSeparator()
        menu.addAction(Action(FluentIcon.SETTING, 'Settings'))

        self.menu = menu
        menu.exec(e.globalPos())