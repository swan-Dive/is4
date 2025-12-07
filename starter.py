import json
import random
import secrets
from copy import copy

from pade.acl.aid import AID
from pade.acl.messages import ACLMessage
from pade.behaviours.protocols import TimedBehaviour
from pade.core.agent import Agent
from pade.misc.utility import display_message, start_loop, call_later

MANAGER_AID = AID("manager@185.200.178.189:59001")
STARTER_AID = AID('starter@localhost:59000')

class StarterAgent(Agent):
    def __init__(self, aid: AID):
        super(StarterAgent, self).__init__(aid)
        # comp_temp = ComportTemporal(self,  15.0, self.send_message)
        # self.behaviours.append(comp_temp)


    def on_start(self):
        super(StarterAgent, self).on_start()
        display_message(self.aid.localname, 'Starter Agent started.')
        call_later(15.0, self.send_message)

    def send_message(self):
        display_message(self.aid.name, 'message sent')
        message = ACLMessage(ACLMessage.INFORM)
        message.add_receiver(MANAGER_AID)
        message.set_content(json.dumps({
            "number_of_questions": 4,
            "number_of_tickets": 10
        }))
        self.send(message)


if __name__ == '__main__':
    s_agent = StarterAgent(STARTER_AID)
    start_loop([s_agent])
