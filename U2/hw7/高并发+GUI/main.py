import os
import time
import traceback
import shutil
import subprocess
from prettytable import PrettyTable
from concurrent.futures import ThreadPoolExecutor, as_completed
import signal
import sys
import threading
import queue
import tkinter as tk
from tkinter import ttk

# 全局队列，用于GUI状态更新、日志输出和summary更新
status_queue = queue.Queue()
log_queue = queue.Queue()
summary_queue = queue.Queue()

def gui_print(*args):
    """将输出内容添加到日志队列中，最终在GUI中显示。"""
    message = " ".join(str(a) for a in args)
    log_queue.put(message)

# 信号处理
def signal_handler(_sig, _frame):
    gui_print("Ctrl+C detected. Exiting immediately.")
    os._exit(1)
signal.signal(signal.SIGINT, signal_handler)

import gen
import Checker

# 全局常量
LENGTH = 100
SERIAL = 500  # 测试时数字较小，实际使用时可调整
MAX_THREAD = 20
MAX_TIME_LIMIT = 120

EXE_PATH = os.path.abspath("datainput_student_win64.exe")

# 用于更新GUI状态的函数
def update_gui(test_index, jar_name, status, sys_rt="", avg_tct="", pc=""):
    status_queue.put((test_index, jar_name, status, sys_rt, avg_tct, pc))

