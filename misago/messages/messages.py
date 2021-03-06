class Messages(object):
    def __init__(self, session):
        self.session = session
        self.messages = session.get('messages_list', [])
        self.session['messages_list'] = []
        
    def set_message(self, message, type='info', owner=None):
        message.type = type
        message.owner = owner
        self.messages.append(message)
    
    def set_flash(self, message, type='info', owner=None):
        self.set_message(message, type, owner)
        self.session['messages_list'].append(message)
        
    def get_message(self, owner=None):
        for index, message in enumerate(self.messages):
            if message.owner == owner:
                del self.messages[index]
                return message
        return None