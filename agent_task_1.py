# -*- coding: utf-8 -*-
from pade.misc.utility import display_message, start_loop
from pade.core.agent import Agent
from pade.acl.aid import AID
from pade.acl.messages import ACLMessage

class QuestionAgent(Agent):
    def __init__(self, aid, questions):
        super(QuestionAgent, self).__init__(aid=aid)
        # questions - список словарей {'id':..., 'section':..., 'difficulty': ...}
        self.questions = questions

    def react(self, message):
        if message.performative == ACLMessage.REQUEST:
            content = message.content
            # Ожидаемый запрос с фильтром по уже выбранным разделам
            # content = список разделов, которые уже выбраны
            used_sections = content.split(',') if content else []
            filtered = [q for q in self.questions if q['section'] not in used_sections]
            # Отправляем назад вопросы в формате строка: id|section|difficulty
            response = '\n'.join(f"{q['id']}|{q['section']}|{q['difficulty']}" for q in filtered)
            reply = message.create_reply()
            reply.set_performative(ACLMessage.INFORM)
            reply.content = response
            self.send(reply)
            display_message(self.aid.localname, f"Sent {len(filtered)} questions excluding sections {used_sections}")

class TicketAgent(Agent):
    def __init__(self, aid, question_agent_aid, ticket_size, target_difficulty_sum, ticket_count):
        super(TicketAgent, self).__init__(aid=aid)
        self.question_agent_aid = question_agent_aid
        self.ticket_size = ticket_size
        self.target_difficulty_sum = target_difficulty_sum
        self.ticket_count = ticket_count
        self.tickets = []
        self.current_ticket = []
        self.used_sections = set()
        self.pending_ticket_idx = 0

    def on_start(self):
        display_message(self.aid.localname, "Starting ticket formation")
        self.request_questions()

    def request_questions(self):
        # Запрос вопросов, исключая уже выбранные разделы (для текущего билета)
        msg = ACLMessage(ACLMessage.REQUEST)
        msg.add_receiver(self.question_agent_aid)
        # Передаем строки через запятую
        msg.content = ','.join(self.used_sections)
        self.send(msg)

    def react(self, message):
        if message.performative == ACLMessage.INFORM and message.sender == self.question_agent_aid:
            content = message.content
            questions_raw = content.strip().split('\n') if content else []
            questions = []
            for line in questions_raw:
                parts = line.split('|')
                if len(parts) == 3:
                    qid, section, diff_str = parts
                    questions.append({'id': qid, 'section': section, 'difficulty': int(diff_str)})

            # Выбор вопросов для формирования билета
            self.try_form_ticket(questions)

    def try_form_ticket(self, available_questions):
        # Жадный обход с поиском билетов из уникальных разделов и суммой сложности ~= target_difficulty_sum
        # Простая жадная реализация: перебираем и берем первые подходящие вопросы
        from itertools import combinations

        n = self.ticket_size
        target = self.target_difficulty_sum
        suitable_tickets = []

        # Перебор комбинаций размера n
        for combo in combinations(available_questions, n):
            sections = {q['section'] for q in combo}
            if len(sections) == n:  # все вопросы из разных разделов
                diff_sum = sum(q['difficulty'] for q in combo)
                if abs(diff_sum - target) <= 1:  # допускаем небольшой отклон
                    suitable_tickets.append((combo, diff_sum))
        if not suitable_tickets:
            display_message(self.aid.localname, f"Cannot form ticket #{self.pending_ticket_idx+1} matching criteria!")
            # Отправить сообщение менеджеру?
            # Можно остановить или обработать ошибку - для примера просто вывести
            return

        # Выбираем первый подходящий билет
        chosen_ticket, chosen_sum = suitable_tickets[0]
        ticket_repr = [(q['id'], q['section'], q['difficulty']) for q in chosen_ticket]
        display_message(self.aid.localname, f"Formed ticket #{self.pending_ticket_idx+1} with difficulty sum {chosen_sum}: {ticket_repr}")
        self.tickets.append(chosen_ticket)

        # Подготовка к следующему билету
        self.pending_ticket_idx += 1
        self.used_sections.clear()  # можно, но не обязательно, зависит от критериев
        if self.pending_ticket_idx < self.ticket_count:
            self.request_questions()
        else:
            display_message(self.aid.localname, f"All {self.ticket_count} tickets formed successfully")
            # Здесь можно завершить работу агента, отправить отчет менеджеру

class ManagerAgent(Agent):
    def __init__(self, aid):
        super(ManagerAgent, self).__init__(aid=aid)

    def on_start(self):
        # Создаем агентов и задаём вопросы
        questions = [
            {'id': 'Q1', 'section': 'Math', 'difficulty': 3},
            {'id': 'Q2', 'section': 'Physics', 'difficulty': 4},
            {'id': 'Q3', 'section': 'Chemistry', 'difficulty': 5},
            {'id': 'Q4', 'section': 'Biology', 'difficulty': 2},
            {'id': 'Q5', 'section': 'Math', 'difficulty': 4},
            {'id': 'Q6', 'section': 'Physics', 'difficulty': 3},
            {'id': 'Q7', 'section': 'Chemistry', 'difficulty': 2},
            {'id': 'Q8', 'section': 'Biology', 'difficulty': 4},
            # Добавьте больше вопросов по необходимости
        ]

        self.question_agent = QuestionAgent(AID(name='question_agent@localhost:{}'.format(self.aid.name.split('@')[1])), questions)
        self.ticket_agent = TicketAgent(AID(name='ticket_agent@localhost:{}'.format(self.aid.name.split('@')[1])),
                                        self.question_agent.aid,
                                        ticket_size=4,
                                        target_difficulty_sum=14,
                                        ticket_count=2)

        self.add_agent(self.question_agent)
        self.add_agent(self.ticket_agent)
        self.ticket_agent.on_start()

if __name__ == '__main__':
    from pade.misc.utility import start_loop
    manager = ManagerAgent(AID(name='manager@localhost:{}'.format(9200)))
    start_loop([manager])
