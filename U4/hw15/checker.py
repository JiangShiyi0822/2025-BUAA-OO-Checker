import random
import subprocess
import os
import datetime
import time
import re
from collections import defaultdict
import threading # 用于 stderr 读取
import queue # 用于 stderr 读取

# --- Configuration ---
JAR_PATH = "test.jar"
JAVA_CMD = "java"
BASE_DATE = datetime.date(2025, 1, 1)
RANDOM_SEED = None # 设置一个整数以获得可复现的测试, e.g., 42

# --- 枚举和常量 ---
class BookLocation:
    BOOKSHELF = "bs"
    HOT_BOOKSHELF = "hbs"
    APPOINTMENT_OFFICE = "ao"
    BORROW_RETURN_OFFICE = "bro"
    READING_ROOM = "rr"
    USER = "user"
    UNKNOWN = "unknown"

class BookType:
    A = 'A'
    B = 'B'
    C = 'C'

class LibraryBookState_Official:
    BOOKSHELF = "bs"
    APPOINTMENT_OFFICE = "ao"
    BORROW_RETURN_OFFICE = "bro"
    READING_ROOM = "rr"
    HOT_BOOKSHELF = "hbs"
    USER = "user"

# --- 错误记录 ---
errors_lock = threading.Lock()
errors = []
# warnings = [] # Removed warnings list

def log_entry(log_list, prefix, message, command=None, output=None):
    log_msg = f"{prefix}: {message}"
    if command: log_msg += f"\n  COMMAND: {command}"
    if output:
        if isinstance(output, list):
            output_str = "\n    ".join(output)
            log_msg += f"\n  OUTPUT:\n    {output_str}"
        else:
            log_msg += f"\n  OUTPUT: {str(output)}"
    
    with errors_lock:
        log_list.append(log_msg)
    print(log_msg) # 实时打印错误，以便观察

def log_error(message, command=None, output=None):
    log_entry(errors, "ERROR", message, command, output)


# --- Helper Functions ---
def generate_student_id():
    return str(random.randint(23370000, 23370099))

def generate_book_uid():
    return f"{random.randint(0, 999):04d}"

def format_date(date_obj):
    return date_obj.strftime("%Y-%m-%d")

def parse_date_from_command_line(command_str):
    match = re.match(r"\[(\d{4}-\d{2}-\d{2})\]", command_str)
    if match:
        return datetime.datetime.strptime(match.group(1), "%Y-%m-%d").date()
    return None

# --- stderr Reader Thread ---
def stderr_reader_thread(pipe, q):
    try:
        for line in iter(pipe.readline, ''): 
            q.put(line)
    except ValueError: 
        pass 
    except Exception as e:
        pass


# --- Core Classes ---
class BookCopy:
    def __init__(self, book_id_str, isbn_str, book_type_char):
        self.id = book_id_str
        self.isbn = isbn_str
        self.type = book_type_char
        self.location = BookLocation.BOOKSHELF
        self.borrowed_by_student_id = None
        self.borrow_date = None 
        self.reserved_for_student_id = None
        self.reservation_arrival_date = None 
        self.reservation_expiry_date = None 
        self.is_hot_candidate_this_cycle = False 
        self.read_by_student_id = None

    def __repr__(self):
        return (f"<BookCopy {self.id} at {self.location} "
                f"borrowed_by:{self.borrowed_by_student_id} reserved_for:{self.reserved_for_student_id} "
                f"read_by:{self.read_by_student_id}>")

class Student:
    def __init__(self, student_id):
        self.id = student_id
        self.credits = 100
        self.held_books_b = set() 
        self.held_books_c = defaultdict(set) 
        self.active_order_isbn = None 
        self.book_being_read_id = None
        self.read_today_and_not_yet_returned = False 

    def __repr__(self):
        return f"<Student {self.id}, Cr:{self.credits}, B:{len(self.held_books_b)}, C:{sum(len(s) for s in self.held_books_c.values())}, Ord:{self.active_order_isbn}, Read:{self.book_being_read_id}>"

    def _update_credits(self, amount, reason=""):
        old_credits = self.credits
        self.credits += amount
        if self.credits > 180: self.credits = 180
        if self.credits < 0: self.credits = 0
        # if old_credits != self.credits:
            # print(f"DEBUG CREDIT: Student {self.id} credits {old_credits} -> {self.credits} (by {amount}, reason: {reason}) Date: {LibraryState.current_date_for_debug}")


    def add_credits(self, amount, reason=""): self._update_credits(amount, reason)
    def remove_credits(self, amount, reason=""): self._update_credits(-amount, reason)

    def can_borrow_b(self, state): return not self.held_books_b
    def can_borrow_c(self, state, isbn_to_borrow): return isbn_to_borrow not in self.held_books_c
    
    def can_order_b(self, state):
        return not self.held_books_b and not self.active_order_isbn
    def can_order_c(self, state, isbn_to_order):
        return isbn_to_order not in self.held_books_c and not self.active_order_isbn

