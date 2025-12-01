import json
import random
import secrets
import uuid
from itertools import combinations
from secrets import choice

from pade.acl.aid import AID
from pade.acl.messages import ACLMessage
from pade.core.agent import Agent
from pade.misc.utility import display_message, call_later, start_loop

fields = ['Теоретическая информатика', "Техническая информатика", 'Прикладная информатика', 'Информационные системы',
          'Компьютерные сети и телекоммуникации', 'Базы данных', 'Информационная безопасность и кибербезопасность',
          'Анализ данных и визуализация']

difficulties = [1,2,3,4,5]

MANAGER_AID = AID('manager@localhost:52000')
TICKET_AID = AID('ticket@localhost:52001')
QUESTION_AID = AID('question@localhost:52002')
STARTED_AID = AID('starter@localhost:52003')

class QuestionAgent(Agent):
    def __init__(self,pos_questions, aid: AID, ):
        super(QuestionAgent, self).__init__(aid)
        self.questions = pos_questions

    def on_start(self):
        super(QuestionAgent, self).on_start()
        display_message(self.aid.localname, 'Question Agent started.')

    def react(self, message):
        super(QuestionAgent, self).react(message)
        if message.performative == ACLMessage.INFORM and message.sender == TICKET_AID:
            display_message(self.aid.localname, 'Received message from ticket manager')

            self.react_create_question(message)

    def react_create_question(self, message):
        content = json.loads(message.content)
        info_id = content.get('info_id', None)
        diff = content.get('diff', None)
        field = content.get('field', None)
        appl_questions = []
        for q in self.questions:
            if q['diff'] == diff and q['field'] == field:
                appl_questions.append(q)
        rand_question = choice(appl_questions)
        message = ACLMessage(ACLMessage.INFORM)
        message.add_receiver(TICKET_AID)
        message.set_content(json.dumps({
            "info_id": str(info_id),
            "question": rand_question
        }))
        display_message(self.aid.localname, 'question created: {}'.format(str(rand_question)))

        self.send(message)


class TicketAgent(Agent):
    def __init__(self, aid: AID):
        super(TicketAgent, self).__init__(aid)
        self.info = {}

    def on_start(self):
        super(TicketAgent, self).on_start()
        display_message(self.aid.localname, 'Ticket Agent started.')

    def react(self, message):
        super(TicketAgent, self).react(message)

        if message.performative == ACLMessage.INFORM and message.sender == MANAGER_AID:
            display_message(self.aid.localname, 'Received message from manager')

            self.react_create_ticket(message)
        elif message.performative == ACLMessage.INFORM and message.sender == QUESTION_AID:
            display_message(self.aid.localname, 'Received message from q agent')

            self.react_append_question(message)


    def react_create_ticket(self, message):
        info_id = uuid.uuid4()

        content = json.loads(message.content)
        number_of_questions = content.get('number_of_questions', 2)
        req_diff = content.get('req_diff', 10) # TODO: проверка на сложность
        diff_combs = []
        for comb  in combinations(difficulties, number_of_questions):
            if sum(comb) == req_diff:
                diff_combs.append(list(comb))
        
        field_combs = combinations(fields, number_of_questions)
        
        ticket_combs = []
        
        for field_comb in field_combs:
            for diff_comb in diff_combs:
                ticket_combs.append({
                    'fields': field_comb,
                    'diffs': diff_comb
                })
        
        self.info[str(info_id)] = {
            "questions": [],
            "number_of_questions": number_of_questions,
            "req_diff": req_diff,
            'combs': ticket_combs
        }
        field, diff = self.get_next_comb(str(info_id))
        self.create_create_q_message(info_id,field, diff )


    def create_create_q_message(self, uid, field, diff):
        message = ACLMessage(ACLMessage.INFORM)
        message.add_receiver(QUESTION_AID)
        message.set_content(json.dumps({
            "info_id": str(uid),
            "field": field,
            "diff": diff
        }))
        display_message(self.aid.localname, 'create question message to q_agent sent')

        self.send(message)


    def react_append_question(self, message):
        content = json.loads(message.content)

        info_id = content.get('info_id', None)
        display_message(self.aid.localname, 'received append question to uid:{}'.format(info_id))
        ticket = self.info.get(info_id, None)
        if ticket is None:
            pass #todo: validate
            raise

        question = content.get('question', None)

        ticket["questions"].append(question)
        field, diff = self.get_next_comb(info_id)
        if len(ticket["questions"]) >= ticket['number_of_questions']:
            display_message(self.aid.localname, 'we are done: {}'.format(ticket['questions']))
        else:
            self.create_create_q_message(info_id, field, diff)
            display_message(
                self.aid.localname, 'len of questions: {}'.format(len(ticket["questions"])) )
    
    def get_next_comb(self, uid):
        info = self.info.get(uid, None)
        combs = info.get('combs', None)
        return combs[0]['fields'][len(info['questions'])], combs[0]['diffs'][len(info['questions'])]
        
    

class ManagerAgent(Agent):
    def __init__(self, aid: AID):
        super(ManagerAgent, self).__init__(aid)

    def on_start(self):
        super(ManagerAgent, self).on_start()
        display_message(self.aid.localname, 'Manager Agent started.')

    def react(self, message):
        super(ManagerAgent, self).react(message)

        if message.performative == ACLMessage.INFORM and message.sender == STARTED_AID:
            display_message(self.aid.localname, 'Received message from starter')
            self.react_create_ticket_list(message)

    def react_create_ticket_list(self, message):
        message = ACLMessage(ACLMessage.INFORM)
        message.add_receiver(TICKET_AID)
        message.set_content(json.dumps({
            "number_of_questions": 2,
            "req_diff": 10,
        }))
        display_message(self.aid.localname, 'create ticket message to ticket agent sent')

        self.send(message)

class StarterAgent(Agent):
    def __init__(self, aid: AID):
        super(StarterAgent, self).__init__(aid)


    def on_start(self):
        super(StarterAgent, self).on_start()
        display_message(self.aid.localname, 'Starter Agent started.')
        self.send_message()
        call_later(8.0, self.send_message)

    def send_message(self):
        message = ACLMessage(ACLMessage.INFORM)
        message.add_receiver(MANAGER_AID)
        message.set_content('Ola')
        display_message(self.aid.localname, 'message_sent: {}'.format('OLA'))
        self.send(message)

if __name__ == '__main__':
    questions = [{
        "id": 'Qid_{}'.format(i),
        "diff": random.randint(1, 5),
        "field": secrets.choice(fields)
    } for i in range(0, 100)]

    q_agent = QuestionAgent(aid=QUESTION_AID, pos_questions=questions)
    t_agent = TicketAgent(TICKET_AID)

    m_agent = ManagerAgent(MANAGER_AID)
    s_agent = StarterAgent(STARTED_AID)

    start_loop([q_agent, t_agent, m_agent, s_agent])
