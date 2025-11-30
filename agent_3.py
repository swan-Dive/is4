from pade.core.agent import Agent
from pade.acl.aid import AID
from pade.acl.messages import ACLMessage
from pade.behaviours.protocols import FipaRequestProtocol
from pade.misc.utility import display_message
import asyncio

# Вопросы: (id, раздел, сложность)
questions = [
    (1, "Математика", 3),
    (2, "Физика", 4),
    (3, "Информатика", 2),
    (4, "Математика", 5),
    (5, "Физика", 1),
    (6, "Информатика", 3),
]

# Сообщения между агентами будут с содержанием вопроса или билета

class CoordinatorAgent(Agent):
    def __init__(self, aid, question_agents, ticket_agent):
        super().__init__(aid)
        self.question_agents = question_agents
        self.ticket_agent = ticket_agent
        self.pending_responses = 0
        self.all_questions = []

    def on_start(self):
        display_message(self.aid.localname, "Запуск CoordinatorAgent")
        # Запрашиваем вопросы у всех агентоа
        self.pending_responses = len(self.question_agents)
        for agent_aid in self.question_agents:
            msg = ACLMessage(ACLMessage.REQUEST)
            msg.add_receiver(agent_aid)
            msg.set_content("send_questions")
            self.post(msg)

    def react(self, message):
        if message.performative == ACLMessage.INFORM and message.content.startswith("questions:"):
            # Получаем список вопросов от QuestionAgent
            content = message.content[len("questions:"):]
            # Преобразуем из строки в список кортежей
            questions_list = eval(content)
            self.all_questions.extend(questions_list)
            self.pending_responses -= 1
            if self.pending_responses == 0:
                # Все вопросы получены — формируем билеты
                tickets = self.form_tickets(self.all_questions)
                # Отправляем билет агенту TicketAgent
                msg = ACLMessage(ACLMessage.INFORM)
                msg.add_receiver(self.ticket_agent)
                msg.set_content(f"tickets:{tickets}")
                self.post(msg)

    def form_tickets(self, questions):
        # Формируем билеты из 2 вопросов с разным разделом и равной суммарной сложностью
        # Сначала группируем по разделу
        from collections import defaultdict
        by_section = defaultdict(list)
        for q in questions:
            by_section[q[1]].append(q)

        # Берем все пары вопросов из разных разделов
        pairs = []
        sections = list(by_section.keys())
        for i in range(len(sections)):
            for j in range(i+1, len(sections)):
                sec1 = sections[i]
                sec2 = sections[j]
                for q1 in by_section[sec1]:
                    for q2 in by_section[sec2]:
                        pairs.append((q1, q2))

        # Сортируем пары по сумме сложности
        pairs.sort(key=lambda pair: pair[0][2] + pair[1][2])

        # Пытаемся подобрать равные по сложности пары
        # Для простоты возьмем первые N пар с минимальной дисперсией сложности
        # Пример: сгенерируем столько билетов, сколько максимум может быть без повторов вопросов

        used_questions = set()
        tickets = []
        for pair in pairs:
            ids = (pair[0][0], pair[1][0])
            if ids[0] not in used_questions and ids[1] not in used_questions:
                tickets.append((pair[0], pair[1]))
                used_questions.update(ids)

        return tickets


class QuestionAgent(Agent):
    def __init__(self, aid, questions_subset):
        super().__init__(aid)
        self.questions = questions_subset

    def react(self, message):
        if message.performative == ACLMessage.REQUEST and message.content == "send_questions":
            msg = ACLMessage(ACLMessage.INFORM)
            msg.add_receiver(message.sender)
            msg.set_content(f"questions:{self.questions}")
            await self.post(msg)


class TicketAgent(Agent):
    def __init__(self, aid):
        super().__init__(aid)

    def react(self, message):
        if message.performative == ACLMessage.INFORM and message.content.startswith("tickets:"):
            content = message.content[len("tickets:"):]
            tickets = eval(content)
            display_message(self.aid.localname, "Сформированные экзаменационные билеты:")
            for i, (q1, q2) in enumerate(tickets, start=1):
                display_message(self.aid.localname,
                                f"Билет {i}: Вопрос 1 [{q1[0]}] - {q1[1]} (сложность {q1[2]}), "
                                f"Вопрос 2 [{q2[0]}] - {q2[1]} (сложность {q2[2]}), "
                                f"Суммарная сложность: {q1[2] + q2[2]}")


if __name__ == '__main__':
    import pade.misc.utility as utility
    import sys

    # Создаем агентов

    # Разбиваем вопросы по агентам для демонстрации (можно изменить логику)
    q_agents_questions = [
        questions[:2],   # Agent 1: первые 2 вопроса
        questions[2:4],  # Agent 2: 3 и 4
        questions[4:],   # Agent3: 5 и 6
    ]

    agents = []

    # Question Agents
    question_agents_aids = []
    for i, q_subset in enumerate(q_agents_questions):
        aid = AID(name=f"question_agent{i}@localhost:888{i}")
        question_agents_aids.append(aid)
        agent = QuestionAgent(aid, q_subset)
        agents.append(agent)

    # Ticket Agent
    ticket_agent_aid = AID(name="ticket_agent@localhost:8890")
    ticket_agent = TicketAgent(ticket_agent_aid)
    agents.append(ticket_agent)

    # Coordinator Agent
    coordinator_aid = AID(name="coordinator_agent@localhost:8891")
    coordinator_agent = CoordinatorAgent(coordinator_aid, question_agents_aids, ticket_agent_aid)
    agents.append(coordinator_agent)

    # Запуск всех агентов
    utility.start_loop(agents)
