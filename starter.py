# import json
# import random
# import secrets
# from copy import copy
#
# from pade.acl.aid import AID
# from pade.acl.messages import ACLMessage
# from pade.behaviours.protocols import TimedBehaviour
# from pade.core.agent import Agent
# from pade.misc.utility import display_message, start_loop, call_later
#
# MANAGER_AID = AID("manager@185.200.178.189:59001")
# STARTER_AID = AID('starter@localhost:59000')
#
# class StarterAgent(Agent):
#     def __init__(self, aid: AID):
#         super(StarterAgent, self).__init__(aid)
#         # comp_temp = ComportTemporal(self,  15.0, self.send_message)
#         # self.behaviours.append(comp_temp)
#
#
#     def on_start(self):
#         super(StarterAgent, self).on_start()
#         display_message(self.aid.localname, 'Starter Agent started.')
#         call_later(15.0, self.send_message)
#
#     def send_message(self):
#         display_message(self.aid.name, 'message sent')
#         message = ACLMessage(ACLMessage.INFORM)
#         message.add_receiver(MANAGER_AID)
#         message.set_content(json.dumps({
#             "number_of_questions": 4,
#             "number_of_tickets": 10
#         }))
#         self.send(message)
#
#
# if __name__ == '__main__':
#     s_agent = StarterAgent(STARTER_AID)
#     start_loop([s_agent])
import pickle
# Source - https://stackoverflow.com/a
# Posted by AbdulMueed, modified by community. See post 'Timeline' for change history
# Retrieved 2025-12-07, License - CC BY-SA 3.0

import socket
import time

host = "185.200.178.189"
this_host = "155.212.171.31"
port = 59001                   # The same port as used by the server
this_port = 59000
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((host, port))



s.sendall(pickle.dumps('(inform '
          ':conversationID 4f1fce1c-d39a-11f0-a78f-525400150a7e'
          ' :sender (agent-identifier :name starter@155.212.171.31:59000 :addresses (sequence localhost:59000))'
          ' :receiver (set (agent-identifier :name manager@185.200.178.189:59001 :addresses (sequence manager@185.200.178.189:59001 ) )  )'
          ' :content "{"number_of_questions": 3, "number_of_tickets": 10}")'))

s.close()
time.sleep(1)
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((this_host, this_port))
s.listen(1)
all_d = b''
closed = False
l = None
while True:
    conn, addr = s.accept()
    with conn:
        print(f"Connected by {addr}")
        while True:
            data = conn.recv(1024)
            if data:
                all_d += data
            else:
                print("Client closed connection.")
                l = pickle.loads(all_d)
                closed = True
                break

    if closed:
        break
s.close()
for ind, line in enumerate(l):
    questions = line["questions"]
    print("-----------------------------------------------------")
    print(f"Билет #{ind + 1}")
    for q_ind, q in enumerate(questions):
          print(f"Вопрос #{q_ind + 1}: {q['question']}, тема: {q['field']}, сложность: {q['diff']}")
    print("-----------------------------------------------------")
