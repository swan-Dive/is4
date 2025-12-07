import json
import random
import secrets

from pade.acl.aid import AID
from pade.acl.messages import ACLMessage
from pade.behaviours.protocols import TimedBehaviour
from pade.core.agent import Agent
from pade.misc.utility import display_message, start_loop, call_later

fields = ['Теоретическая информатика', "Техническая информатика", 'Прикладная информатика', 'Информационные системы',
          'Компьютерные сети и телекоммуникации', 'Базы данных', 'Информационная безопасность и кибербезопасность',
          'Анализ данных и визуализация']

difficulties = [1,2,3,4,5]
STARTER_AID = AID('starter@localhost:59000')
MANAGER_AID = AID('manager@localhost:59001')


class QuestionAgent(Agent):
    def __init__(self,question, aid: AID, ):
        super(QuestionAgent, self).__init__(aid)
        self.question = question

    def on_start(self):
        super(QuestionAgent, self).on_start()
        display_message(self.aid.name, 'Question Agent started.')

    def react(self, message):
        super(QuestionAgent, self).react(message)
        if message.performative == ACLMessage.INFORM:
            display_message(self.aid.name, 'Received message from ticket {}'.format(str(message.sender.name)))




class TicketAgent(Agent):
    def __init__(self, aid: AID, question_agents_aids):
        super(TicketAgent, self).__init__(aid)
        self.info = {}
        self.question_agents_aids = question_agents_aids

    def on_start(self):
        super(TicketAgent, self).on_start()
        display_message(self.aid.name, 'Ticket Agent started.')
        self.call_later(30.0, self.send_message)

    def react(self, message):
        super(TicketAgent, self).react(message)

    def send_message(self):
        message = ACLMessage(ACLMessage.INFORM)
        ch = secrets.choice(self.question_agents_aids)
        message.add_receiver(ch)
        display_message(self.aid.name, 'Sending message to {}'.format(str(ch.name)))
        message.set_content(json.dumps({
            "number_of_questions": random.randint(2,5),
            "number_of_tickets": 10
        }))
        self.send(message)



class ManagerAgent(Agent):
    def __init__(self, aid: AID, questions):
        super(ManagerAgent, self).__init__(aid)
        self.questions = questions
        self.number_of_tickets = 0
        self.number_of_questions = 0

    def on_start(self):
        super(ManagerAgent, self).on_start()
        display_message(self.aid.localname, 'Manager Agent started.')

    def react(self, message):
        super(ManagerAgent, self).react(message)

    #     if message.performative == ACLMessage.INFORM and message.sender == STARTER_AID:
    #         display_message(self.aid.localname, 'Received message from starter')
    #         content = json.loads(message.content)
    #         number_of_tickets = content.get('number_of_tickets', None)
    #         number_of_questions = content.get('number_of_questions', None)
    #
    #         if number_of_tickets is not None and number_of_questions is not None:
    #             self.number_of_tickets = number_of_tickets
    #             self.number_of_questions = number_of_questions
    #             self.react_create_ticket_list()
    #
    #
    #
    # def react_create_ticket_list(self):
    #     pass

class ComportTemporal(TimedBehaviour):
    def __init__(self, agent, time, send_message):
        super(ComportTemporal, self).__init__(agent, time)
        self.send_message = send_message
    def on_time(self):
        super(ComportTemporal, self).on_time()
        display_message(self.agent.aid.localname, 'Hello World!')
        self.send_message()



class StarterAgent(Agent):
    def __init__(self, aid: AID):
        super(StarterAgent, self).__init__(aid)
        # comp_temp = ComportTemporal(self,  15.0, self.send_message)
        # self.behaviours.append(comp_temp)


    def on_start(self):
        super(StarterAgent, self).on_start()
        display_message(self.aid.localname, 'Starter Agent started.')
        # call_later(10.0, self.send_message)

    def send_message(self):
        message = ACLMessage(ACLMessage.INFORM)
        message.add_receiver(MANAGER_AID)
        message.set_content(json.dumps({
            "number_of_questions": random.randint(2,5),
            "number_of_tickets": 10
        }))
        self.send(message)


if __name__ == '__main__':
    gen_questions = [{
        "id": 'Qid_{}'.format(i),
        "diff": random.randint(min(difficulties), max(difficulties)),
        "field": secrets.choice(fields)
    } for i in range(0, 100)]

    m_agent = ManagerAgent(MANAGER_AID, questions=gen_questions)
    s_agent = StarterAgent(STARTER_AID)

    question_agents_aids = list()
    agents = [m_agent, s_agent]
    for index, question in enumerate(gen_questions):
        port = 60000 + index
        aid = AID('question_{}@localhost:{}'.format(port, port))
        agent = QuestionAgent(question=question, aid=aid)
        question_agents_aids.append(aid)
        agents.append(agent)

    for i in range(100):
        port = 61000 + i
        aid = AID('ticket_{}@localhost:{}'.format(port, port))
        agent = TicketAgent(aid=aid, question_agents_aids=question_agents_aids)
        agents.append(agent)

    start_loop(agents)

