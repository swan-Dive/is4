import random
import secrets

from pade.acl.aid import AID
from pade.acl.messages import ACLMessage
from pade.core.agent import Agent
from pade.misc.utility import display_message, call_later, start_loop

STARTED_AID = AID('starter@localhost:52003')

MANAGER_AID = AID('manager@localhost:52000')


class StarterAgent(Agent):
    def __init__(self, aid: AID):
        super(StarterAgent, self).__init__(aid)


    def on_start(self):
        super(StarterAgent, self).on_start()
        display_message(self.aid.localname, 'Starter Agent started.')
        call_later(4.0, self.send_message)

    def send_message(self):
        message = ACLMessage(ACLMessage.INFORM)
        message.add_receiver(MANAGER_AID)
        message.set_content({
            "number_of_tickets": 5,
            "number_of_questions": 5
        })
        self.send(message)

if __name__ == '__main__':



    s_agent = StarterAgent(STARTED_AID)

    start_loop([s_agent])