class LibraryState:
    current_date_for_debug = BASE_DATE 

    def __init__(self):
        self.current_date = BASE_DATE
        LibraryState.current_date_for_debug = self.current_date 
        self.library_is_open = False
        self.last_open_processing_date = None 

        self.all_book_copies = {} 
        self.books_by_isbn = defaultdict(list) 

        self.students = {} 
        self.hot_isbns_from_last_cycle = set() 
        self.overdue_deduction_tracker = defaultdict(lambda: defaultdict(bool)) 


    def _update_current_date(self, new_date):
        self.current_date = new_date
        LibraryState.current_date_for_debug = new_date

    def get_student(self, student_id, create_if_missing=True):
        if student_id not in self.students and create_if_missing:
            self.students[student_id] = Student(student_id)
        return self.students.get(student_id)

    def add_book_copy(self, book_copy_obj):
        self.all_book_copies[book_copy_obj.id] = book_copy_obj
        self.books_by_isbn[book_copy_obj.isbn].append(book_copy_obj)

    def generate_initial_inventory(self, num_isbn_types_range=(2, 5), copies_per_isbn_range=(1, 3)):
        initial_inventory_lines = []
        num_isbns = random.randint(*num_isbn_types_range)
        initial_inventory_lines.append(str(num_isbns))
        generated_isbns_this_run = set()

        for _ in range(num_isbns):
            book_type_char = random.choice([BookType.A, BookType.B, BookType.C])
            uid = generate_book_uid()
            isbn_str = f"{book_type_char}-{uid}"
            while isbn_str in generated_isbns_this_run:
                 uid = generate_book_uid()
                 isbn_str = f"{book_type_char}-{uid}"
            generated_isbns_this_run.add(isbn_str)

            num_copies = random.randint(*copies_per_isbn_range)
            initial_inventory_lines.append(f"{isbn_str} {num_copies}")
            for i in range(1, num_copies + 1):
                copy_id_str = f"{i:02d}"
                book_id_str = f"{isbn_str}-{copy_id_str}"
                book_copy = BookCopy(book_id_str, isbn_str, book_type_char)
                self.add_book_copy(book_copy)
        return initial_inventory_lines

    def get_book_copy_on_shelf(self, isbn_str):
        for book_copy in self.books_by_isbn.get(isbn_str, []):
            if book_copy.location in [BookLocation.BOOKSHELF, BookLocation.HOT_BOOKSHELF]:
                return book_copy
        return None

    def get_random_isbn(self, book_type_filter=None, ensure_on_shelf=False):
        eligible_isbns = []
        for isbn, copies_list in self.books_by_isbn.items():
            if not copies_list: 
                continue
            book_type_of_this_isbn = copies_list[0].type 
            
            type_match = True
            if book_type_filter:
                if isinstance(book_type_filter, list): 
                    if book_type_of_this_isbn not in book_type_filter:
                        type_match = False
                elif book_type_of_this_isbn != book_type_filter: 
                    type_match = False
            if not type_match: continue

            if ensure_on_shelf:
                if not self.get_book_copy_on_shelf(isbn): 
                    continue
            eligible_isbns.append(isbn)
        return random.choice(eligible_isbns) if eligible_isbns else None

    def get_random_book_id(self, location_filter=None, owner_filter_student_id=None, specific_isbn=None):
        eligible_book_ids = []
        source_books = self.all_book_copies.values()
        if specific_isbn: 
            source_books = self.books_by_isbn.get(specific_isbn, [])

        for book_copy in source_books:
            valid = True
            if location_filter:
                if isinstance(location_filter, list):
                    if book_copy.location not in location_filter: valid = False
                elif book_copy.location != location_filter: valid = False
            if owner_filter_student_id and book_copy.borrowed_by_student_id != owner_filter_student_id:
                valid = False
            if valid: eligible_book_ids.append(book_copy.id)
        return random.choice(eligible_book_ids) if eligible_book_ids else None

    def _check_credit_rules(self, student, action_type, book_type_char=None):
        if action_type in ["borrow", "order"]:
            if student.credits < (100 if action_type == "order" else 60) and \
               book_type_char in [BookType.B, BookType.C]:
                return False, f"信用分 {student.credits} 不足 (需 {'100' if action_type == 'order' else '60'})"
        elif action_type == "read":
            if book_type_char == BookType.A and student.credits < 40:
                return False, f"信用分 {student.credits} 不足 (需 40 读A类)"
            if book_type_char in [BookType.B, BookType.C] and student.credits == 0:
                return False, f"信用分 {student.credits} 为0 (不可读B/C类)"
        return True, ""

    def pre_check_borrow(self, student_id, isbn_str):
        student = self.get_student(student_id)
        book_type = isbn_str[0]
        
        valid_credits, reason_credits = self._check_credit_rules(student, "borrow", book_type)
        if not valid_credits: return False, reason_credits

        if book_type == BookType.A: return False, "A类书不可借阅"
        if not self.get_book_copy_on_shelf(isbn_str): return False, f"书架无 {isbn_str} 余本"
        if book_type == BookType.B and not student.can_borrow_b(self): return False, "已持有B类书"
        if book_type == BookType.C and not student.can_borrow_c(self, isbn_str): return False, f"已持有C类书({isbn_str})"
        return True, "Checker认为可借阅"

    def pre_check_return(self, student_id, book_id_str):
        student = self.get_student(student_id)
        book = self.all_book_copies.get(book_id_str)
        if not book or book.borrowed_by_student_id != student_id or book.location != BookLocation.USER:
            return False, "非该学生持有或书不在用户手中"
        return True, "Checker认为可还书"

    def pre_check_order(self, student_id, isbn_str):
        student = self.get_student(student_id)
        book_type = isbn_str[0]

        valid_credits, reason_credits = self._check_credit_rules(student, "order", book_type)
        if not valid_credits: return False, reason_credits

        if book_type == BookType.A: return False, "A类书不可预约"
        if student.active_order_isbn: return False, "已有未完成预约"
        if book_type == BookType.B and not student.can_order_b(self): return False, "已持有B类或已有预约"
        if book_type == BookType.C and not student.can_order_c(self, isbn_str): return False, f"已持有C类({isbn_str})或已有预约"
        return True, "Checker认为可预约"

    def pre_check_pick(self, student_id, isbn_str):
        student = self.get_student(student_id)
        book_type = isbn_str[0]

        if student.active_order_isbn != isbn_str: return False, "未有效预约此ISBN或预约已完成/失效"
        
        reserved_book_at_ao = None
        for book in self.books_by_isbn.get(isbn_str, []):
            if book.location == BookLocation.APPOINTMENT_OFFICE and \
               book.reserved_for_student_id == student_id and \
               book.reservation_expiry_date and self.current_date <= book.reservation_expiry_date:
                reserved_book_at_ao = book
                break
        if not reserved_book_at_ao: return False, "预约处无此预留或已过期"

        if book_type == BookType.B and not student.can_borrow_b(self): return False, "取后将违反B类借阅数限"
        if book_type == BookType.C and not student.can_borrow_c(self, isbn_str): return False, "取后将违反C类借阅数限"
        return True, "Checker认为可取书"

    def pre_check_read(self, student_id, isbn_str):
        student = self.get_student(student_id)
        book_type = isbn_str[0]

        valid_credits, reason_credits = self._check_credit_rules(student, "read", book_type)
        if not valid_credits: return False, reason_credits

        if student.read_today_and_not_yet_returned : return False, "当日已有阅读后未归还"
        if not self.get_book_copy_on_shelf(isbn_str): return False, f"书架无 {isbn_str} 余本"
        return True, "Checker认为可阅读"

    def pre_check_restore(self, student_id, book_id_str):
        student = self.get_student(student_id)
        book = self.all_book_copies.get(book_id_str)
        if not book or student.book_being_read_id != book_id_str or \
           book.read_by_student_id != student_id or book.location != BookLocation.READING_ROOM:
            return False, "非该学生当前阅读或书不在阅览室"
        return True, "Checker认为可归还(阅读)"

    def _update_book_location(self, book_id, new_loc, cmd_str, from_loc_expected=None):
        book = self.all_book_copies.get(book_id)
        if not book: return
        if from_loc_expected and book.location != from_loc_expected:
            log_error(f"书籍 {book_id} 移动前位置 ({book.location})与预期 ({from_loc_expected})不符", cmd_str)
        book.location = new_loc
    
    def post_check_borrow_accept(self, cmd_str, student_id, req_isbn, acc_book_id):
        student = self.get_student(student_id)
        book = self.all_book_copies.get(acc_book_id)
        parsed_date = parse_date_from_command_line(cmd_str)

        if not book: log_error(f"借阅成功返回无效副本号 {acc_book_id}", cmd_str); return
        if book.isbn != req_isbn: log_error(f"借阅成功副本 {acc_book_id}({book.isbn})非请求ISBN {req_isbn}", cmd_str); return
        
        original_loc = book.location
        expected_from_loc = None
        if original_loc == BookLocation.BOOKSHELF: expected_from_loc = BookLocation.BOOKSHELF
        elif original_loc == BookLocation.HOT_BOOKSHELF: expected_from_loc = BookLocation.HOT_BOOKSHELF
        else: log_error(f"借阅的书 {acc_book_id} 原本不在书架上 (位置: {original_loc})", cmd_str) 
        
        if expected_from_loc: 
            self._update_book_location(acc_book_id, BookLocation.USER, cmd_str, from_loc_expected=expected_from_loc)
        else: 
            self._update_book_location(acc_book_id, BookLocation.USER, cmd_str)

        book.borrowed_by_student_id = student_id
        book.borrow_date = parsed_date
        book.is_hot_candidate_this_cycle = True 
        self.overdue_deduction_tracker[student_id].pop(f"{student.id}_{book.id}_last_day_penalty_{parsed_date.isoformat()}", None) 
        self.overdue_deduction_tracker[student_id].pop(f"{student.id}_{book.id}_daily_penalty_{parsed_date.isoformat()}", None)


        if book.type == BookType.B: student.held_books_b.add(acc_book_id)
        elif book.type == BookType.C: student.held_books_c[book.isbn].add(acc_book_id)

    def post_check_return_accept(self, cmd_str, student_id, ret_book_id, overdue_status_from_prog):
        student = self.get_student(student_id)
        book = self.all_book_copies.get(ret_book_id)
        parsed_date = parse_date_from_command_line(cmd_str) 

        if not book: log_error(f"还书成功涉及无效副本号 {ret_book_id}", cmd_str); return

        self._update_book_location(ret_book_id, BookLocation.BORROW_RETURN_OFFICE, cmd_str, from_loc_expected=BookLocation.USER)
        book.borrowed_by_student_id = None
        if book.type == BookType.B: student.held_books_b.discard(ret_book_id)
        elif book.type == BookType.C: 
            if book.isbn in student.held_books_c: 
                student.held_books_c[book.isbn].discard(ret_book_id)
                if not student.held_books_c[book.isbn]: del student.held_books_c[book.isbn]

        checker_calculates_as_on_time = True 
        limit_days = 0 
        if book.borrow_date:
            limit_days = 30 if book.type == BookType.B else 60
            last_due_date = book.borrow_date + datetime.timedelta(days=limit_days)
            if parsed_date > last_due_date:
                checker_calculates_as_on_time = False
        else:
            log_error(f"还书的书籍 {ret_book_id} 在Checker中没有借阅日期记录，无法准确判断是否按时", cmd_str)
            if overdue_status_from_prog == "overdue": checker_calculates_as_on_time = False
        
        if overdue_status_from_prog == "overdue" and checker_calculates_as_on_time:
            log_error(f"程序报告逾期，但Checker计算未逾期 for {ret_book_id} (borrowed: {book.borrow_date}, returned: {parsed_date}, limit: {limit_days})", cmd_str)
        elif overdue_status_from_prog == "not overdue" and not checker_calculates_as_on_time:
            log_error(f"程序报告未逾期，但Checker计算已逾期 for {ret_book_id} (borrowed: {book.borrow_date}, returned: {parsed_date}, limit: {limit_days})", cmd_str)

        if checker_calculates_as_on_time: 
            student.add_credits(10, f"on-time return of {ret_book_id} on {parsed_date}")
        
        book.borrow_date = None 
        keys_to_remove = [k for k in self.overdue_deduction_tracker[student_id] if ret_book_id in k]
        for k in keys_to_remove:
            if k in self.overdue_deduction_tracker[student_id]: 
                del self.overdue_deduction_tracker[student_id][k]


    def post_check_order_accept(self, cmd_str, student_id, ord_isbn):
        student = self.get_student(student_id)
        student.active_order_isbn = ord_isbn

    def post_check_pick_accept(self, cmd_str, student_id, req_isbn, acc_book_id):
        student = self.get_student(student_id)
        book = self.all_book_copies.get(acc_book_id)
        parsed_date = parse_date_from_command_line(cmd_str)

        if not book: log_error(f"取书成功返回无效副本号 {acc_book_id}", cmd_str); return
        if book.isbn != req_isbn: log_error(f"取书成功副本 {acc_book_id}({book.isbn})非请求ISBN {req_isbn}", cmd_str); return
        if book.reserved_for_student_id != student_id: log_error(f"取书副本 {acc_book_id} 非为该学生预留 (Checker记录为 {book.reserved_for_student_id})", cmd_str);

        self._update_book_location(acc_book_id, BookLocation.USER, cmd_str, from_loc_expected=BookLocation.APPOINTMENT_OFFICE)
        book.borrowed_by_student_id = student_id
        book.borrow_date = parsed_date 
        # book.is_hot_candidate_this_cycle = True # Picked book does NOT become hot candidate by this action
        
        keys_to_remove = [k for k in self.overdue_deduction_tracker[student_id] if acc_book_id in k]
        for k in keys_to_remove:
            if k in self.overdue_deduction_tracker[student_id]:
                del self.overdue_deduction_tracker[student_id][k]

        book.reserved_for_student_id = None 
        book.reservation_arrival_date = None
        book.reservation_expiry_date = None
        
        student.active_order_isbn = None 
        if book.type == BookType.B: student.held_books_b.add(acc_book_id)
        elif book.type == BookType.C: student.held_books_c[book.isbn].add(acc_book_id)

    def post_check_read_accept(self, cmd_str, student_id, req_isbn, acc_book_id):
        student = self.get_student(student_id)
        book = self.all_book_copies.get(acc_book_id)

        if not book: log_error(f"阅读成功返回无效副本号 {acc_book_id}", cmd_str); return
        if book.isbn != req_isbn: log_error(f"阅读成功副本 {acc_book_id}({book.isbn})非请求ISBN {req_isbn}", cmd_str); return

        original_loc = book.location
        expected_from_loc = None
        if original_loc == BookLocation.BOOKSHELF: expected_from_loc = BookLocation.BOOKSHELF
        elif original_loc == BookLocation.HOT_BOOKSHELF: expected_from_loc = BookLocation.HOT_BOOKSHELF
        else: log_error(f"阅读的书 {acc_book_id} 原本不在书架上 (位置: {original_loc})", cmd_str)

        if expected_from_loc:
            self._update_book_location(acc_book_id, BookLocation.READING_ROOM, cmd_str, from_loc_expected=expected_from_loc)
        else:
            self._update_book_location(acc_book_id, BookLocation.READING_ROOM, cmd_str)

        book.read_by_student_id = student_id
        book.is_hot_candidate_this_cycle = True 
        student.book_being_read_id = acc_book_id
        student.read_today_and_not_yet_returned = True

    def post_check_restore_accept(self, cmd_str, student_id, res_book_id):
        student = self.get_student(student_id)
        book = self.all_book_copies.get(res_book_id)

        if not book: log_error(f"阅读归还成功涉及无效副本号 {res_book_id}", cmd_str); return
        
        self._update_book_location(res_book_id, BookLocation.BORROW_RETURN_OFFICE, cmd_str, from_loc_expected=BookLocation.READING_ROOM)
        book.read_by_student_id = None
        student.book_being_read_id = None
        student.read_today_and_not_yet_returned = False
        student.add_credits(10, f"restored read book {res_book_id} on {self.current_date}")

    def post_check_queried_credit(self, cmd_str, student_id_req, credit_out_str):
        student = self.get_student(student_id_req, False) 
        try: credit_out = int(credit_out_str)
        except ValueError: log_error(f"信用查询返回非数字信用分: {credit_out_str}", cmd_str); return

        if not student: 
            if credit_out != 100: log_error(f"新学生 {student_id_req} 信用查询非100 (程序输出: {credit_out})", cmd_str)
            return
        if student.credits != credit_out:
            log_error(f"信用查询不一致 for {student_id_req}: Checker={student.credits}, Prog={credit_out} on {self.current_date}", cmd_str)
    
    def post_check_queried_trace(self, cmd_str, book_id_req, output_lines):
        if not output_lines: log_error(f"查询轨迹 {book_id_req} 无输出", cmd_str); return
        
        match_first = re.match(r"\[\d{4}-\d{2}-\d{2}\]\s+([\w\d-]+-[\w\d]+-[\w\d]+)\s+moving trace:\s+(\d+)", output_lines[0])
        if not match_first: log_error(f"轨迹查询首行格式错误: {output_lines[0]}", cmd_str); return
        
        book_id_out, num_traces_str = match_first.groups()
        if book_id_out != book_id_req: log_error(f"轨迹查询首行书号 {book_id_out} 与请求 {book_id_req} 不符", cmd_str)
        
        try: num_traces_prog = int(num_traces_str)
        except ValueError: log_error(f"轨迹查询首行条数非数字: {num_traces_str}", cmd_str); return
        
        if num_traces_prog != len(output_lines) - 1:
            log_error(f"轨迹查询报告 {num_traces_prog} 条, 实际输出 {len(output_lines)-1} 条", cmd_str, output_lines)

    def _handle_organize_moves(self, cmd_str, move_lines_from_prog, is_open_op):
        parsed_date = parse_date_from_command_line(cmd_str)
        if not move_lines_from_prog : 
            if isinstance(move_lines_from_prog, list) and not move_lines_from_prog: return
            log_error(f"整理流程move输出格式错误, 期望数字或空列表", cmd_str, move_lines_from_prog); return

        num_moves_prog = -1 
        try:
            num_moves_prog = int(move_lines_from_prog[0])
            if num_moves_prog != len(move_lines_from_prog) - 1:
                log_error(f"整理报告移动 {num_moves_prog} 条, 实际输出 {len(move_lines_from_prog)-1} 条", cmd_str, move_lines_from_prog)
        except (ValueError, TypeError, IndexError) :
             if len(move_lines_from_prog) == 1 and move_lines_from_prog[0] == '0': pass 
             else: log_error(f"整理move首行非数字或格式错: {move_lines_from_prog[0] if move_lines_from_prog else 'None'}", cmd_str); return

        actual_move_strs = move_lines_from_prog[1:]
        # moved_books_this_pass = set() # Not strictly needed if not warning on multiple moves

        for move_str in actual_move_strs: 
            match = re.match(r"\[(\d{4}-\d{2}-\d{2})\] move ([\w\d-]+-[\w\d]+-[\w\d]+) from (\w+) to (\w+)(?: for (\d+))?", move_str)
            if not match: log_error(f"整理move格式错误: {move_str}", cmd_str); continue
            
            m_date, m_book_id, m_from_prog, m_to_prog, m_for_sid_prog = match.groups() 
            if m_date != format_date(parsed_date): log_error(f"整理move日期 {m_date} 与指令日期 {format_date(parsed_date)} 不符: {move_str}", cmd_str)

            book = self.all_book_copies.get(m_book_id)
            if not book: log_error(f"整理move未知书籍 {m_book_id}", cmd_str); continue
            
            # moved_books_this_pass.add(m_book_id)

            if m_from_prog == m_to_prog: log_error(f"整理move起点终点相同 {m_from_prog}", cmd_str)
            
            # student_id_book_was_for_before_move = book.reserved_for_student_id  # Capture before update
            # book_isbn_book_was_for_before_move = book.isbn 
            
            if book.location != m_from_prog and book.location != BookLocation.UNKNOWN :
                 pass 
            
            # Update book's location based on program's move command
            book.location = m_to_prog

            if m_from_prog == BookLocation.APPOINTMENT_OFFICE:
                # If a book is moved FROM AO, and it was reserved for someone
                if book.reserved_for_student_id and m_to_prog != BookLocation.USER:
                    # This means the reservation ended (either expired or cleared by library)
                    # The student's active_order_isbn and credit deduction should have been handled
                    # in process_close_event on the expiry_date.
                    # Here, we just clear the book's own reservation details.
                    # print(f"INFO-MOVE: Book {m_book_id} (was for {book.reserved_for_student_id}) moved from AO (not to user). Clearing its reservation info. Date: {self.current_date}")
                    book.reserved_for_student_id = None
                    book.reservation_arrival_date = None
                    book.reservation_expiry_date = None
            
            elif m_to_prog == BookLocation.APPOINTMENT_OFFICE:
                if not m_for_sid_prog: log_error(f"整理move至ao未指定for学号: {m_book_id}", cmd_str); continue
                student_for = self.get_student(m_for_sid_prog, False)
                if not (student_for and student_for.active_order_isbn == book.isbn):
                    log_error(f"整理move至ao for {m_for_sid_prog}, 但其未有效预约 {book.isbn} (或Checker未记录)", cmd_str)
                
                book.reserved_for_student_id = m_for_sid_prog
                book.reservation_arrival_date = parsed_date
                start_reserve_day = parsed_date if is_open_op else parsed_date + datetime.timedelta(days=1)
                book.reservation_expiry_date = start_reserve_day + datetime.timedelta(days=4) 

            if m_from_prog == BookLocation.READING_ROOM and book.read_by_student_id:
                reader = self.get_student(book.read_by_student_id, False)
                if reader: reader.book_being_read_id = None 
                book.read_by_student_id = None

    def process_open_event(self, cmd_str, move_lines_from_prog):
        new_date = parse_date_from_command_line(cmd_str)
        self._update_current_date(new_date)
        self.library_is_open = True
        
        self._handle_organize_moves(cmd_str, move_lines_from_prog, is_open_op=True)

        for book_id, book in self.all_book_copies.items():
            if book.location == BookLocation.BORROW_RETURN_OFFICE: log_error(f"OPEN后 {book_id} 仍在bro", cmd_str)
            if book.location == BookLocation.READING_ROOM: log_error(f"OPEN后 {book_id} 仍在rr", cmd_str)
            if book.location == BookLocation.APPOINTMENT_OFFICE:
                if book.reserved_for_student_id and book.reservation_expiry_date and self.current_date > book.reservation_expiry_date:
                    log_error(f"OPEN后ao中书 {book_id} (for {book.reserved_for_student_id}) 仍被预留且已过期 (应保留至{book.reservation_expiry_date})", cmd_str)
                    student = self.get_student(book.reserved_for_student_id, False)
                    # Student's active_order_isbn and credit should have been handled by a previous CLOSE event.
                    # Here, we just ensure the book's state is consistent if program failed to move it.
                    if student and student.active_order_isbn == book.isbn: 
                        student.active_order_isbn = None 
                    book.reserved_for_student_id = None
                    book.reservation_expiry_date = None

        for book_id, book in self.all_book_copies.items():
            is_expected_hot = book.isbn in self.hot_isbns_from_last_cycle
            if book.location == BookLocation.HOT_BOOKSHELF and not is_expected_hot:
                log_error(f"OPEN后非热门ISBN {book.isbn} 的书 {book_id} 在hbs", cmd_str)
            if book.location == BookLocation.BOOKSHELF and is_expected_hot:
                log_error(f"OPEN后热门ISBN {book.isbn} 的书 {book_id} 在bs而非hbs", cmd_str)
        
        self.hot_isbns_from_last_cycle.clear()
        for book_copy_obj in self.all_book_copies.values(): 
            book_copy_obj.is_hot_candidate_this_cycle = False 
        
        for student in self.students.values():
            student.read_today_and_not_yet_returned = False

        self.last_open_processing_date = self.current_date

    def process_close_event(self, cmd_str, move_lines_from_prog):
        new_date = parse_date_from_command_line(cmd_str)
        self._update_current_date(new_date) 
        self.library_is_open = False

        self._handle_organize_moves(cmd_str, move_lines_from_prog, is_open_op=False)
        
        for student in self.students.values():
            if student.read_today_and_not_yet_returned: 
                student.remove_credits(10, f"not restoring read book by EOD {self.current_date}")
                if student.book_being_read_id:
                    book_read = self.all_book_copies.get(student.book_being_read_id)
                    if book_read and book_read.read_by_student_id == student.id:
                        book_read.read_by_student_id = None 
                    student.book_being_read_id = None
            student.read_today_and_not_yet_returned = False 

            if student.active_order_isbn:
                book_that_was_reserved_and_expired_today = None
                for book_copy_iter in self.books_by_isbn.get(student.active_order_isbn, []):
                    if book_copy_iter.reserved_for_student_id == student.id and \
                       book_copy_iter.reservation_expiry_date == self.current_date: 
                        book_that_was_reserved_and_expired_today = book_copy_iter
                        break 
                
                if book_that_was_reserved_and_expired_today:
                    # Check if the book was NOT picked up today (i.e., it's not in USER state by this student)
                    # Its location might have been changed by a move in this CLOSE, or still AO.
                    is_picked_up = (book_that_was_reserved_and_expired_today.location == BookLocation.USER and \
                                    book_that_was_reserved_and_expired_today.borrowed_by_student_id == student.id)

                    if not is_picked_up:
                        student.remove_credits(15, f"ordered book {student.active_order_isbn} (copy like {book_that_was_reserved_and_expired_today.id}) expired, not picked by EOD {self.current_date}")
                        student.active_order_isbn = None 
                        # print(f"INFO: Student {student.id} order for {book_that_was_reserved_and_expired_today.isbn} (copy {book_that_was_reserved_and_expired_today.id}) expired on {self.current_date}, -15 credits. Student active_order_isbn cleared.")
                        
                        book_that_was_reserved_and_expired_today.reserved_for_student_id = None
                        book_that_was_reserved_and_expired_today.reservation_arrival_date = None 
                        book_that_was_reserved_and_expired_today.reservation_expiry_date = None 

        for book_id, book in self.all_book_copies.items():
            if book.location == BookLocation.USER and book.borrowed_by_student_id and book.borrow_date:
                student = self.get_student(book.borrowed_by_student_id, False)
                if not student: continue

                limit_days = 30 if book.type == BookType.B else 60
                last_day_of_loan = book.borrow_date + datetime.timedelta(days=limit_days)
                
                deduction_key_last_day_penalty = f"{student.id}_{book.id}_last_day_penalty_{last_day_of_loan.isoformat()}"
                
                if self.current_date == last_day_of_loan:
                    if not self.overdue_deduction_tracker[student.id].get(deduction_key_last_day_penalty):
                        student.remove_credits(5, f"overdue book {book.id} - penalty on last due date EOD {self.current_date}")
                        self.overdue_deduction_tracker[student.id][deduction_key_last_day_penalty] = True
                elif self.current_date > last_day_of_loan:
                    deduction_key_daily_penalty_today = f"{student.id}_{book.id}_daily_penalty_{self.current_date.isoformat()}"
                    if not self.overdue_deduction_tracker[student.id].get(deduction_key_daily_penalty_today):
                        student.remove_credits(5, f"overdue book {book.id} - daily penalty on {self.current_date}")
                        self.overdue_deduction_tracker[student.id][deduction_key_daily_penalty_today] = True
        
        self.hot_isbns_from_last_cycle.clear()
        for book_copy_obj in self.all_book_copies.values(): 
            if book_copy_obj.is_hot_candidate_this_cycle:
                self.hot_isbns_from_last_cycle.add(book_copy_obj.isbn)
            book_copy_obj.is_hot_candidate_this_cycle = False 

