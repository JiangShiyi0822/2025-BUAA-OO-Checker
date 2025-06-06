import os
import time
import sys # For flushing output

from generator import Generator

TESTNUM = 10         # 测试组数
INSTR = 1000        # 每组测试的指令数

class Tester:
    testcase_count: int
    instruction_count: int

    # Define result strings for clarity
    ACCEPTED_STR = "Accepted"
    WRONG_ANSWER_STR = "Wrong Answer"
    RUNTIME_ERROR_STR = "Runtime Error"
    UNKNOWN_ERROR_STR = "Unknown Error" # For unexpected OS return codes

    # Map return codes to strings
    RESULT_MAP = {
        0: ACCEPTED_STR,
        1: WRONG_ANSWER_STR,
        2: RUNTIME_ERROR_STR
    }

    def __init__(self, testcase_count: int, instruction_count: int):
        self.testcase_count = testcase_count
        self.instruction_count = instruction_count
        # Create directories if they don't exist
        os.makedirs('input', exist_ok=True)
        os.makedirs('output', exist_ok=True)
        os.makedirs('answer', exist_ok=True)
        os.makedirs('jar', exist_ok=True)


    def check_dependencies(self) -> bool:
        # Directories are created in __init__, so just check for std.jar
        if not os.path.isfile('std.jar'):
            print("Error: std.jar not found. (std.jar should be in the main directory)")
            return False
        # Check if jar directory is empty
        if not self.get_jar_list():
             print("Warning: 'jar' directory is empty. No student jars to test.")
             # Allow execution to proceed, maybe only standard is needed
        return True

    def get_jar_list(self):
        if not os.path.isdir('jar'):
            return []
        # Filter out non-jar files if any
        return [f for f in os.listdir('jar') if f.lower().endswith('.jar')]

    def run(self):
        if not self.check_dependencies():
            return

        generator = Generator()
        jar_list = self.get_jar_list()
        results_summary = {jar: {self.ACCEPTED_STR: 0, self.WRONG_ANSWER_STR: 0, self.RUNTIME_ERROR_STR: 0, self.UNKNOWN_ERROR_STR: 0} for jar in jar_list}


        print(f"Starting tests for {len(jar_list)} jar file(s)...")

        for i in range(self.testcase_count):
            test_num = i + 1
            print(f"\n--- Testcase {test_num}/{self.testcase_count} ---")
            sys.stdout.flush() # Ensure header prints immediately

            generator.reset()
            # Consider adding a small number of initial people/relations?
            # generator.add_operations(10) # Example pre-population
            generator.add_operations(self.instruction_count)

            input_filename = f"test{test_num}.txt"
            answer_filename = f"test_ans{test_num}.txt"
            input_filepath = os.path.join('input', input_filename)
            answer_filepath = os.path.join('answer', answer_filename)

            # Generate input file
            instrs = generator.get_result()
            try:
                with open(input_filepath, 'w') as f:
                    for instr in instrs:
                        f.write(instr + '\n')
            except IOError as e:
                print(f"Error writing input file {input_filepath}: {e}")
                continue # Skip to next test case

            # Generate standard answer
            print(f"  Generating standard answer for {input_filename}...")
            sys.stdout.flush()
            std_command = f"java -jar std.jar < \"{input_filepath}\" > \"{answer_filepath}\""
            # print(f"  Running: {std_command}") # Debug command
            std_return_code = os.system(std_command)

            if std_return_code != 0:
                print(f"  Error: std.jar runtime error (code {std_return_code}) on {input_filename}. Skipping comparison for this case.")
                # Clean up potentially partial answer file?
                if os.path.exists(answer_filepath):
                     try:
                         os.remove(answer_filepath)
                     except OSError:
                         pass
                continue # Skip comparison for this test case

            print(f"  Standard answer generated: {answer_filename}")
            sys.stdout.flush()

            # Test each student jar
            if not jar_list:
                print("  No student jars found in 'jar' directory to test.")
                continue

            testcase_results = {}
            for jar_filename in jar_list:
                output_filename = f"test{test_num}_{jar_filename}.txt"
                output_filepath = os.path.join('output', output_filename)
                jar_filepath = os.path.join('jar', jar_filename)

                print(f"  Testing {jar_filename}...")
                sys.stdout.flush()

                # Run student jar
                run_command = f"java -jar \"{jar_filepath}\" < \"{input_filepath}\" > \"{output_filepath}\""
                # print(f"    Running: {run_command}") # Debug command
                start_time = time.time()
                return_code = os.system(run_command)
                end_time = time.time()
                exec_time = end_time - start_time
                print(f"    Finished in {exec_time:.2f}s (Return Code: {return_code})")
                sys.stdout.flush()


                # Judge the result
                result_code = self.UNKNOWN_ERROR_STR # Default to unknown
                if return_code != 0:
                    result_code = self.RUNTIME_ERROR_STR
                    print(f"    Result: {result_code}")
                    sys.stdout.flush()
                else:
                    # Compare output with standard answer
                    try:
                        with open(output_filepath, 'r') as f_out, open(answer_filepath, 'r') as f_ans:
                            output_content = f_out.read()
                            answer_content = f_ans.read()
                        if output_content == answer_content:
                            result_code = self.ACCEPTED_STR
                            print(f"    Result: {result_code}")
                            sys.stdout.flush()
                            # Optional: delete correct output file to save space
                            # os.remove(output_filepath)
                        else:
                            result_code = self.WRONG_ANSWER_STR
                            print(f"    Result: {result_code} (Output differs from {answer_filename})")
                            sys.stdout.flush()
                            # Consider adding diff command here if needed
                            # os.system(f"diff \"{answer_filepath}\" \"{output_filepath}\"")

                    except IOError as e:
                        print(f"    Error comparing files for {jar_filename}: {e}")
                        result_code = self.UNKNOWN_ERROR_STR # Error during comparison

                testcase_results[jar_filename] = result_code
                results_summary[jar_filename][result_code] += 1


            # Print summary for the testcase
            print(f"  --- Testcase {test_num} Summary ---")
            for jar, result in testcase_results.items():
                 print(f"    {jar}: {result}")
            print("  --------------------------")
            sys.stdout.flush()

        # Print final summary
        print("\n===== Final Results Summary =====")
        for jar, counts in results_summary.items():
            print(f"  --- {jar} ---")
            total = sum(counts.values())
            print(f"    Total Cases: {total}")
            for result_type, count in counts.items():
                 if count > 0 : # Only print categories with results
                     print(f"      {result_type}: {count}")
            print(f"  -------------------")
        print("===============================")


if __name__ == '__main__':
    # Example usage: Run 10 testcases with 1000 instructions each
    num_testcases = TESTNUM
    num_instructions = INSTR

    # Allow overriding from command line arguments if needed
    if len(sys.argv) == 3:
        try:
            num_testcases = int(sys.argv[1])
            num_instructions = int(sys.argv[2])
            print(f"Using command line arguments: {num_testcases} testcases, {num_instructions} instructions.")
        except ValueError:
            print("Invalid command line arguments. Using defaults.")
    elif len(sys.argv) != 1:
        print("Usage: python main.py [num_testcases num_instructions]")
        print("Using defaults.")


    tester = Tester(testcase_count=num_testcases, instruction_count=num_instructions)
    tester.run()