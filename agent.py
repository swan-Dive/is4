from pade.misc.utility import display_message, start_loop
from pade.core.agent import Agent
from pade.acl.messages import ACLMessage
from pade.acl.aid import AID
from pade.behaviours.protocols import FipaRequestProtocol
from sys import argv

class MessageReceiverProtocol(FipaRequestProtocol):
    def __init__(self, agent):
        super(MessageReceiverProtocol, self).__init__(agent=agent,
                                                     message=None,
                                                     is_initiator=False)

    def handle_request(self, message):
        super(MessageReceiverProtocol, self).handle_request(message)
        display_message(self.agent.aid.localname, f'Message received: {message.content}')
        print(f'[{self.agent.aid.localname}] Received message content: {message.content}')  # добавлен print
        reply = message.create_reply()
        reply.set_performative(ACLMessage.INFORM)
        reply.set_content('Message received successfully.')
        self.agent.send(reply)

class MessageSenderProtocol(FipaRequestProtocol):
    def __init__(self, agent, message):
        super(MessageSenderProtocol, self).__init__(agent=agent,
                                                   message=message,
                                                   is_initiator=True)

    def handle_inform(self, message):
        display_message(self.agent.aid.localname, f'Reply from receiver: {message.content}')
        print(f'[{self.agent.aid.localname}] Received reply content: {message.content}')  # добавлен print


class ReceiverAgent(Agent):
    def __init__(self, aid):
        super(ReceiverAgent, self).__init__(aid=aid)
        self.behaviours.append(MessageReceiverProtocol(self))

class SenderAgent(Agent):
    def __init__(self, aid, receiver_aid):
        super(SenderAgent, self).__init__(aid=aid)
        message = ACLMessage(ACLMessage.REQUEST)
        message.set_protocol(ACLMessage.FIPA_REQUEST_PROTOCOL)
        message.add_receiver(receiver_aid)
        message.set_content('Hello from SenderAgent!')
        self.behaviours.append(MessageSenderProtocol(self, message))


if __name__ == '__main__':
    base_port = int(argv[1]) if len(argv) > 1 else 9000

    receiver_name = f'receiver@localhost:{base_port}'
    sender_name = f'sender@localhost:{base_port + 1}'

    receiver_agent = ReceiverAgent(AID(name=receiver_name))
    sender_agent = SenderAgent(AID(name=sender_name), AID(name=receiver_name))

    agents = [receiver_agent, sender_agent]
    start_loop(agents)
