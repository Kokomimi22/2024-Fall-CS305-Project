from config import MessageType


class MessageFormat:
    def __init__(self, type: str, sender_name: str, message: str):
        self.type = type
        self.sender_name = sender_name
        self.message = message

    def pack(self):
        return {
            'type': self.type,
            'sender_name': self.sender_name,
            'message': self.message
        }

    @staticmethod
    def unpack(data: dict) -> tuple:
        raise NotImplementedError("This method cannot be called directly or by RequestFormat subclass.")

class RequestFormat(MessageFormat):
    pass

class ResponseFormat(MessageFormat):
    @staticmethod
    def unpack(data: dict) -> tuple[str, str]:
        """
        @param data: dict
        @return tuple[str, str] (sender_name, message)
        """
        try:
            if data.get('type') == MessageType.TEXT_MESSAGE.value:
                return data['sender_name'], data['message']
            else:
                raise ValueError("Invalid message type.")

        except KeyError:
            raise ValueError("Invalid message format.")