def generate_next_command_str(state: LibraryState):
    if not state.library_is_open:
        next_date_to_open = state.current_date 
        if state.last_open_processing_date : 
             days_to_advance = random.randint(0, random.choice([1,1,1,1,1,2,3,5,7])) 
             if days_to_advance == 0 and state.current_date == state.last_open_processing_date: 
                 days_to_advance = 1
             next_date_to_open = state.current_date + datetime.timedelta(days=days_to_advance)
        elif state.current_date == BASE_DATE and not state.last_open_processing_date: 
             pass 
        else: 
             next_date_to_open = state.current_date + datetime.timedelta(days=1)
        return f"[{format_date(next_date_to_open)}] OPEN"
    
    if random.random() < 0.15 and state.library_is_open : 
        return f"[{format_date(state.current_date)}] CLOSE"

    student_id = None
    if not state.students or random.random() < 0.10: 
        student_id = generate_student_id()
        state.get_student(student_id) 
    else:
        student_id = random.choice(list(state.students.keys()))
    
    student = state.get_student(student_id)
    possible_actions_with_context = []

    if student.active_order_isbn:
        for book_iter in state.books_by_isbn.get(student.active_order_isbn,[]):
            if book_iter.location == BookLocation.APPOINTMENT_OFFICE and \
               book_iter.reserved_for_student_id == student.id and \
               book_iter.reservation_expiry_date and state.current_date <= book_iter.reservation_expiry_date:
                possible_actions_with_context.append(("picked", student.active_order_isbn)) 
                break 
    if student.book_being_read_id and student.read_today_and_not_yet_returned:
        possible_actions_with_context.append(("restored", student.book_being_read_id)) 
    held_b = list(student.held_books_b)
    held_c_flat = [item for sublist in student.held_books_c.values() for item in sublist]
    all_held = held_b + held_c_flat
    if all_held:
        possible_actions_with_context.append(("returned", random.choice(all_held))) 

    base_action_candidates = ["borrowed", "ordered", "read", "queried_credit", "queried_book"]
    
    chosen_cmd_str = None
    action_choice_rand = random.random()
    action_tuple = None 
    if possible_actions_with_context:
        if action_choice_rand < 0.3 and ("picked", student.active_order_isbn) in possible_actions_with_context: 
             action_tuple = ("picked", student.active_order_isbn)
        elif action_choice_rand < 0.5 and ("restored", student.book_being_read_id) in possible_actions_with_context :
             action_tuple = ("restored", student.book_being_read_id)
        elif action_choice_rand < 0.7 and any(a[0] == "returned" for a in possible_actions_with_context):
            returned_options = [a for a in possible_actions_with_context if a[0] == "returned"]
            action_tuple = random.choice(returned_options)
        else: 
            if possible_actions_with_context and random.random() < 0.5: 
                 action_tuple = random.choice(possible_actions_with_context)
            else:
                 action_tuple = None 
    else:
        action_tuple = None

    if action_tuple:
        act, item_id = action_tuple
        chosen_cmd_str = f"[{format_date(state.current_date)}] {student_id} {act} {item_id}"
    else: 
        chosen_base_action = random.choice(base_action_candidates)
        cmd_date_str = f"[{format_date(state.current_date)}]"
        if chosen_base_action == "borrowed":
            isbn = state.get_random_isbn(book_type_filter=[BookType.B, BookType.C], ensure_on_shelf=True)
            if isbn: chosen_cmd_str = f"{cmd_date_str} {student_id} borrowed {isbn}"
        elif chosen_base_action == "ordered":
            isbn = state.get_random_isbn(book_type_filter=[BookType.B, BookType.C]) 
            if isbn: chosen_cmd_str = f"{cmd_date_str} {student_id} ordered {isbn}"
        elif chosen_base_action == "read":
            isbn = state.get_random_isbn(ensure_on_shelf=True) 
            if isbn: chosen_cmd_str = f"{cmd_date_str} {student_id} read {isbn}"
        elif chosen_base_action == "queried_book":
            book_id_to_query = None
            if state.all_book_copies : 
                 book_id_to_query = state.get_random_book_id() 
            if book_id_to_query: 
                chosen_cmd_str = f"{cmd_date_str} {student_id} queried {book_id_to_query}"
        else: 
            chosen_cmd_str = f"{cmd_date_str} {student_id} queried credit score"
            
    return chosen_cmd_str if chosen_cmd_str else f"[{format_date(state.current_date)}] {student_id} queried credit score" 


