import json
import pickle
import random
import re
import secrets
import socket
from copy import copy

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
MANAGER_AID = AID('manager@185.200.178.189:59001')
match_sender_pattern = r":[^ ]+ starter@(\d{1,3}(?:\.\d{1,3}){3}:\d+)"


def within_20_percent(a, b):
    """
    Проверяет, отличаются ли два числа не более чем на 20%,
    считая число a за 100%.
    """
    if a == 0:
        return False  # или обработать отдельно, если нужно

    diff_percent = abs(a - b) / a
    return diff_percent <= 0.35


class QuestionAgent(Agent):
    def __init__(self,question, aid: AID, ):
        super(QuestionAgent, self).__init__(aid)
        self.question = question

    def on_start(self):
        super(QuestionAgent, self).on_start()
        display_message(self.aid.name, 'Question Agent started.')

    def react(self, message):
        super(QuestionAgent, self).react(message)
        if message.performative == ACLMessage.INFORM and 'ticket' in str(message.sender.name):
            display_message(self.aid.name, 'Received message from ticket {}'.format(str(message.sender.name)))
            self.send_ticket_agent_question(message.sender)

    def send_ticket_agent_question(self, ticket_aid):
        ans_message = ACLMessage(ACLMessage.INFORM)
        ans_message.add_receiver(ticket_aid)
        ans_message.set_content(json.dumps(self.question))
        display_message(self.aid.name, 'Sending message to {}'.format(str(ticket_aid.name)))

        self.send(ans_message)

class TicketAgent(Agent):
    def __init__(self, aid: AID, question_agents_aids, ticket_agent_aids):
        super(TicketAgent, self).__init__(aid)
        self.questions = []
        self.question_agents_aids = question_agents_aids
        self.current_question_aids = question_agents_aids
        self.ticket_agents_aids = copy(ticket_agent_aids)
        self.number_of_questions = 0
        self.number_of_tickets=  0
        self.all_diffs = []
        self.is_running = False

    def on_start(self):
        super(TicketAgent, self).on_start()
        self.ticket_agents_aids.remove(self.aid)
        display_message(self.aid.name, 'Ticket Agent started. AIDS len: {}'.format(len(self.ticket_agents_aids)))

        # self.call_later(10.0, self.send_get_new_question)

    def react(self, message):
        super(TicketAgent, self).react(message)
        if message.performative == ACLMessage.INFORM:
            if 'ams' not in message.sender.name:
                display_message(self.aid.name, 'Received message from {}'.format(message.sender.name))

            if 'manager' in str(message.sender.name):
                content = json.loads(message.content)
                command = content['command']
                display_message(self.aid.name, 'Received command: {}'.format(command))

                if command == 'run':

                    if self.is_running:
                        display_message(self.aid.name, 'Already running questions creation')
                        return
                    self.current_question_aids = copy(self.question_agents_aids)
                    self.is_running = True
                    self.questions = []
                    self.all_diffs = []
                    self.number_of_questions = json.loads(message.content)['number_of_questions']
                    self.number_of_tickets = json.loads(message.content)['number_of_tickets']
                    self.send_get_new_question()
                elif command == 'notify':
                    self.is_running = True
                    self.inform_other_ticket_agents()
                elif command == 'remake':
                    self.is_running = True
                    idx = random.randrange(len(self.questions))
                    self.questions.pop(idx)
                    self.send_get_new_question()

            elif 'question' in  str(message.sender.name):
                self.set_new_question(json.loads(message.content))
                display_message(self.aid.name, 'Received question from question agent, questions: {}'.format(self.questions))

            elif 'ticket' in str(message.sender.name):
                self.handle_receive_ticket_agent_notif(message)

    def handle_receive_ticket_agent_notif(self, message):
        if not self.is_running:
            return
        diff = float(message.content)
        self.all_diffs.append(diff)

        if len(self.all_diffs) == self.number_of_tickets - 1:
            self.all_diffs.push(self.calc_mid_diff())
            is_within = within_20_percent(sum(self.all_diffs) / len(self.all_diffs), self.calc_mid_diff())
            display_message(self.aid.name, 'My mid diff is : {}, all_agents diff is: {}'.format( self.calc_mid_diff(), sum(self.all_diffs) / len(self.all_diffs)))
            ans_message_content = {
                'is_within': is_within,
                'questions': self.questions,
                'aid_name': self.aid.name
            }
            # display_message(self.aid.name, 'Sending done message to manager, content: {}'.format(json.dumps(ans_message_content)))
            ans_message = ACLMessage(ACLMessage.INFORM)
            ans_message.add_receiver(MANAGER_AID)
            ans_message.set_content(json.dumps(ans_message_content))
            self.all_diffs = []
            self.is_running = False
            self.send(ans_message)



    def set_new_question(self, new_question):
        if len(self.questions) < self.number_of_questions:

            found_existing_field = False
            for q in  self.questions:
                if q['field'] == new_question['field']:
                    found_existing_field = True
                    break
            if not found_existing_field:
                self.questions.append(new_question)

        if len(self.questions) == self.number_of_questions:
            self.inform_other_ticket_agents()
        else:
            self.send_get_new_question()

    def send_get_new_question(self):
        message = ACLMessage(ACLMessage.INFORM)
        ch = secrets.choice(self.question_agents_aids)
        # self.current_question_aids.remove(ch)
        message.add_receiver(ch)
        display_message(self.aid.name, 'Sending message to {}'.format(str(ch.name)))
        message.set_content(json.dumps({
            "number_of_questions": random.randint(2,5),
            "number_of_tickets": 10
        }))
        self.send(message)

    def inform_other_ticket_agents(self):
        display_message(self.aid.name, 'informing other agents')
        for ticket_agent in self.ticket_agents_aids:
            message = ACLMessage(ACLMessage.INFORM)
            message.add_receiver(ticket_agent)
            message.set_content(str(self.calc_mid_diff()))
            self.send(message)

    def calc_mid_diff(self):
        mid_diff = 0
        for a_question in self.questions:
            mid_diff += int(a_question.get('diff', 0))
        mid_diff = mid_diff / len(self.questions) if len(self.questions) != 0 else 0
        return mid_diff

