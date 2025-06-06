import os
import time
import sys # Added for flushing output

# Assuming generator.py is in the same directory or Python path
try:
    from generator import Generator
except ImportError:
    print("Error: generator.py not found or contains import errors.")
    sys.exit(1)

TESTCASE = 100
INSTRUCTION = 3000 # Default instructions per testcase

class Tester:
    testcase_count: int
    instruction_count: int

    ACCEPTED : int = 0
    WRONG_ANSWER : int = 1
    RUNTIME_ERROR : int = 2

    # Map codes to human-readable strings
    STATUS_MAP = {
        ACCEPTED: "Accepted",
        WRONG_ANSWER: "Wrong Answer",
        RUNTIME_ERROR: "Runtime Error"
    }

    def __init__(self, testcase_count: int, instruction_count: int):
        self.testcase_count = testcase_count
        self.instruction_count = instruction_count
        # Create directories if they don't exist
        for dir_name in ['input', 'output', 'answer', 'jar']:
             if not os.path.isdir(dir_name):
                try:
                    os.mkdir(dir_name)
                    print(f"Created directory: {dir_name}")
                except OSError as e:
                    print(f"Error creating directory {dir_name}: {e}", file=sys.stderr)
                    # Exit if essential directories cannot be created
                    if dir_name in ['input', 'output', 'answer']:
                        sys.exit(1)

    def check_dependencies(self) -> bool:
        """Checks for required directories and the standard JAR file."""
        all_ok = True
        if not os.path.isdir('input'):
            print("Error: input directory not found.", file=sys.stderr)
            all_ok = False
        if not os.path.isdir('output'):
            print("Error: output directory not found.", file=sys.stderr)
            all_ok = False
        if not os.path.isdir('answer'):
            print("Error: answer directory not found.", file=sys.stderr)
            all_ok = False
        if not os.path.isdir('jar'):
            print("Error: jar directory not found.", file=sys.stderr)
            all_ok = False
        if not os.path.isfile('std.jar'):
            print("Error: std.jar not found. (std.jar should be in the main directory)", file=sys.stderr)
            all_ok = False
        return all_ok

    def get_jar_list(self):
        """Gets a list of .jar files from the 'jar' directory."""
        if not os.path.isdir('jar'):
            return []
        try:
            return [f for f in os.listdir('jar') if f.lower().endswith('.jar')]
        except OSError as e:
            print(f"Error reading 'jar' directory: {e}", file=sys.stderr)
            return []

    def run(self):
        """Runs the testing process: generate inputs, run std.jar, run test jars, compare."""
        if not self.check_dependencies():
             print("Dependency check failed. Exiting.", file=sys.stderr)
             return # Don't run if dependencies are missing

        try:
             generator = Generator()
        except NameError: # Handle case where Generator class isn't defined due to import error
             print("Error: Generator class not available. Check generator.py.", file=sys.stderr)
             return

        jar_list = self.get_jar_list()
        if not jar_list:
            print("Error: No .jar files found in the 'jar' directory.", file=sys.stderr)
            return

        # Initialize overall results tracking
        overall_results = {jar: {"AC": 0, "WA": 0, "RE": 0, "TotalTime": 0.0} for jar in jar_list}
        total_std_re = 0 # Track how many times std.jar failed

        print(f"Starting tests for {len(jar_list)} JAR file(s)...")

        for i in range(self.testcase_count):
            test_num = i + 1
            print(f"\n--- Testcase {test_num}/{self.testcase_count} ---")
            sys.stdout.flush() # Ensure prompt output before potentially long operations

            # Generate input
            generator.reset()
            try:
                 generator.add_operations(self.instruction_count)
                 instrs = generator.get_result()
            except Exception as e:
                 print(f"  Error during test case generation: {e}", file=sys.stderr)
                 print("  Skipping this test case.")
                 continue # Skip to next test case

            input_file_name = f"test{test_num}.txt"
            answer_file_name = f"test_ans{test_num}.txt"
            input_file_path = os.path.join('input', input_file_name)
            answer_file_path = os.path.join('answer', answer_file_name)

            try:
                with open(input_file_path, 'w') as f:
                    for instr in instrs:
                        f.write(instr + '\n')
                # print(f"  Input file generated: {input_file_path}") # Optional verbose output
            except IOError as e:
                print(f"  Error writing input file {input_file_path}: {e}", file=sys.stderr)
                continue # Skip to next test case

            # Run std.jar to generate answer
            print(f"  Running std.jar to generate answer...")
            sys.stdout.flush()
            std_command = f"java -jar std.jar < \"{input_file_path}\" > \"{answer_file_path}\""
            std_start_time = time.time()
            return_code = os.system(std_command)
            std_end_time = time.time()
            print(f"  std.jar finished in {std_end_time - std_start_time:.3f}s (Exit Code: {return_code})")

            if return_code != 0:
                print(f"  Error: std.jar runtime error (exit code {return_code}) on testcase {test_num}.", file=sys.stderr)
                total_std_re += 1
                # Optionally remove potentially incomplete answer file
                if os.path.exists(answer_file_path):
                    try: os.remove(answer_file_path)
                    except OSError: pass
                continue # Skip to next test case if standard fails

            # Read the generated answer
            try:
                with open(answer_file_path, 'r') as f:
                    answer = f.read()
            except IOError as e:
                print(f"  Error reading answer file {answer_file_path}: {e}", file=sys.stderr)
                continue # Skip to next test case

            # Run each test jar
            judge_result_current_test = {}
            for jar in jar_list:
                output_file_name = f"test{test_num}_{jar}.txt"
                output_file_path = os.path.join('output', output_file_name)
                jar_file_path = os.path.join('jar', jar)
                print(f"  Running {jar}...")
                sys.stdout.flush()

                run_command = f"java -jar \"{jar_file_path}\" < \"{input_file_path}\" > \"{output_file_path}\""
                start_time = time.time()
                return_code = os.system(run_command)
                end_time = time.time()
                exec_time = end_time - start_time
                overall_results[jar]["TotalTime"] += exec_time
                print(f"    Finished in {exec_time:.3f}s (Exit Code: {return_code})")

                # Slight pause might be unnecessary unless observing file system race conditions
                # time.sleep(0.05) # Reduced pause

                result_code = -1 # Default to unknown
                if return_code != 0:
                    print(f"    Result: Runtime Error (Exit Code {return_code})")
                    result_code = self.RUNTIME_ERROR
                    overall_results[jar]["RE"] += 1
                    # Optionally remove incomplete output file
                    if os.path.exists(output_file_path):
                         try: os.remove(output_file_path)
                         except OSError: pass
                else:
                    # Compare output with answer
                    try:
                        with open(output_file_path, 'r') as f:
                            output = f.read()
                        # Normalize line endings and strip trailing whitespace for comparison
                        norm_output = output.replace('\r\n', '\n').rstrip()
                        norm_answer = answer.replace('\r\n', '\n').rstrip()

                        if norm_output == norm_answer:
                            print(f"    Result: Accepted")
                            result_code = self.ACCEPTED
                            overall_results[jar]["AC"] += 1
                        else:
                            print(f"    Result: Wrong Answer")
                            # Optional: print diff or first differing line
                            # print(f"      Output:\n{norm_output[:200]}{'...' if len(norm_output)>200 else ''}") # Show snippet
                            # print(f"      Answer:\n{norm_answer[:200]}{'...' if len(norm_answer)>200 else ''}")
                            result_code = self.WRONG_ANSWER
                            overall_results[jar]["WA"] += 1
                    except IOError as e:
                         print(f"    Error reading output file {output_file_path}: {e}", file=sys.stderr)
                         print(f"    Result: Runtime Error (File I/O)")
                         result_code = self.RUNTIME_ERROR # Treat read error as RE
                         overall_results[jar]["RE"] += 1

                judge_result_current_test[jar] = result_code

            # --- Print results table for the current testcase ---
            # print(f"--- Results for Testcase {test_num} ---")
            # header = f"{'JAR File':<20} | {'Status':<15} | {'Time (s)':<10}"
            # print(header)
            # print("-" * len(header))
            # for jar, result_code in judge_result_current_test.items():
            #     status_str = self.STATUS_MAP.get(result_code, "Unknown")
            #     time_str = f"{overall_results[jar]['TotalTime'] / test_num:.3f}" # Avg time so far? Show current time?
            #     # Let's just show status for the current test case result line
            #     print(f"{jar:<20} | {status_str:<15}") # Time shown above already
            # print("-" * 30) # Separator
            sys.stdout.flush()

        # --- Print overall summary ---
        print("\n" + "=" * 40)
        print(" " * 12 + "Overall Summary")
        print("=" * 40)
        if total_std_re > 0:
             print(f"Warning: std.jar encountered runtime errors in {total_std_re} testcase(s).")
        header = f"{'JAR File':<25} | {'AC':>4} | {'WA':>4} | {'RE':>4} | {'Avg Time (s)':>12}"
        print(header)
        print("-" * len(header))
        for jar, results in overall_results.items():
             avg_time = results['TotalTime'] / self.testcase_count if self.testcase_count > 0 else 0
             print(f"{jar:<25} | {results['AC']:>4} | {results['WA']:>4} | {results['RE']:>4} | {avg_time:>12.3f}")
        print("=" * 40)


if __name__ == '__main__':
    num_testcases = TESTCASE
    num_instructions = INSTRUCTION

    # Example: Override defaults from command line arguments if provided
    if len(sys.argv) == 3:
        try:
            num_testcases = int(sys.argv[1])
            num_instructions = int(sys.argv[2])
            if num_testcases <= 0 or num_instructions <= 0:
                 raise ValueError("Counts must be positive.")
            print(f"Running with {num_testcases} testcases, {num_instructions} instructions each.")
        except ValueError as e:
            print(f"Usage: python {sys.argv[0]} [num_testcases] [num_instructions]")
            print(f"Error parsing arguments: {e}", file=sys.stderr)
            sys.exit(1)
    elif len(sys.argv) != 1:
         print(f"Usage: python {sys.argv[0]} [num_testcases] [num_instructions]")
         sys.exit(1)

    tester = Tester(num_testcases, num_instructions)
    tester.run() # check_dependencies is called inside run()
    print("\nTesting finished.")