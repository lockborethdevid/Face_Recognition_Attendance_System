import get_from_rabbitmq
import get_from_postgres
import threading
from alert_to_slack import alet2slack
from multiprocessing import Process, Manager
from collections import defaultdict
from datetime import datetime, date
import calendar
import schedule


def clear_studentID_count(dict_count, cursor, students, session_each_batchs, all_sections):
    session_alert2slack = dict()
    while True:
        datetime_now = datetime.now()
        time_format = datetime_now.strftime("%H:%M")
        float_time_now = int(time_format.split(':')[0]) + int(time_format.split(':')[1]) / 60

        # Loop to take all section_id
        for sectionID in session_each_batchs:
            # loop all session in section
            for sessionTime in session_each_batchs[sectionID][
                Global.today]:  # sessionTime contain [session_id, start_session]
                float_session_time = int(sessionTime[1].split(':')[0]) + int(sessionTime[1].split(':')[1]) / 60
                # alert to slack at the 40m of start session, check 2m for alert to slack
                if ((float_time_now > float_session_time + 0.666) and (float_time_now < float_session_time + 0.7)):
                    if (not (sectionID in session_alert2slack)) or (
                            (sectionID in session_alert2slack) and session_alert2slack[
                        sectionID] != float_session_time):
                        # session_alter2slack contain {sectionionID: float_session_time}
                        session_alert2slack[sectionID] = float_session_time
                        for studentid in all_sections[sectionID]:
                            if (not (studentid in dict_count) or (
                                    studentid in dict_count and dict_count[studentid][6] != "P")):
                                pass
                                # alet2slack(students[studentid][2],"Please make sure your face straight to board or camera")
                # check for all absents at 50m
                elif (float_time_now > float_session_time + 0.833) and (float_time_now < float_session_time + 1):
                    # list all students in section_id
                    for studentID in all_sections[sectionID]:
                        if not (studentID in dict_count):
                            cursor.execute(
                                """INSERT INTO attendances(student_id, batch_id, section_id, session_id, status, date) VALUES(%s,%s,%s,%s,%s,%s)""",
                                (studentID, students[studentID][0], students[studentID][1],
                                 sessionTime[0], "A", datetime_now))
                            connection.commit()
                            # alet2slack(students[studentID][2],"You are Absent on : " + str(datetime_now))
                        elif (studentID in dict_count) and (dict_count[studentID][6] != "P"):
                            cursor.execute(
                                """INSERT INTO attendances(student_id, batch_id, section_id, session_id, status, date) VALUES(%s,%s,%s,%s,%s,%s)""",
                                (studentID, students[studentID][0], students[studentID][1],
                                 sessionTime[0], "A", datetime_now))
                            connection.commit()
                            dict_count.pop(studentID)
                            # alet2slack(students[studentID][2], "You are Absent on : " + str(datetime_now))
                        elif (studentID in dict_count) and (dict_count[studentID][6] == "P"):
                            dict_count.pop(studentID)
                    session_each_batchs[sectionID][Global.today].remove(sessionTime)


def refresh_everyday(get_students, get_sessions, get_sections, cursor):
    get_students.clear()
    get_sessions.clear()
    get_sections.clear()
    get_students.extend(get_from_postgres.get_students(cursor))
    get_sessions.extend(get_from_postgres.get_sessions(cursor))
    get_sections.extend(get_from_postgres.get_sections(cursor))
    Global.today = calendar.day_name[date.today().weekday()]


def set_schedule_each_day(get_students, get_sessions, get_sections, cursor):
    # refresh data from database and Global.tody eavery day on 05:00 am
    schedule.every().day.at("05:00").do(refresh_everyday, get_students, get_sessions, get_sections, cursor)
    while True:
        schedule.run_pending()


