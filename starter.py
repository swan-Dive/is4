
import pickle


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
all_d = 0
n_questions = 0
for ind, line in enumerate(l):
    questions = line["questions"]
    print("-----------------------------------------------------")
    print(f"Билет #{ind + 1}")
    mid_diff = 0
    for q_ind, q in enumerate(questions):
        print(f"Вопрос #{q_ind + 1}: {q['question']}, тема: {q['field']}, сложность: {q['diff']}")
        mid_diff += int(q['diff'])
    print(f'Средняя сложность: {mid_diff / len(questions)}')
    n_questions += len(questions)
    all_d += mid_diff
    print("-----------------------------------------------------")

print(f'Общая средняя сложность: {all_d / n_questions}')