# 修改后的主界面，同时新增了summary区域
class TestGUI:
    def __init__(self, root, total_case, jar_files):
        self.root = root
        self.root.title("HW7 Testing Status")
        self.paned = ttk.PanedWindow(root, orient='vertical')
        self.paned.pack(fill="both", expand=True)

        # 状态树区域含滚动条
        self.tree_frame = ttk.Frame(self.paned)
        self.tree = ttk.Treeview(self.tree_frame)
        self.tree["columns"] = ("Status", "SystemRunTime", "AvgTaskTime", "PowerConsumption")
        self.tree.column("#0", width=400)
        self.tree.column("Status", width=400)
        self.tree.column("SystemRunTime", width=150)
        self.tree.column("AvgTaskTime", width=150)
        self.tree.column("PowerConsumption", width=150)
        self.tree.heading("#0", text="Testcase/ Jar File")
        self.tree.heading("Status", text="Status")
        self.tree.heading("SystemRunTime", text="SystemRunTime")
        self.tree.heading("AvgTaskTime", text="AvgTaskTime")
        self.tree.heading("PowerConsumption", text="PowerConsumption")

        self.tree_vsb = ttk.Scrollbar(self.tree_frame, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=self.tree_vsb.set)
        self.tree_vsb.pack(side='right', fill='y')
        self.tree.pack(side='left', fill='both', expand=True)

        self.case_nodes = {}  # test_index -> tree item id
        self.jar_nodes = {}   # (test_index, jar_name) -> tree item id

        # 创建测试用例节点及对应jar子节点（各用例下每个jar显示状态）
        for i in range(total_case):
            case_id = self.tree.insert("", "end", text=f"Case {i}", values=("", "", "", ""), open=True)
            self.case_nodes[i] = case_id
            for jar in jar_files:
                jar_id = self.tree.insert(case_id, "end", text=jar,
                                          values=("准备生成数据中", "", "", ""))
                self.jar_nodes[(i, jar)] = jar_id
                self.tree.tag_configure("准备生成数据中", foreground="blue")
                self.tree.item(jar_id, tags=("准备生成数据中",))
        self.paned.add(self.tree_frame)

        # 新增Summary区域显示每个jar的平均性能分数和参与测试组数
        self.summary_frame = ttk.Frame(self.paned)
        self.summary_tree = ttk.Treeview(self.summary_frame)
        self.summary_tree["columns"] = ("AvgSystemRunTime", "AvgTaskTime", "AvgPowerConsumption", "GroupCount")
        self.summary_tree.column("#0", width=150)
        self.summary_tree.heading("#0", text="Jar File")
        self.summary_tree.column("AvgSystemRunTime", width=150)
        self.summary_tree.heading("AvgSystemRunTime", text="Avg SystemRunTime")
        self.summary_tree.column("AvgTaskTime", width=150)
        self.summary_tree.heading("AvgTaskTime", text="Avg TaskTime")
        self.summary_tree.column("AvgPowerConsumption", width=150)
        self.summary_tree.heading("AvgPowerConsumption", text="Avg PowerConsumption")
        self.summary_tree.column("GroupCount", width=100)
        self.summary_tree.heading("GroupCount", text="组数")
        self.summary_nodes = {}
        for jar in jar_files:
            node = self.summary_tree.insert("", "end", text=jar, 
                                              values=("0.0000", "0.0000", "0.00", "0"))
            self.summary_nodes[jar] = node
        self.summary_tree.pack(fill="both", expand=True)
        self.paned.add(self.summary_frame)

        # 日志显示区域含滚动条
        self.log_frame = ttk.Frame(self.paned)
        self.log_text = tk.Text(self.log_frame, height=30, state="disabled")
        self.log_vsb = ttk.Scrollbar(self.log_frame, orient='vertical', command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=self.log_vsb.set)
        self.log_text.pack(side="left", fill="both", expand=True)
        self.log_vsb.pack(side="right", fill="y")
        self.paned.add(self.log_frame)

        # 添加退出按钮
        self.exit_button = ttk.Button(self.root, text="退出", command=self.exit_program)
        self.exit_button.pack(pady=10)

        # 开始轮询各个队列
        self.poll_status_queue()
        self.poll_log_queue()
        self.poll_summary_queue()

    def poll_status_queue(self):
        try:
            while True:
                item = status_queue.get_nowait()
                if len(item) == 6:
                    test_index, jar_name, status, sys_rt, avg_tct, pc = item
                    self.update_status(test_index, jar_name, status, sys_rt, avg_tct, pc)
                else:
                    test_index, jar_name, status = item
                    self.update_status(test_index, jar_name, status)
        except queue.Empty:
            pass
        self.root.after(100, self.poll_status_queue)

    def update_status(self, test_index, jar_name, status, sys_rt="", avg_tct="", pc=""):
        if status.startswith("检查失败"):
            color = "red"
        elif status in ["准备生成数据中", "生成数据完成"]:
            color = "blue"
        elif status == "运行程序输出中":
            color = "orange"
        elif status == "输出成功":
            color = "pink"
        elif status == "检查中":
            color = "purple"
        elif status == "检查通过":
            color = "green"
        else:
            color = "black"
        node = self.jar_nodes.get((test_index, jar_name))
        if node:
            self.tree.item(node, values=(status, sys_rt, avg_tct, pc))
            self.tree.tag_configure(status, foreground=color)
            self.tree.item(node, tags=(status,))

    def poll_log_queue(self):
        try:
            while True:
                msg = log_queue.get_nowait()
                self.append_log(msg)
        except queue.Empty:
            pass
        self.root.after(100, self.poll_log_queue)

    def append_log(self, msg):
        self.log_text.config(state="normal")
        self.log_text.insert("end", msg + "\n")
        self.log_text.see("end")
        self.log_text.config(state="disabled")

    def poll_summary_queue(self):
        try:
            while True:
                jar_name, avg_rt, avg_tct, avg_pc, count = summary_queue.get_nowait()
                self.update_summary(jar_name, avg_rt, avg_tct, avg_pc, count)
        except queue.Empty:
            pass
        self.root.after(100, self.poll_summary_queue)

    def update_summary(self, jar_name, avg_rt, avg_tct, avg_pc, count):
        node = self.summary_nodes.get(jar_name)
        if node:
            self.summary_tree.item(node, values=(avg_rt, avg_tct, avg_pc, count))

    def exit_program(self):
        """退出程序，关闭GUI和命令行"""
        self.root.destroy()
        os._exit(1)