class ManagerAgent(Agent):
    def __init__(self, aid: AID, ticket_agents):
        super(ManagerAgent, self).__init__(aid)
        self.ticket_agents = ticket_agents
        self.tickets = []
        self.number_of_tickets = 0
        self.number_of_questions = 0
        self.ip_port = None

    def on_start(self):
        super(ManagerAgent, self).on_start()
        display_message(self.aid.localname, 'Manager Agent started.')

    def react(self, message):
        try:
            super(ManagerAgent, self).react(message)
        except Exception as e:
            pass
        match_content = re.search(r':content\s*"(.+)"', str(message))
        if not match_content:
            return
        received_content = str(match_content.group(1))
        match_sender = re.search(match_sender_pattern, str(message))

        if match_sender:
            self.ip_port = match_sender.group(1)
            display_message(
                self.aid.localname, 'The sender is: {}'.format(self.ip_port))

        if 'number_of_questions' in received_content:
            display_message(self.aid.localname, 'Received message from starter: {}'.format(received_content) )
            content = json.loads(received_content)
            number_of_tickets = content.get('number_of_tickets', None)
            number_of_questions = content.get('number_of_questions', None)
            if number_of_tickets is not None and number_of_questions is not None:
                self.number_of_tickets = number_of_tickets
                self.number_of_questions = number_of_questions
                self.react_create_ticket_list(number_of_tickets, number_of_questions)

        elif message.performative == ACLMessage.INFORM and 'ticket' in  message.sender.name:
            self.handle_ticket_message(message)


    def react_create_ticket_list(self, number_of_tickets, number_of_questions):
        c_ticket_agents = copy(self.ticket_agents)

        for i in range(number_of_tickets):
            new_ticket_agent = secrets.choice(c_ticket_agents)
            c_ticket_agents.remove(new_ticket_agent)

            message = ACLMessage(ACLMessage.INFORM)
            message.add_receiver(new_ticket_agent)
            display_message(self.aid.name, 'Sending message to {}'.format(str(new_ticket_agent.name)))
            message.set_content(json.dumps({
                "command": "run",
                "number_of_questions": number_of_questions,
                "number_of_tickets": number_of_tickets
            }))
            self.send(message)

    def handle_ticket_message(self, message):
        content = json.loads(message.content)
        self.tickets.append(content)
        display_message(self.aid.name, 'Received content: {}'.format(message.content))
        if len(self.tickets) == self.number_of_tickets:
            all_within = True
            for ticket in self.tickets:
                if not ticket['is_within']:
                    all_within = False
                    break

            if all_within:
                display_message(self.aid.name, 'ALL WITHIN')
                if self.ip_port:
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    parts = (str(self.ip_port).split(":"))
                    s.connect((parts[0], int(parts[1])))
                    s.sendall(pickle.dumps(self.tickets))
                    s.close()
                self.tickets = []
                return

            for ticket in self.tickets:
                q_aid = copy(AID(ticket['aid_name']))
                if ticket['is_within']:
                    call_later(1.0, self.send_command_notify, q_aid )
                else:
                    call_later(1.0, self.send_command_remake, q_aid)
            self.tickets = []

    def send_command_notify(self, ticket_agent_aid):
        message = ACLMessage(ACLMessage.INFORM)
        message.add_receiver(ticket_agent_aid)
        display_message(self.aid.name, 'Sending command notify to {} '.format(str(ticket_agent_aid.name)))
        message.set_content(json.dumps({
            "command": "notify",
            "number_of_questions": self.number_of_questions,
            "number_of_tickets": self.number_of_tickets
        }))
        self.send(message)

    def send_command_remake(self, ticket_agent_aid):
        message = ACLMessage(ACLMessage.INFORM)
        message.add_receiver(ticket_agent_aid)
        display_message(self.aid.name, 'Sending command remake to {}'.format(str(ticket_agent_aid.name)))
        message.set_content(json.dumps({
            "command": "remake",
            "number_of_questions": self.number_of_questions,
            "number_of_tickets": self.number_of_tickets
        }))
        self.send(message)

if __name__ == '__main__':
          
    gen_questions = None
    with open("data.json", 'r') as f:
        gen_questions = json.loads(f.read())
          
    question_agents_aids = list()
    ticket_agents_aids = list()
    agents = []
    for index, question in enumerate(gen_questions):
        port = 60000 + index
        aid = AID('question_{}@localhost:{}'.format(port, port))
        agent = QuestionAgent(question=question, aid=aid)
        question_agents_aids.append(aid)
        agents.append(agent)

    for i in range(100):
        port = 61000 + i
        aid = AID('ticket_{}@localhost:{}'.format(port, port))

        ticket_agents_aids.append(aid)

    for aid in ticket_agents_aids:
        agent = TicketAgent(aid=aid, question_agents_aids=question_agents_aids, ticket_agent_aids=ticket_agents_aids)
        agents.append(agent)

    m_agent = ManagerAgent(MANAGER_AID, ticket_agents=ticket_agents_aids)
    agents.append(m_agent)

    # agents.append(s_agent)

    start_loop(agents)

