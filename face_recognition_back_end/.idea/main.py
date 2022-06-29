import get_from_rabbitmq
import get_from_postgres
import threading
from collections import defaultdict
from datetime import datetime, date
import calendar
import time

def clear_studentID_count(dict_count, cursor, today, students, session_each_batchs,all_sections):
    while True:
        time.sleep(2)
        datetime_now = datetime.now()
        time_format = datetime_now.strftime("%H:%M")
        float_time_now = int(time_format.split(':')[0]) + int(time_format.split(':')[1]) / 60
        # float_time_now = 9.40

        for sectionID in session_each_batchs:

            # loop all sesstion in section
            for sessionTime in session_each_batchs[sectionID][today]:  # sessionTime contain [session_id, sessionTime]

                float_session_time = int(sessionTime[1].split(':')[0]) + int(sessionTime[1].split(':')[1]) / 60
                # check last 10m
                if (float_time_now > float_session_time + 0.83) and (float_time_now < float_session_time + 1):

                    # list all students in section_id
                    for studentID in all_sections[sectionID]:

                        if (not studentID in dict_count) or ((studentID in dict_count) and (dict_count[studentID][6] !="P")):
                            cursor.execute("""INSERT INTO attendances(student_id, batch_id, section_id, session_id, status, date) VALUES(%s,%s,%s,%s,%s,%s)""",
                                (studentID, students[studentID][0], students[studentID][1],
                                 sessionTime[0], "A", datetime_now))
                            connection.commit()
                    session_each_batchs[sectionID][today].remove(sessionTime)
        time.sleep(1)

if __name__ == '__main__':
    # get student_id from rabbitmq
    th1 = threading.Thread(target=get_from_rabbitmq.get_q_fun)
    th1.start()
    # get_from_rabbitmq.my_queue.queue.clear()

    connection = get_from_postgres.get_connection()
    cursor = get_from_postgres.get_cursor(connection=connection)
    get_students = get_from_postgres.get_students(cursor)
    get_sessions = get_from_postgres.get_sessions(cursor)
    get_sections = get_from_postgres.get_sections(cursor)
    dict_count = defaultdict(list)
    students = defaultdict(list)
    session_each_batchs = defaultdict(list)
    all_sections = defaultdict(list)  # contain "section_id":[student_id]
    num_present = 25
    today = calendar.day_name[date.today().weekday()]
    # today = "Monday"

    for student in get_students:
        # key is student_id   "student_id" : ["batch_id", "section_id"]
        students[student[0]].extend([student[2], student[3]])
        # add student_id to all_section
        all_sections[student[3]].append(student[0])

    days_of_week = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    for batch in get_sections:
        session_each_batchs[batch[0]] = {}
        for day in days_of_week:
            session_each_batchs[batch[0]][day] = []

    for session in get_sessions:
        # "section_id" : {"day" : [[session_id, start_session], ...]}
        # user try-except to throught exception if no mathch day in it
        try:

            session_each_batchs[session[1]][session[3]].append([session[0], session[4]])
        except:
            continue

    th2 = threading.Thread(target= clear_studentID_count, args=(dict_count, cursor, today, students, session_each_batchs, all_sections,))
    th2.start()

    while True:
        if (not get_from_rabbitmq.my_queue.empty()):



            q_info = get_from_rabbitmq.my_queue.get()
            student_id = list(q_info.keys())[0]  # type str
            cursor.execute(
                """INSERT INTO test_face(id, time) VALUES(%s,%s)""", (int(student_id), q_info[student_id]))
            connection.commit()
            now = datetime.strptime(q_info[student_id], '%Y-%m-%d %H:%M:%S.%f')
            # today = calendar.day_name[now.weekday()]

            current_time = now.strftime("%H:%M")
            current_time_float = int(current_time.split(":")[0]) + int(current_time.split(":")[1]) / 60
            # current_time_float = 8.52
            next_loop = True
            # use try-except to through exception if no student_id in session_each_batchs
            try:
                # check time if that student, now is in the session time it will allow to next process if not it will go to next loop
                for session_time in session_each_batchs[students[int(student_id)][1]][today]:   # session_time contain [sesstion_id, sesstion_time]
                    # convert time to float, ex: 8:30 to 8.5
                    time_float = int(session_time[1].split(':')[0]) + int(session_time[1].split(':')[1])/60
                    if (current_time_float >= time_float and current_time_float <= time_float + 1 ):
                        next_loop = False
                        break
            except:
                continue

            if next_loop:
                if int(student_id) in dict_count:
                    dict_count.pop(int(student_id))
                continue

            if (not (int(student_id) in dict_count)) and (int(student_id) in students):
                    for data in get_sessions:
                        if (students[int(student_id)][1] == data[1]) and (today == data[3]):
                            # In dict contain  {"student_id" : [ batch_id, section_id, session_id, session_name, start_time, count, status]}
                            dict_count[int(student_id)].extend([students[int(student_id)][0], data[1], data[0],
                                                          data[2], q_info[student_id], 1,"A"])

            else:
                if dict_count[int(student_id)][6] != "P":
                    dict_count[int(student_id)][5] += 1
                    # count to specific number and make it present
                    if dict_count[int(student_id)][5] >= num_present:
                        dict_count[int(student_id)][6] = "P"
                        # insert data to attendances table
                        cursor.execute("""INSERT INTO attendances(student_id, batch_id, section_id, session_id, status, date) VALUES(%s,%s,%s,%s,%s,%s)""",
                                       (int(student_id), dict_count[int(student_id)][0], dict_count[int(student_id)][1], dict_count[int(student_id)][2], dict_count[int(student_id)][6], now))
                        connection.commit()