# 修改后的test()函数，新增了对每个jar性能数据的实时统计
def test(length, total_case, file_name_list):
    # 清理相关文件夹
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
    
    time_exceed_errors = []

    # 全局性能数据统计: {jar_file: [total_rt, total_tct, total_pc, count]}
    performance_summary = {}
    summary_lock = threading.Lock()

    def run_jar(file_name, test_index):
        update_gui(test_index, file_name, "运行程序输出中", "", "", "")
        gui_print(f'case{test_index}:运行jar: {file_name}...')
        output_file = f'out/{file_name}/output_{test_index}.txt'
        exe_proc = subprocess.Popen(
            [EXE_PATH],
            cwd=f'in/{test_index}',
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        jar_proc = subprocess.Popen(
            ['java', '-jar', f'jar/{file_name}'],
            stdin=exe_proc.stdout,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8',
            errors='replace',
        )
        exe_proc.stdout.close()
        retry_attempts = 3
        for attempt in range(retry_attempts):
            try:
                jar_output, jar_err = jar_proc.communicate(timeout=MAX_TIME_LIMIT)
                if jar_proc.returncode != 0:
                    error_type = f"jar error: {jar_err.strip()}"
                    gui_print(f"jar执行失败 (尝试 {attempt + 1}/{retry_attempts}): {error_type}")
                    if attempt + 1 == retry_attempts:
                        update_gui(test_index, file_name, f"运行失败: {error_type}", "N/A", "N/A", "N/A")
                        return [file_name, "Fail", error_type, "N/A", "N/A"]
                    time.sleep(0.5)  # 稍作等待后重试
            except subprocess.TimeoutExpired:
                error_type = "时间过长错误"
                update_gui(test_index, file_name, f"检查失败: {error_type}", "N/A", "N/A", "N/A")
                gui_print(f"运行时间超过{MAX_TIME_LIMIT}s, 输出时间过长错误")
                time_exceed_errors.append((test_index, file_name))
                return [file_name, "Fail", error_type, "N/A", "N/A"]
            except BrokenPipeError:
                error_type = "Broken Pipe Error"
                update_gui(test_index, file_name, f"Pipe运行失败: {error_type}", "N/A", "N/A", "N/A")
                gui_print(f"Broken Pipe Error occurred")
                return [file_name, "Fail", error_type, "N/A", "N/A"]
            else:
                break  # 成功获取输出，跳出重试循环
        else:
            # 如果所有尝试都失败了，这里处理
            error_type = "多次尝试后jar执行仍然失败"
            update_gui(test_index, file_name, f"运行失败: {error_type}", "N/A", "N/A", "N/A")
            return [file_name, "Fail", error_type, "N/A", "N/A"]
        with open(output_file, 'w', encoding='utf-8') as fout:
            fout.write(jar_output)
        gui_print("开始检查数据有效性...")
        update_gui(test_index, file_name, "检查中", "", "", "")
        try:
            performanceInfo = Checker.check(f"in/{test_index}/stdin.txt", output_file)
        except Exception as e:
            error_type = f"{e.__class__.__name__}: {str(e)}"
            update_gui(test_index, file_name, f"检查失败: {error_type}", "N/A", "N/A", "N/A")
            err_info = traceback.format_exc()
            gui_print(err_info)
            gui_print(f"{file_name} 检查失败。")
            with open(f"judge_result/test{test_index}_errorInfo_{file_name}.txt", mode='w') as f:
                f.write("Fail.\n")
                f.write(err_info)
            return [file_name, "Fail", error_type, "N/A", "N/A"]
        else:
            sys_rt = format(performanceInfo[0], ".4f")
            avg_tct = format(performanceInfo[1], ".4f")
            pc = format(performanceInfo[2], ".2f")
            gui_print(f"{file_name} 检查通过。")
            update_gui(test_index, file_name, "检查通过", sys_rt, avg_tct, pc)
            return [file_name, "Pass", sys_rt, avg_tct, pc]

    def run_case(i):
        gui_print(f"开始测试用例: {i}.")
        gui_print('生成输入数据...')
        os.makedirs(f'in/{i}', exist_ok=True)
        time.sleep(0.1)
        for file_name in file_name_list:
            os.makedirs(f'out/{file_name}', exist_ok=True)
        time.sleep(0.1)
        generated_data = gen.generate_hw7_data(
            total_requests_target=length,
            mutual_mode=True,
            pattern="dense",
            max_time_override=2 
        )
        # 等待数据生成完成
        time.sleep(0.2)
        try:
            with open(f"in/{i}/stdin.txt", "w", encoding="utf-8") as f:
                [f.write(line + "\n") for line in generated_data]
        except Exception as e:
            gui_print(f"Error writing input data for test case {i}: {str(e)}")
            return
        gui_print(f"测试用例 {i} 输入数据生成完毕。")

        for jar in file_name_list:
            update_gui(i, jar, "生成数据完成", "", "", "")
        time.sleep(0.2)
        allPassed = True
        table = PrettyTable(['file_name', 'state', 'systemRunTime', 'avgTaskCompleteTime', 'powerConsumption'])
        row_list = []
    
        with ThreadPoolExecutor(max_workers=len(file_name_list)) as executor:
            future_to_file = {executor.submit(run_jar, file_name, i): file_name for file_name in file_name_list}
            for future in as_completed(future_to_file):
                file_name = future_to_file[future]
                try:
                    row = future.result()
                except Exception as e:
                    gui_print(f"测试用例 {i} 执行 {file_name} 时发生异常: {str(e)}")
                    row = [file_name, "Fail", "N/A", "N/A", "N/A"]
                if row[1] == "Fail":
                    allPassed = False
                table.add_row(row)
                row_list.append(row)
                # 若检查通过则更新性能统计
                if row[1] == "Pass":
                    try:
                        sys_rt_val = float(row[2])
                        avg_tct_val = float(row[3])
                        pc_val = float(row[4])
                    except Exception:
                        continue
                    with summary_lock:
                        if file_name not in performance_summary:
                            performance_summary[file_name] = [sys_rt_val, avg_tct_val, pc_val, 1]
                        else:
                            performance_summary[file_name][0] += sys_rt_val
                            performance_summary[file_name][1] += avg_tct_val
                            performance_summary[file_name][2] += pc_val
                            performance_summary[file_name][3] += 1
                        total_rt, total_tct, total_pc, count = performance_summary[file_name]
                        avg_rt = total_rt / count
                        avg_tct = total_tct / count
                        avg_pc = total_pc / count
                    summary_queue.put((file_name, format(avg_rt, ".4f"), format(avg_tct, ".4f"), format(avg_pc, ".2f"), count))

        with open(f"judge_result/test{i}_table.txt", mode='w') as f:
            f.write(table.get_string())
        gui_print(table.get_string())
        gui_print(f"测试用例 {i} 执行完毕。")
        with open("final_table.txt", "a") as f:
            f.write(f"{i}\n")
        return (allPassed, row_list)

    overall_rows = []
    case_results = {}
    group_failed_jars = {}
    with ThreadPoolExecutor(max_workers=MAX_THREAD) as executor:
        future_to_case = {executor.submit(run_case, i): i for i in range(total_case)}
        for future in as_completed(future_to_case):
            i = future_to_case[future]
            try:
                passed, rows = future.result()
                overall_rows.extend(rows)
                case_results[i] = passed
                failed_jars = [row[0] for row in rows if row[1] == "Fail" and row[2] != "时间过长错误"]
                if failed_jars:
                    group_failed_jars[i] = failed_jars
            except Exception as e:
                gui_print(f"测试用例 {i} 发生未处理异常: {str(e)}")
                case_results[i] = False
                group_failed_jars[i] = ["Unhandled exception"]

    overall = {}
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
    gui_print("Final averaged results:")
    gui_print(output_str)
    gui_print("测试全部结束。")

    finished = set()
    if os.path.exists("final_table.txt"):
        with open("final_table.txt", "r") as f:
            for line in f:
                line = line.strip()
                if line.isdigit():
                    finished.add(int(line))
    expected = set(range(total_case))
    missing = sorted(expected - finished)
    if missing:
        gui_print("未成功运行的测试序号:", ", ".join(str(n) for n in missing))
    else:
        gui_print("所有测试序号均已完成。")

    if group_failed_jars:
        gui_print("以下测试组存在jar check失败:")
        for group in sorted(group_failed_jars.keys()):
            jars = group_failed_jars[group]
            gui_print(f"组 {group}: {', '.join(jars)} - 该组测试结果为失败")
    else:
        gui_print(f"所有在时间限制{MAX_TIME_LIMIT}s内的测试组的jar均通过检查。")

    if time_exceed_errors:
        gui_print(f"以下测试组存在运行时间超过{MAX_TIME_LIMIT}s的错误:")
        error_dict = {}
        for test_index, file_name in time_exceed_errors:
            error_dict.setdefault(test_index, []).append(file_name)
        for test_index in sorted(error_dict):
            files = ", ".join(sorted(error_dict[test_index]))
            gui_print(f"组 {test_index}: 文件: {files}  - 该组测试结果为超时")
    else:
        gui_print(f"所有测试组均未出现运行时间超过{MAX_TIME_LIMIT}s的错误。")

    if group_failed_jars or missing or time_exceed_errors:
        gui_print("总体测试结果：失败")
    else:
        gui_print("总体测试结果：通过")
    
    with open("final_table.txt", mode='w') as f:
        f.write(output_str)

def start_test():
    file_name_list = [f for f in os.listdir('jar')]
    threading.Thread(target=test, args=(LENGTH, SERIAL, file_name_list), daemon=True).start()

if __name__ == '__main__':
    root = tk.Tk()
    if not os.path.exists("jar"):
        gui_print("jar文件夹找不到！")
        sys.exit(1)
    jar_files = [f for f in os.listdir('jar')]
    gui = TestGUI(root, SERIAL, jar_files)
    root.after(500, start_test)
    root.mainloop()
