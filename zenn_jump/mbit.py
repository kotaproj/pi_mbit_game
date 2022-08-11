from bluepy.btle import DefaultDelegate, Peripheral,ADDR_TYPE_RANDOM
from queue import Queue
import threading
import time
import datetime

MAC_ADDRESSs = [
    'e8:26:d5:f4:54:28',
]

#ACCELEROMETER SERVICE/CHARACTERISTICS UUID
ACC_SERVICE_UUID = 'E95D0753251D470AA062FA1922DFA9A8'
ACC_CHARACTERISTICS_UUID = 'E95DCA4B251D470AA062FA1922DFA9A8'

#加速度センサーの動作判定しきい値
JUMP_TH_MIN = 1500 #ジャンプ最小値
JUMP_TH_MAX = 3000 #ジャンプ最大値


class Mbit(threading.Thread):
    """
    マイクロビット管理
    """

    def __init__(self, macadr, snd_que=None, s_min=8, s_max=20):
        threading.Thread.__init__(self)
        self.stop_event = threading.Event()
        self.setDaemon(True)

        self._macadr = macadr
        self._snd_que = snd_que
        self._peripheral = None
        self._s_min = s_min
        self._s_max = s_max
        return

    def stop(self):
        self.stop_event.set()
        if self._peripheral is not None:
            self._peripheral.disconnect()
        return

    def run(self):

        def is_running(strength):
             return True if strength > RUN_TH else False

        def cal_strength(x0, y0, x1, y1, x):
            return y0 + (y1 - y0) * (x - x0) // (x1 - x0)

        def is_jumping(strength):
            if strength > JUMP_TH_MAX:
                return True, self._s_max
            elif strength > JUMP_TH_MIN:
                return True, cal_strength(JUMP_TH_MIN, self._s_min, JUMP_TH_MAX, self._s_max, strength)
            return False, None

        def service_mb():
            # 接続設定
            peripheral = Peripheral(self._macadr, ADDR_TYPE_RANDOM)
            acc_service = peripheral.getServiceByUUID(ACC_SERVICE_UUID)
            acc_characteristic = peripheral.getCharacteristics(uuid=ACC_CHARACTERISTICS_UUID)

            while True:
                # 値の読み取り
                acc_read_data = acc_characteristic[0].read()

                # 加速度センサー
                x = int.from_bytes(acc_read_data[0:2], byteorder='little', signed=True)
                y = int.from_bytes(acc_read_data[2:4], byteorder='little', signed=True)
                z = int.from_bytes(acc_read_data[4:6], byteorder='little', signed=True)
                s = (x**2 + y**2 + z**2)**0.5

                ret, s_conv = is_jumping(s)
                if ret:
                    self._send_msg(self._macadr, "jump", s_conv)

        while True:
            try:
                service_mb()
            except:
                print("error : except")
                time.sleep(3)
        return


    def _send_msg(self, name, action, strength=10):
        if self._snd_que is None:
            return
        print(f"action: {action}, strength: {strength}")
        self._snd_que.put({"type": "mbit", "name": name, "action": action, "strength": int(strength)})
        return


def main():
    q = Queue()

    for ma in MAC_ADDRESSs:
        mbit_th = Mbit(ma, q)
        mbit_th.start()

    time.sleep(60)
    mbit_th.stop()

    while True:
        if q.empty():
            print("!!! q.empty !!!")
            break
        print(q.get())
    return


if __name__ == "__main__":
    main()
