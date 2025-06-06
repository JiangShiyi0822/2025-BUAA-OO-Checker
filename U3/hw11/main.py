import os
import time
import random

from generator import Generator

TESTCASE = 100
INSTRUCTION = 10000 
DEFAULT_LN_RELATION_PROB = 0.9 
DEFAULT_LN_MIN_PERSONS = 100
DEFAULT_LN_MAX_PERSONS = 300
DEFAULT_PROBABILITY_LN_IS_FIRST: float = 0.8 


class Tester:
    testcase_count: int
    instruction_count: int
    ln_min_persons: int
    ln_max_persons: int
    ln_relation_prob: float
    probability_ln_is_first: float

    ACCEPTED: int = 0
    WRONG_ANSWER: int = 1
    RUNTIME_ERROR: int = 2
    STD_JAR_ERROR: int = 3 

    overall_results: dict[str, dict[int, int]] 
    # To store runtime details for each jar: jar_name -> list of runtimes for each testcase
    jar_runtimes: dict[str, list[float]]


    def __init__(self, testcase_count: int, instruction_count: int, 
                 ln_min_p: int = DEFAULT_LN_MIN_PERSONS,
                 ln_max_p: int = DEFAULT_LN_MAX_PERSONS,
                 ln_rel_prob: float = DEFAULT_LN_RELATION_PROB,
                 prob_ln_first: float = DEFAULT_PROBABILITY_LN_IS_FIRST):
        self.testcase_count = testcase_count
        self.instruction_count = instruction_count 
        self.ln_min_persons = ln_min_p
        self.ln_max_persons = ln_max_p
        self.ln_relation_prob = ln_rel_prob
        
        if 0.0 <= prob_ln_first <= 1.0:
            self.probability_ln_is_first = prob_ln_first
        else:
            print(f"Warning: Invalid probability_ln_is_first ({prob_ln_first}). Using default {DEFAULT_PROBABILITY_LN_IS_FIRST}.")
            self.probability_ln_is_first = DEFAULT_PROBABILITY_LN_IS_FIRST
            
        self.overall_results = {}
        self.jar_runtimes = {} # Initialize runtime storage
        for dir_name in ['input', 'output', 'answer', 'jar']:
            if not os.path.isdir(dir_name):
                os.mkdir(dir_name)

    def check_dependencies(self) -> bool:
        if not os.path.isdir('input'): print("Error: input directory not found."); return False
        if not os.path.isdir('output'): print("Error: output directory not found."); return False
        if not os.path.isdir('answer'): print("Error: answer directory not found."); return False
        if not os.path.isdir('jar'): print("Error: jar directory not found."); return False
        if not os.path.isfile('std.jar'): print("Error: std.jar not found."); return False
        return True

    def get_jar_list(self):
        return [f for f in os.listdir('jar') if os.path.isfile(os.path.join('jar', f)) and f.endswith('.jar')]

    def run(self):
        generator = Generator(
            load_network_min_persons=self.ln_min_persons,
            load_network_max_persons=self.ln_max_persons,
            load_network_relation_probability=self.ln_relation_prob
        ) 
        jar_list = self.get_jar_list()

        if not jar_list:
            print("Error: no jar file found in 'jar' directory.")
            return

        for jar_filename in jar_list:
            self.overall_results[jar_filename] = {
                self.ACCEPTED: 0, self.WRONG_ANSWER: 0,
                self.RUNTIME_ERROR: 0, self.STD_JAR_ERROR: 0
            }
            self.jar_runtimes[jar_filename] = [] # Initialize list for this jar's runtimes

        
        failing_testcases_details: dict[str, dict[str, list[int]]] = {
            jar_name: {"WA": [], "RE": [], "STD_FAIL": []} for jar_name in jar_list
        }


        for i in range(self.testcase_count):
            current_testcase_num = i + 1
            print(f"Testcase {current_testcase_num}:")
            
            generator.reset_internal_state_and_ops() 

            remaining_instructions = self.instruction_count
            has_ln_in_testcase = False 

            if random.random() < self.probability_ln_is_first and self.instruction_count > 0 : 
                print(f"  (Testcase {current_testcase_num} starts with Load Network)")
                generator.add_operation_load_network() 
                remaining_instructions -= 1
                has_ln_in_testcase = True 
            
            if remaining_instructions < 0: remaining_instructions = 0
            
            if remaining_instructions > 0 :
                 generator.add_operations_randomly(remaining_instructions) 
            
            instrs = generator.get_result() 
            if not instrs and self.instruction_count > 0:
                if not (self.instruction_count == 1 and has_ln_in_testcase):
                    print(f"  Warning: No instructions generated for TC {current_testcase_num} (expected {self.instruction_count}, ln={has_ln_in_testcase}, rem={remaining_instructions}).")

            input_file_name = f"test{current_testcase_num}.txt"
            answer_file_name = f"test_ans{current_testcase_num}.txt"
            input_file_path = os.path.join('input', input_file_name)
            answer_file_path = os.path.join('answer', answer_file_name)

            with open(input_file_path, 'w') as f:
                for instr_line in instrs: 
                    f.write(instr_line + '\n')

            # Run std.jar (runtime not typically measured for std)
            std_jar_cmd = f"java -jar std.jar < {input_file_path} > {answer_file_path}"
            return_code_std = os.system(std_jar_cmd)

            if return_code_std != 0:
                print(f"  Error: std.jar runtime error (Code: {return_code_std}) in testcase {current_testcase_num}.")
                for jar_filename in jar_list:
                    self.overall_results[jar_filename][self.STD_JAR_ERROR] += 1
                    failing_testcases_details[jar_filename]["STD_FAIL"].append(current_testcase_num)
                    self.jar_runtimes[jar_filename].append(-1.0) # Indicate std_jar failure, no valid runtime
                print("-" * 30)
                continue 

            # Store results for current testcase to print them together
            # (jar_filename -> (status_code, runtime_seconds))
            testcase_jar_summary: dict[str, tuple[int, float]] = {}

            for jar_filename in jar_list:
                output_filename_base = f"test{current_testcase_num}_{jar_filename}.txt"
                output_file_path = os.path.join('output', output_filename_base)
                jar_path = os.path.join('jar', jar_filename)
                user_jar_cmd = f"java -jar {jar_path} < {input_file_path} > {output_file_path}"
                
                start_time = time.perf_counter() # More precise timer
                return_code_user = os.system(user_jar_cmd)
                end_time = time.perf_counter()
                execution_time_seconds = end_time - start_time
                
                self.jar_runtimes[jar_filename].append(execution_time_seconds) # Store runtime

                # time.sleep(0.05) # This sleep is for file system to catch up, not part of jar exec time.
                                 # Keep it if needed, but outside timing.
                
                current_status_for_jar = -1

                if return_code_user != 0:
                    current_status_for_jar = self.RUNTIME_ERROR
                    self.overall_results[jar_filename][self.RUNTIME_ERROR] += 1
                    failing_testcases_details[jar_filename]["RE"].append(current_testcase_num)
                else:
                    try:
                        with open(output_file_path, 'r', encoding='utf-8', errors='ignore') as f_out:
                            output_content = f_out.read()
                        with open(answer_file_path, 'r', encoding='utf-8', errors='ignore') as f_ans:
                            answer_content = f_ans.read()

                        normalized_output = '\n'.join(line.rstrip() for line in output_content.splitlines()).strip()
                        normalized_answer = '\n'.join(line.rstrip() for line in answer_content.splitlines()).strip()

                        if normalized_output == normalized_answer:
                            current_status_for_jar = self.ACCEPTED
                            self.overall_results[jar_filename][self.ACCEPTED] += 1
                        else:
                            current_status_for_jar = self.WRONG_ANSWER
                            self.overall_results[jar_filename][self.WRONG_ANSWER] += 1
                            failing_testcases_details[jar_filename]["WA"].append(current_testcase_num)
                    except Exception as e: 
                        print(f"    Error during diff for {jar_filename} (TC {current_testcase_num}): {e}")
                        current_status_for_jar = self.RUNTIME_ERROR 
                        self.overall_results[jar_filename][self.RUNTIME_ERROR] += 1
                        failing_testcases_details[jar_filename]["RE"].append(current_testcase_num)
                
                testcase_jar_summary[jar_filename] = (current_status_for_jar, execution_time_seconds)

            # Print results for the current testcase including runtime
            for jar_file, (result_status, exec_time) in testcase_jar_summary.items():
                status_message = ""
                if result_status == self.ACCEPTED: status_message = "Accepted"
                elif result_status == self.WRONG_ANSWER: status_message = "Wrong Answer"
                elif result_status == self.RUNTIME_ERROR: status_message = "Runtime Error"
                else: status_message = f"Unknown Status ({result_status})" 
                print(f"  {jar_file}: {status_message} (Runtime: {exec_time:.3f}s)")
            print("-" * 30)
        
        self.print_final_summary(failing_testcases_details)

    def print_final_summary(self, failing_details: dict[str, dict[str, list[int]]]):
        print("\n" + "=" * 15 + " FINAL TEST SUMMARY " + "=" * 15)
        if not self.overall_results:
            print("No JARs were tested or no results available.")
            return

        for jar_filename, results in self.overall_results.items():
            print(f"\n--- Summary for {jar_filename} ---")
            ac_count = results.get(self.ACCEPTED, 0)
            wa_count = results.get(self.WRONG_ANSWER, 0)
            re_count = results.get(self.RUNTIME_ERROR, 0)
            std_fail_count = results.get(self.STD_JAR_ERROR, 0)
            
            total_possible_judgements = self.testcase_count - std_fail_count

            print(f"  Accepted (AC):        {ac_count}/{total_possible_judgements if total_possible_judgements >= 0 else self.testcase_count}")
            
            print(f"  Wrong Answer (WA):    {wa_count}")
            if wa_count > 0 and failing_details[jar_filename]['WA']:
                print(f"    Failing Testcases (WA): {', '.join(map(str, sorted(list(set(failing_details[jar_filename]['WA'])))))}")
            
            print(f"  Runtime Error (RE):   {re_count}")
            if re_count > 0 and failing_details[jar_filename]['RE']:
                print(f"    Failing Testcases (RE): {', '.join(map(str, sorted(list(set(failing_details[jar_filename]['RE'])))))}")

            if std_fail_count > 0:
                print(f"  Skipped (std.jar err):{std_fail_count}")
                if failing_details[jar_filename]['STD_FAIL']:
                     print(f"    Testcases affected by std.jar failure: {', '.join(map(str, sorted(list(set(failing_details[jar_filename]['STD_FAIL'])))))}")
            
            # Calculate and print average runtime for this jar
            runtimes_for_jar = self.jar_runtimes.get(jar_filename, [])
            valid_runtimes = [rt for rt in runtimes_for_jar if rt >= 0] # Exclude -1.0 for std_jar failures
            if valid_runtimes:
                avg_runtime = sum(valid_runtimes) / len(valid_runtimes)
                max_runtime = max(valid_runtimes)
                min_runtime = min(valid_runtimes)
                print(f"  Avg Runtime:          {avg_runtime:.3f}s (Min: {min_runtime:.3f}s, Max: {max_runtime:.3f}s over {len(valid_runtimes)} judged TCs)")
            else:
                print("  Avg Runtime:          N/A (No successful runs or std.jar failed for all)")


            if total_possible_judgements > 0:
                if ac_count == total_possible_judgements:
                    print(f"  Overall Status: ALL PASS (among {total_possible_judgements} judged testcases)")
                elif ac_count > 0 :
                    print(f"  Overall Status: PARTIALLY PASS (among {total_possible_judgements} judged testcases)")
                else:
                    print(f"  Overall Status: ALL FAIL (among {total_possible_judgements} judged testcases)")
            elif std_fail_count == self.testcase_count: 
                 print(f"  Overall Status: ALL SKIPPED (std.jar failed for all testcases or no testcases judged)")
            else: 
                 print(f"  Overall Status: NO TESTCASES JUDGED OR ALL SKIPPED")
        print("=" * (48))

if __name__ == '__main__':
    tester = Tester(TESTCASE, INSTRUCTION) 
    if tester.check_dependencies():
        tester.run()
    else:
        print("Dependency check failed. Exiting.")