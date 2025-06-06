import os
import time
import traceback
import shutil
import subprocess
from prettytable import PrettyTable
from concurrent.futures import ThreadPoolExecutor, as_completed
import signal
import sys

def signal_handler(sig, frame):
    print("Ctrl+C detected. Exiting immediately.")
    os._exit(1)
signal.signal(signal.SIGINT, signal_handler)

import gen
import Checker

LENGTH = 100
SERIAL = 100
MAX_THREAD = 20

def test(length, total_case, file_name_list):
    # Clean up folders once.
    for folder in ['in', 'out', 'judge_result']:
        if not os.path.exists(folder):
            os.makedirs(folder)
        if os.path.isdir(folder):
            for item in os.listdir(folder):
                item_path = os.path.join(folder, item)
                if os.path.isfile(item_path) or os.path.islink(item_path):
                    os.remove(item_path)
                elif os.path.isdir(item_path):
                    shutil.rmtree(item_path)
    if os.path.exists("final_table.txt"):
        os.remove("final_table.txt")
    def run_jar(file_name, test_index):
        print(f'running jar: {file_name}...')
        os.makedirs(f'out/{file_name}', exist_ok=True)
        time.sleep(0.01)
        output_file = f'out/{file_name}/output_{test_index}.txt'
        exe_path = os.path.abspath("datainput_student_win64.exe")
        exe_proc = subprocess.Popen(
            ['cmd', '/c', exe_path],
            cwd=f'in/{test_index}',
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        jar_proc = subprocess.Popen(
            ['java', '-jar', f'jar/{file_name}'],
            stdin=exe_proc.stdout,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        exe_proc.stdout.close()
        jar_output, _ = jar_proc.communicate()
        exe_proc.wait()
        if exe_proc.returncode != 0:
            exe_error_message = exe_proc.stderr.read().decode()
            raise Exception(f"datainput_student_win64.exe failed: {exe_error_message}")
        with open(output_file, 'w', encoding='utf-8') as fout:
            fout.write(jar_output)
        print("check validity...")
        try:
            performanceInfo = Checker.check(f"in/{test_index}/stdin.txt", output_file)
        except Exception:
            err_info = traceback.format_exc()
            print(err_info)
            print(f"{file_name} failed.")
            with open(f"judge_result/test{test_index}_errorInfo_{file_name}.txt", mode='w') as f:
                f.write("Fail.\n")
                f.write(err_info)
            return [file_name, "Fail", "N/A", "N/A", "N/A"]
        else:
            print(f"{file_name} passed.")
            return [file_name, "Pass", format(performanceInfo[0], ".4f"),
                    format(performanceInfo[1], ".4f"),
                    format(performanceInfo[2], ".2f")]

    def run_case(i):
        print(f'testcase: {i}.')
        print('generate input...')
        os.makedirs(f'in/{i}', exist_ok=True)
        time.sleep(0.01)
        generated_data = gen.generate_hw7_data(
            total_requests_target=length,
            mutual_mode=False,
            pattern="random",
            max_time_override=50
        )
        with open(f"in/{i}/stdin.txt", "w", encoding="utf-8") as f:
            [f.write(line + "\n") for line in generated_data]
        print('input generated.')
        time.sleep(0.2)

        allPassed = True
        table = PrettyTable(['file_name', 'state', 'systemRunTime', 'avgTaskCompleteTime', 'powerConsumption'])
        row_list = []
        with ThreadPoolExecutor(max_workers=len(file_name_list)) as executor:
            future_to_file = {executor.submit(run_jar, file_name, i): file_name for file_name in file_name_list}
            for future in as_completed(future_to_file):
                try:
                    row = future.result()
                except Exception as e:
                    file_name = future_to_file[future]
                    print(f"Unhandled exception for {file_name}: {str(e)}")
                    row = [file_name, "Fail", "N/A", "N/A", "N/A"]
                if row[1] == "Fail":
                    allPassed = False
                table.add_row(row)
                row_list.append(row)

        with open(f"judge_result/test{i}_table.txt", mode='w') as f:
            f.write(table.get_string())
        print(table)
        print(f'testcase {i} end.')
        with open("final_table.txt", "a") as f:
            f.write(f"{i}\n")
        return (allPassed, row_list)

    overall_rows = []
    case_results = {}
    with ThreadPoolExecutor(max_workers=MAX_THREAD) as executor:
        future_to_case = {executor.submit(run_case, i): i for i in range(total_case)}
        for future in as_completed(future_to_case):
            i = future_to_case[future]
            try:
                passed, rows = future.result()
                overall_rows.extend(rows)
                case_results[i] = passed
            except Exception as e:
                print(f"Unhandled exception for testcase {i}: {str(e)}")
                case_results[i] = False

    # Compute final averages for each file (only Pass cases)
    overall = {}  # {file_name: [total_run_time, total_task_time, total_power, count]}
    for row in overall_rows:
        file_name, state = row[0], row[1]
        if state == "Pass":
            try:
                rt = float(row[2])
                tct = float(row[3])
                pc = float(row[4])
            except Exception:
                continue
            if file_name not in overall:
                overall[file_name] = [rt, tct, pc, 1]
            else:
                overall[file_name][0] += rt
                overall[file_name][1] += tct
                overall[file_name][2] += pc
                overall[file_name][3] += 1

    final_table = PrettyTable(['file_name', 'avg_systemRunTime', 'avg_avgTaskCompleteTime', 'avg_powerConsumption'])
    for file_name, (total_rt, total_tct, total_pc, count) in overall.items():
        avg_rt = format(total_rt / count, ".4f")
        avg_tct = format(total_tct / count, ".4f")
        avg_pc = format(total_pc / count, ".2f")
        final_table.add_row([file_name, avg_rt, avg_tct, avg_pc])

    output_str = final_table.get_string()
    print("Final averaged results:")
    print(output_str)
    print("test end.")

    # 先读取 final_table.txt 中记录的已完成的测试序号
    finished = set()
    if os.path.exists("final_table.txt"):
        with open("final_table.txt", "r") as f:
            for line in f:
                line = line.strip()
                if line.isdigit():
                    finished.add(int(line))

    # 计算应完成的序号集合（假设完成序号从 0 到 total_case-1）
    expected = set(range(total_case))
    missing = sorted(expected - finished)
    if missing:
        print("缺少的测试序号:", ", ".join(str(n) for n in missing))
    else:
        print("所有测试序号均已完成。")

    # 将最终平均结果写入 final_table.txt
    with open("final_table.txt", mode='w') as f:
        f.write(output_str)

file_name_list = [f for f in os.listdir('jar')]
test(LENGTH, SERIAL, file_name_list)