# Start Program
if __name__ == '__main__':

    # Connect to postgre
    connection = get_from_postgres.get_connection()

    # Cursor bring data from postgre to our program
    cursor = get_from_postgres.get_cursor(connection=connection)

    # Get data from DB Postgre
    get_students = get_from_postgres.get_students(cursor)
    get_sessions = get_from_postgres.get_sessions(cursor)
    get_sections = get_from_postgres.get_sections(cursor)

    # Create Global Variable
    Global = Manager().Namespace()

    # Get current date
    Global.today = calendar.day_name[date.today().weekday()]

    # set schedule for fetching data from database and Global.today refresh every day
    set_schedule = threading.Thread(target=set_schedule_each_day,
                                    args=(get_students, get_sessions, get_sections, cursor,))
    set_schedule.start()

    # Detect face 5 or more than 5 so we can put present
    num_present = 5

    # Put list in dictionary --- defaultdict usage ---
    dict_count = defaultdict(list)
    students = defaultdict(list)
    all_sections = defaultdict(list)

    for student in get_students:
        # key is student_id "student_id" : ["batch_id", "section_id", "slack_id"]
        students[student[0]].extend([student[2], student[3], student[4]])

        # all_students contain "section_id": [student_id]
        all_sections[student[3]].append(student[0])

    #Find session each day
    session_each_batch = defaultdict(list)

    for section in get_sections:
        session_each_batch[section[0]] = {}
        session_each_batch[section[0]][Global.today] = []
    for session in get_sessions:
        # session_each_batch contain "section_id" : {"day" : [session_id, start_session] }
        try:
            if (Global.today == session[3]):
                session_each_batch[session[1]][session[3]].append(
                    [session[0], session[4]])  # user try-except to throught exception if no match day in it
        except:
            continue
    print(session_each_batch)
    # get student info from rabbitmq
    th1 = threading.Thread(target=get_from_rabbitmq.get_q_fun)
    th1.start()

    # Use this fun to push Absent and clear student_id in dict_count, it like to setup new count in next sesstion
    th2 = threading.Thread(target=clear_studentID_count,
                           args=(dict_count, cursor, students, session_each_batch, all_sections,))
    th2.start()

    while True:
        if (not get_from_rabbitmq.my_queue.empty()):
            q_info = get_from_rabbitmq.my_queue.get()
            try:
                student_id = int(q_info[0])
                q_datetime = datetime.strptime(q_info[1], '%Y-%m-%d %H:%M:%S.%f')
            except:
                print("student_id not int")
                continue

            q_time = q_datetime.strftime("%H:%M")
            # Convert time number to float
            q_time_float = int(q_time.split(":")[0]) + int(q_time.split(":")[1]) / 60
            next_loop = True

            # use try-except to through exception if no student_id in session_each_batch
            try:
                # check: if that ID is in the session time, it will allow to next process, if not it will go to next loop
                for session_time in session_each_batch[students[student_id][1]][
                    Global.today]:  # session_time contain [session_id, start_session]
                    # convert time to float, ex: 8:30 to 8.5
                    session_time_float = int(session_time[1].split(':')[0]) + int(session_time[1].split(':')[1]) / 60
                    # detect from start session to 50m
                    if (q_time_float >= session_time_float and q_time_float < session_time_float + 0.833):
                        next_loop = False
                        break
            except:
                continue
            if next_loop:
                continue

            # Student id should have in Database students
            if (not (student_id in dict_count)) and (student_id in students):
                for session in get_sessions:
                    if (students[student_id][1] == session[1]) and (Global.today == session[3]):
                        # In dict_count contain  {"student_id" : [ batch_id, section_id, session_id, session_name, start_time, count, status]}
                        dict_count[student_id].extend([students[student_id][0], session[1], session[0],
                                                       session[2], q_datetime, 1, "A"])
            else:
                if dict_count[student_id][6] != "P":
                    dict_count[student_id][5] += 1
                    # count to specific number and make it present
                    if dict_count[student_id][5] >= num_present:
                        dict_count[student_id][6] = "P"
                        print("Student ID : " + str(student_id) + " present")
                        cursor.execute(
                            """INSERT INTO attendances(student_id, batch_id, section_id, session_id, status, date) VALUES(%s,%s,%s,%s,%s,%s)""",
                            (int(student_id), dict_count[int(student_id)][0], dict_count[int(student_id)][1],
                             dict_count[int(student_id)][2], dict_count[int(student_id)][6], q_datetime))
                        connection.commit()
                        # alet2slack(students[student_id][2], "You are Present on : " + dict_count[student_id][4])
