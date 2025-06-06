import os
import time
import traceback

from prettytable import PrettyTable

import gen
import Checker

LENGTH = 30
SERIAL = 20
def test(length, total_case, file_name_list):
    for i in range(total_case):
        print(f'testcase:{i}.')
        print('generate input...')
        gen.generate(length,i)
        time.sleep(0.02)

        allPassed = True
        table = PrettyTable(['file_name', 'state','systemRunTime','avgTaskCompleteTime','powerConsumption'])

        for file_name in file_name_list:
            print(f'running jar: {file_name}...')
            os.system(f'datainput_student_win64.exe | java -jar jar/{file_name} > output.txt')
            time.sleep(0.2)
            print("check vadility...")
            try:
                performanceInfo = Checker.check("stdin.txt", "output.txt")
            except Exception as exc:
                print(traceback.format_exc())
                print(f"{file_name} failed.")
                table.add_row([file_name, "Fail", "N/A", "N/A", "N/A"])
                with open(f"judge_result/test{i}_errorInfo_{file_name}.txt", mode='w') as f:
                    f.write("Fail.\n")
                    f.write(traceback.format_exc())
                allPassed = False
            else:
                print(f"{file_name} passed.")
                table.add_row([file_name, "Pass", format(performanceInfo[0], ".4f"), format(performanceInfo[1], ".4f"), format(performanceInfo[2], ".2f")])
        with open(f"judge_result/test{i}_table.txt", mode='w') as f:
            f.write(table.get_string())
        print(table)
        print(f'testcase {i} end.')

        if (not allPassed):
            break
    print("test end.")
    
def single_check(jar_path):
    os.system(f'datainput_student_win64.exe | java -jar {jar_path} > output.txt')
    time.sleep(0.2)
    try:
        Checker.check("stdin.txt", "output.txt")
    except Exception as exc:
        traceback.print_exc()
        exit(-1)
    print('Passed.')

file_name_list = []
for file_name in os.listdir('jar'): 
    file_name_list.append(f'{file_name}')
test(LENGTH, SERIAL, file_name_list)
# single_check("hw.jar")
