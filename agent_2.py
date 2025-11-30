from pade.core.agent import Agent
from pade.acl.aid import AID
from pade.acl.messages import ACLMessage
from pade.behaviours.protocols import FipaRequestProtocol
from pade.misc.utility import display_message, start_loop

# Вопросы: (id, раздел, сложность)
questions = [
    (1, "Математика", 3),
    (2, "Физика", 4),
    (3, "Информатика", 2),
    (4, "Математика", 5),
    (5, "Физика", 1),
    (6, "Информатика", 3),
]

############# QuestionAgent #############

class QuestionRequestReceiver(FipaRequestProtocol):
    def __init__(self, agent):
        super().__init__(agent=agent, message=None, is_initiator=False)

    def handle_request(self, message):
        super().handle_request(message)
        display_message(self.agent.aid.localname, 'Получен запрос вопросов')
        reply = message.create_reply()
        reply.set_performative(ACLMessage.INFORM)
        reply.set_content(str(self.agent.questions))
        self.agent.send(reply)


class QuestionAgent(Agent):
    def __init__(self, aid, questions_subset):
        super().__init__(aid)
        self.questions = questions_subset
        self.behaviours.append(QuestionRequestReceiver(self))

############# TicketAgent #############

class TicketRequestReceiver(FipaRequestProtocol):
    def __init__(self, agent):
        super().__init__(agent=agent, message=None, is_initiator=False)

    def handle_request(self, message):
        super().handle_request(message)
        content = message.content
        display_message(self.agent.aid.localname, "Получен билет")
        tickets = eval(content)
        display_message(self.agent.aid.localname, "Сформированные экзаменационные билеты:")
        for i, (q1, q2) in enumerate(tickets, start=1):
            display_message(self.agent.aid.localname,
                            f"Билет {i}: Вопрос 1 [{q1[0]}] - {q1[1]} (сложность {q1[2]}), "
                            f"Вопрос 2 [{q2[0]}] - {q2[1]} (сложность {q2[2]}), "
                            f"Суммарная сложность: {q1[2] + q2[2]}")

        reply = message.create_reply()
        reply.set_performative(ACLMessage.CONFIRM)
        self.agent.send(reply)


class TicketAgent(Agent):
    def __init__(self, aid):
        super().__init__(aid)
        self.behaviours.append(TicketRequestReceiver(self))

############# CoordinatorAgent #############

class QuestionRequestSender(FipaRequestProtocol):
    def __init__(self, agent, message, question_agent_aid):
        super().__init__(agent=agent, message=message, is_initiator=True)
        self.question_agent_aid = question_agent_aid

    def handle_inform(self, message):
        super().handle_inform(message)
        self.agent.collect_questions(message)

    def handle_refuse(self, message):
        display_message(self.agent.aid.localname, f"Запрос вопроса у {self.question_agent_aid.localname} отклонён")

class TicketRequestSender(FipaRequestProtocol):
    def __init__(self, agent, message):
        super().__init__(agent=agent, message=message, is_initiator=True)

    def handle_confirm(self, message):
        display_message(self.agent.aid.localname, "TicketAgent подтвердил получение билетов")

class CoordinatorAgent(Agent):
    def __init__(self, aid, question_agents, ticket_agent):
        super().__init__(aid)
        self.question_agents = question_agents
        self.ticket_agent = ticket_agent
        self.all_questions = []
        self.pending_responses = 0

    def on_start(self):
        display_message(self.aid.localname, "Запуск CoordinatorAgent")
        self.pending_responses = len(self.question_agents)
        for qa in self.question_agents:
            msg = ACLMessage(ACLMessage.REQUEST)
            msg.add_receiver(qa)
            msg.set_protocol(ACLMessage.FIPA_REQUEST_PROTOCOL)
            msg.set_content("send_questions")
            behaviour = QuestionRequestSender(self, msg, qa)
            self.behaviours.append(behaviour)
            behaviour.on_start()

    def collect_questions(self, message):
        q_list = eval(message.content)
        self.all_questions.extend(q_list)
        self.pending_responses -= 1
        if self.pending_responses == 0:
            tickets = self.form_tickets(self.all_questions)
            # Отправляем билеты TicketAgent
            msg = ACLMessage(ACLMessage.REQUEST)
            msg.add_receiver(self.ticket_agent)
            msg.set_protocol(ACLMessage.FIPA_REQUEST_PROTOCOL)
            msg.set_content(str(tickets))
            behavior = TicketRequestSender(self, msg)
            self.behaviours.append(behavior)
            behavior.on_start()

    def form_tickets(self, questions):
        from collections import defaultdict
        by_section = defaultdict(list)
        for q in questions:
            by_section[q[1]].append(q)

        pairs = []
        sections = list(by_section.keys())
        for i in range(len(sections)):
            for j in range(i + 1, len(sections)):
                sec1 = sections[i]
                sec2 = sections[j]
                for q1 in by_section[sec1]:
                    for q2 in by_section[sec2]:
                        pairs.append((q1, q2))

        pairs.sort(key=lambda pair: pair[0][2] + pair[1][2])

        used = set()
        tickets = []
        for p in pairs:
            ids = (p[0][0], p[1][0])
            if ids[0] not in used and ids[1] not in used:
                tickets.append(p)
                used.update(ids)

        return tickets

############# Запуск #############
if __name__ == '__main__':
    from pade.misc import utility

    # Разделяем вопросы по агентам
    q_agents_questions = [
        questions[:2],
        questions[2:4],
        questions[4:]
    ]

    agents = []

    question_agents_aids = []
    for i, qsubset in enumerate(q_agents_questions):
        aid = AID(name=f"question_agent{i}@localhost:888{i}")
        question_agents_aids.append(aid)
        agent = QuestionAgent(aid, qsubset)
        agents.append(agent)

    ticket_agent_aid = AID(name="ticket_agent@localhost:8890")
    ticket_agent = TicketAgent(ticket_agent_aid)
    agents.append(ticket_agent)

    coordinator_aid = AID(name="coordinator_agent@localhost:8891")
    coordinator_agent = CoordinatorAgent(coordinator_aid, question_agents_aids, ticket_agent_aid)
    agents.append(coordinator_agent)

    utility.start_loop(agents)
