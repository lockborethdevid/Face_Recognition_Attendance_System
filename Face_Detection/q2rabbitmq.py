from push_to_rabbitmq import get_connection_amqp, publish_data


def from_q_to_rabbitmq(put_get):
    get_connection_rabbitmq = get_connection_amqp()
    while True:
        if not put_get.empty():
            encode = put_get.get()
            try:
                # for encode in encodes:
                publish_data(encode, get_connection_rabbitmq)
            except:
                print("Error while push encode to rabbitmq")
                get_connection_rabbitmq = get_connection_amqp()