def parse_command_from_line(line_str):
    match_date = re.match(r"\[(\d{4}-\d{2}-\d{2})\]\s*(.*)", line_str)
    if not match_date:
        if line_str.strip() in ["OPEN", "CLOSE"]: 
             return None, line_str.strip(), None, None, None
        return None, None, None, None, None 

    date_part_str = match_date.group(1)
    rest_of_cmd = match_date.group(2).strip()
    parts = rest_of_cmd.split()

    if not parts: return date_part_str, None, None, None, None
    
    if parts[0] in ["OPEN", "CLOSE"]:
        return date_part_str, parts[0], None, None, None 
    
    if len(parts) < 2: return date_part_str, None, None, None, None 

    student_id = parts[0]
    action = parts[1]
    
    book_identifier = None
    is_book_id_format = False 

    if action == "queried" and len(parts) > 2 and parts[2] == "credit":
        book_identifier = "credit score"
    elif len(parts) > 2:
        book_identifier = parts[2]
        if action in ["returned", "restored"] or (action == "queried" and book_identifier != "credit score"):
            is_book_id_format = True 
    
    return date_part_str, student_id, action, book_identifier, is_book_id_format


def parse_program_output_for_main_info(output_line_str):
    is_accept = "[accept]" in output_line_str
    is_reject = "[reject]" in output_line_str
    
    content = ""
    if is_accept: content = output_line_str.split("[accept]", 1)[1].strip()
    elif is_reject: content = output_line_str.split("[reject]", 1)[1].strip()
    else: return False, False, None, None, None, None

    parts = content.split()
    if len(parts) < 2: return is_accept, is_reject, None, None, None, None
    
    out_student = parts[0]
    out_action = parts[1]
    out_book_id_or_isbn = parts[2] if len(parts) > 2 else None
    out_extra = parts[3] if len(parts) > 3 else None 
    return is_accept, is_reject, out_student, out_action, out_book_id_or_isbn, out_extra


