import queue, threading, cv2, time


class videoCapture:
    def __init__(self, name):
        self.cap = cv2.VideoCapture(name)
        self.q = queue.Queue()
        t = threading.Thread(target=self._reader)
        t.start()

    # read frames as soon as they are available, keeping only most recent one
    def _reader(self):
        while True:
            ret, frame = self.cap.read()
            if not ret:
                break
            if not self.q.empty():
                try:
                    self.q.get()  # Take the previous frame that unprocessed out
                except queue.Empty:
                    pass
            self.q.put(frame)

    def read(self):
        self.q.queue.clear()
        time.sleep(0.1)
        return self.q.get()
