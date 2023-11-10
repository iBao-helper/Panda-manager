import psutil
import time
from collections import defaultdict, deque

# Variable
program_name = 'Chromium Helper (Renderer)'
average_time = 30 # 몇초 구간을 평균 낼 것인가
interval = 0.1 #cpu 명령을 몇초마다 받아올 것인가, 0.1로 해도, 0.5초정도마다 받아옴.

pid_list = []

def get_process(process_name):
        for process in psutil.process_iter(['pid', 'name']):
            if process.info['name'] == process_name:
                pid = process.info['pid']
                if pid not in pid_list:
                    pid_list.append(pid)

def get_cpu_usage(process_name):
    try:
        cpu_usage_dict = defaultdict(lambda: deque(maxlen=average_time))
        while True:
            get_process(process_name)
            try:
                for pid in pid_list:
                    cpu_usage = psutil.Process(pid).cpu_percent(interval=0.1)
                    if cpu_usage < 3:
                        continue
                    cpu_usage_dict[pid].append(cpu_usage)
                    leng = len(cpu_usage_dict[pid])
                    average = sum(cpu_usage_dict[pid]) / leng
                    # print(f"(PID {pid}): CPU usage: {cpu_usage:.2f}% Average: {average:.2f}% | ", end='')
                    print(f"{pid}: {average:.2f}% | ", end='')
                print('\n')
                time.sleep(1)
            except psutil.NoSuchProcess:
                pid_list.remove(pid)
                continue

    except KeyboardInterrupt:
        print("Monitoring stopped.")

get_cpu_usage(program_name)
