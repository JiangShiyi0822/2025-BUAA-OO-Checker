import os
import time

from generator import Generator

TESTCASE = 10
INSTRUCTION = 1000

class Tester:
    testcase_count: int
    instruction_count: int

    ACCEPTED : int = 0
    WRONG_ANSWER : int = 1
    RUNTIME_ERROR : int = 2

    def __init__(self, testcase_count: int, instruction_count: int):
        self.testcase_count = testcase_count
        self.instruction_count = instruction_count
        if (not os.path.isdir('input')):
            os.mkdir('input')
        if (not os.path.isdir('output')):
            os.mkdir('output')
        if (not os.path.isdir('answer')):
            os.mkdir('answer')
        if (not os.path.isdir('jar')):
            os.mkdir('jar')

    def check_dependencies(self) -> bool:
        if (not os.path.isdir('input')):
            print("Error: input directory not found.")
            return False
        if (not os.path.isdir('output')):
            print("Error: output directory not found.")
            return False
        if (not os.path.isdir('answer')):
            print("Error: answer directory not found.")
            return False
        if (not os.path.isdir('jar')):
            print("Error: jar directory not found.")
            return False
        if (not os.path.isfile('std.jar')):
            print("Error: std.jar not found. (std.jar should be in the main directory)")
            return False
        return True

    def get_jar_list(self):
        return os.listdir('jar')

    def run(self):
        generator = Generator()
        jar_list = self.get_jar_list()
        if (jar_list == []):
            print("Error: no jar file found.")
            return
        for i in range(self.testcase_count):
            print(f"Testcase {i+1}:")
            generator.reset()
            generator.add_operations(self.instruction_count)
            input_file = f"test{i+1}.txt"
            answer_file = f"test_ans{i+1}.txt"

            instrs = generator.get_result()
            with open(f'input/{input_file}', 'w') as f:
                for instr in instrs:
                    f.write(instr + '\n')
            return_code = os.system(f"java -jar std.jar < input/{input_file} > answer/{answer_file}")
            if (return_code != 0):
                print(f"Error: std.jar runtime error in testcase {i+1}.")
                continue

            judge_result = {}
            for jar in jar_list:
                output_file = f"test{i+1}_{jar}.txt"
                # DO NOT USE MULTIPLE THREADS HERE
                return_code = os.system(f"java -jar jar/{jar} < input/{input_file} > output/{output_file}")
                time.sleep(0.1)
                if (return_code != 0):
                    judge_result[jar] = self.RUNTIME_ERROR
                else:
                    with open(f'output/{output_file}', 'r') as f:
                        output = f.read()
                    with open(f'answer/{answer_file}', 'r') as f:
                        answer = f.read()
                    if (output == answer):
                        judge_result[jar] = self.ACCEPTED
                    else:
                        judge_result[jar] = self.WRONG_ANSWER
            # TODO: print results

if __name__ == '__main__':
    tester = Tester(TESTCASE, INSTRUCTION)
    if (tester.check_dependencies()):
        tester.run()