def main():
    if RANDOM_SEED is not None:
        random.seed(RANDOM_SEED)

    global errors
    num_test_cases = int(input("输入测试用例数量: "))
    num_commands_per_case = int(input("输入每个测试用例的指令数量 (不含初始库存): "))

    for dirname in ["data", "output", "logs"]:
        if not os.path.exists(dirname):
            os.makedirs(dirname)

    for i in range(1, num_test_cases + 1):
        print(f"\n--- 测试用例 {i} ---")
        errors.clear()
        state = LibraryState()
        
        testcase_filepath = os.path.join("data", f"testcase_{i}.txt")
        output_filepath = os.path.join("output", f"output_{i}.txt")
        log_filepath = os.path.join("logs", f"log_{i}.txt")

        all_outputs_this_case = [] 

        with open(testcase_filepath, "w", encoding='utf-8') as f_testcase:
            initial_inventory_cmds = state.generate_initial_inventory()
            for line in initial_inventory_cmds:
                f_testcase.write(line + "\n")
            f_testcase.flush() 

            stderr_q = queue.Queue()
            process = subprocess.Popen(
                [JAVA_CMD, "-jar", JAR_PATH],
                stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                text=True, bufsize=1, encoding='utf-8'
            )
            stderr_thread = threading.Thread(target=stderr_reader_thread, args=(process.stderr, stderr_q), daemon=True)
            stderr_thread.start()
            
            time.sleep(0.2) 
            if process.poll() is not None:
                err_msg_from_q = []
                try: 
                    while not stderr_q.empty(): err_msg_from_q.append(stderr_q.get_nowait().strip())
                except queue.Empty: pass
                log_error(f"JAR 进程在发送任何初始库存前已终止. Exit code: {process.returncode}", output="\n".join(err_msg_from_q))
                continue 

            inventory_send_ok = True
            for line_idx, line in enumerate(initial_inventory_cmds):
                if process.poll() is not None:
                    log_error(f"JAR 进程在发送初始库存第 {line_idx+1} 行前已终止.", output=f"Exit code: {process.returncode}")
                    inventory_send_ok = False; break
                try:
                    process.stdin.write(line + "\n"); process.stdin.flush()
                except OSError as e:
                    log_error(f"发送初始库存第 {line_idx+1} 行时发生OSError: {e}", output=f"Exit code: {process.poll()}")
                    inventory_send_ok = False; break
            
            if not inventory_send_ok: continue 

            for cmd_num in range(num_commands_per_case):
                if process.poll() is not None:
                    log_error(f"JAR进程在指令 {cmd_num+1} 前意外终止. Exit code: {process.returncode}")
                    break
                
                cmd_str = generate_next_command_str(state)
                if not cmd_str : continue 
                f_testcase.write(cmd_str + "\n"); f_testcase.flush() 

                try:
                    process.stdin.write(cmd_str + "\n"); process.stdin.flush()
                except OSError as e: 
                    log_error(f"发送指令 '{cmd_str}' 时发生OSError: {e}", output=f"JAR Exit code: {process.poll()}")
                    break

                current_cmd_output_lines = []
                first_line_out = process.stdout.readline().strip()
                if not first_line_out:
                     log_error("JAR对指令无即时输出 (严格模式下视为错误)", cmd_str) 
                     time.sleep(0.1) 
                     if process.poll() is not None : break 
                     first_line_out = process.stdout.readline().strip()
                     if not first_line_out: 
                         err_from_q = []
                         try:
                             while not stderr_q.empty(): err_from_q.append(stderr_q.get_nowait().strip())
                         except queue.Empty: pass
                         if err_from_q : log_error("JAR无stdout但有stderr输出 (指令: "+cmd_str+")", output="\n".join(err_from_q))
                         continue 

                current_cmd_output_lines.append(first_line_out)
                
                _, parsed_cmd_main_actor_or_type, parsed_cmd_action, _, _ = parse_command_from_line(cmd_str)
                
                if parsed_cmd_main_actor_or_type in ["OPEN", "CLOSE"] and first_line_out.isdigit():
                    try: 
                        num_extra = int(first_line_out)
                        for _ in range(num_extra):
                            line = process.stdout.readline().strip()
                            if line: current_cmd_output_lines.append(line) 
                            else: log_error("整理流程报告条数与实际输出不符 (提前结束)", cmd_str, current_cmd_output_lines); break
                    except ValueError:
                        log_error(f"整理流程首行期望数字但得到: {first_line_out}", cmd_str, current_cmd_output_lines)

                elif parsed_cmd_action == "queried" and parsed_cmd_main_actor_or_type is not None and "moving trace:" in first_line_out : 
                    try:
                        num_extra = int(first_line_out.split(":")[-1].strip())
                        for _ in range(num_extra):
                            line = process.stdout.readline().strip()
                            if line: current_cmd_output_lines.append(line) 
                            else: log_error("轨迹查询报告条数与实际输出不符 (提前结束)", cmd_str, current_cmd_output_lines); break
                    except: log_error("解析轨迹查询条数失败", cmd_str, first_line_out)
                
                all_outputs_this_case.extend(current_cmd_output_lines)

                _, cmd_actor, cmd_action, cmd_book_ident, cmd_is_book_id = parse_command_from_line(cmd_str)

                if cmd_actor not in ["OPEN", "CLOSE"]: 
                     current_cmd_date = parse_date_from_command_line(cmd_str)
                     if current_cmd_date: state._update_current_date(current_cmd_date)


                if cmd_actor == "OPEN": state.process_open_event(cmd_str, current_cmd_output_lines)
                elif cmd_actor == "CLOSE": state.process_close_event(cmd_str, current_cmd_output_lines)
                else: 
                    is_acc, is_rej, out_s, out_a, out_b_or_i, out_e = parse_program_output_for_main_info(first_line_out)
                    
                    if not (is_acc or is_rej) and cmd_action != "queried": 
                        log_error(f"学生指令输出非accept/reject且非queried: {first_line_out}", cmd_str)
                        continue

                    if (is_acc or is_rej) and out_s != cmd_actor:
                        log_error(f"输出学号({out_s})与指令({cmd_actor})不符", cmd_str, first_line_out)
                    
                    if cmd_action == "borrowed":
                        can_op, reason = state.pre_check_borrow(cmd_actor, cmd_book_ident) 
                        if is_acc:
                            if not can_op: log_error(f"程序接受不应成功的借阅: {reason}", cmd_str, first_line_out)
                            state.post_check_borrow_accept(cmd_str, cmd_actor, cmd_book_ident, out_b_or_i) 
                        elif is_rej and can_op: log_error(f"程序拒绝Checker认为可成功的借阅: {reason}", cmd_str, first_line_out)
                    
                    elif cmd_action == "returned":
                        can_op, reason = state.pre_check_return(cmd_actor, cmd_book_ident) 
                        if is_acc:
                            if not can_op: log_error(f"程序接受不应成功的还书: {reason}", cmd_str, first_line_out)
                            state.post_check_return_accept(cmd_str, cmd_actor, cmd_book_ident, out_e) 
                        elif is_rej : log_error(f"程序拒绝还书 (应总成功): {reason}", cmd_str, first_line_out)

                    elif cmd_action == "ordered":
                        can_op, reason = state.pre_check_order(cmd_actor, cmd_book_ident) 
                        if is_acc:
                            if not can_op: log_error(f"程序接受不应成功的预约: {reason}", cmd_str, first_line_out)
                            state.post_check_order_accept(cmd_str, cmd_actor, cmd_book_ident)
                        elif is_rej and can_op: log_error(f"程序拒绝Checker认为可成功的预约: {reason}", cmd_str, first_line_out)

                    elif cmd_action == "picked": 
                        can_op, reason = state.pre_check_pick(cmd_actor, cmd_book_ident) 
                        if is_acc:
                            if not can_op: log_error(f"程序接受不应成功的取书: {reason}", cmd_str, first_line_out)
                            state.post_check_pick_accept(cmd_str, cmd_actor, cmd_book_ident, out_b_or_i) 
                        elif is_rej and can_op: log_error(f"程序拒绝Checker认为可成功的取书: {reason}", cmd_str, first_line_out)
                    
                    elif cmd_action == "read":
                        can_op, reason = state.pre_check_read(cmd_actor, cmd_book_ident) 
                        if is_acc:
                            if not can_op: log_error(f"程序接受不应成功的阅读: {reason}", cmd_str, first_line_out)
                            state.post_check_read_accept(cmd_str, cmd_actor, cmd_book_ident, out_b_or_i) 
                        elif is_rej and can_op: log_error(f"程序拒绝Checker认为可成功的阅读: {reason}", cmd_str, first_line_out)

                    elif cmd_action == "restored":
                        can_op, reason = state.pre_check_restore(cmd_actor, cmd_book_ident) 
                        if is_acc:
                            if not can_op: log_error(f"程序接受不应成功的阅读归还: {reason}", cmd_str, first_line_out)
                            state.post_check_restore_accept(cmd_str, cmd_actor, cmd_book_ident)
                        elif is_rej : log_error(f"程序拒绝阅读归还 (应总成功): {reason}", cmd_str, first_line_out)

                    elif cmd_action == "queried":
                        if cmd_book_ident == "credit score":
                            match_credit_q = re.match(r"\[\d{4}-\d{2}-\d{2}\]\s+(\d+)\s+(\d+)", first_line_out) 
                            if match_credit_q:
                                q_stud_id, q_credit_val_str = match_credit_q.groups()
                                if q_stud_id != cmd_actor: log_error(f"信用查询输出学号({q_stud_id})与指令({cmd_actor})不符", cmd_str, first_line_out)
                                state.post_check_queried_credit(cmd_str, cmd_actor, q_credit_val_str)
                            else: log_error(f"信用查询输出格式错误: {first_line_out}", cmd_str)
                        else: 
                            state.post_check_queried_trace(cmd_str, cmd_book_ident, current_cmd_output_lines)
                
                try: 
                    while not stderr_q.empty():
                        err_line = stderr_q.get_nowait()
                        log_error(f"JAR Stderr: {err_line.strip()}", cmd_str)
                except queue.Empty: pass
            
            if process.poll() is None and state.library_is_open: 
                final_close_cmd = f"[{format_date(state.current_date)}] CLOSE"
                f_testcase.write(final_close_cmd + "\n"); f_testcase.flush() 
                try: process.stdin.write(final_close_cmd + "\n"); process.stdin.flush()
                except OSError: pass 

                final_close_outputs = []
                fline = process.stdout.readline().strip()
                if fline:
                    final_close_outputs.append(fline)
                    if fline.isdigit():
                        try: 
                            num_m = int(fline)
                            for _ in range(num_m):
                                mline = process.stdout.readline().strip()
                                if mline: final_close_outputs.append(mline)
                                else: break
                        except ValueError:
                            log_error(f"最终CLOSE指令后期望数字但得到: {fline}", final_close_cmd)
                all_outputs_this_case.extend(final_close_outputs)
                if final_close_outputs : 
                    state.process_close_event(final_close_cmd, final_close_outputs)

            if process.poll() is None:
                try: process.stdin.close() 
                except OSError: pass 
            
            stdout_rem, stderr_rem_communicate = "", ""
            try:
                stdout_rem, stderr_rem_communicate = process.communicate(timeout=10) 
            except subprocess.TimeoutExpired:
                log_error(f"等待 JAR 进程结束超时，将强制终止 (communicate)") 
                process.kill()
                try:
                    stdout_rem_kill, stderr_rem_communicate_kill = process.communicate(timeout=1)
                    if stdout_rem_kill: stdout_rem += stdout_rem_kill
                    if stderr_rem_communicate_kill : stderr_rem_communicate += stderr_rem_communicate_kill
                except: pass 
            except ValueError: pass
            except Exception as e: log_error(f"调用 process.communicate() 时发生未知错误: {e}")

            if stdout_rem: all_outputs_this_case.extend(stdout_rem.strip().split('\n'))
            if stderr_rem_communicate: log_error(f"JAR Stderr (communicate): {stderr_rem_communicate.strip()}")
            
            stderr_thread.join(timeout=0.5) 
            try:
                while not stderr_q.empty(): 
                    err_line = stderr_q.get_nowait()
                    log_error(f"JAR Stderr (final queue clear): {err_line.strip()}")
            except queue.Empty: pass
            except Exception as e: print(f"清空stderr队列时出错: {e}")

        with open(output_filepath, "w", encoding='utf-8') as f_output:
            for line in all_outputs_this_case: f_output.write(line + "\n")
        
        log_summary = f"Test Case {i}: Errors: {len(errors)}" 
        with open(log_filepath, "w", encoding='utf-8') as f_log:
            f_log.write(log_summary + "\n\n")
            if errors: f_log.write("--- ERRORS ---\n" + "\n\n".join(errors) + "\n")
            if not errors:
                 f_log.write("No errors detected for this test case.\n")

        print(log_summary)

    print("\n所有测试用例执行完毕。")

if __name__ == "__main__":
    main()