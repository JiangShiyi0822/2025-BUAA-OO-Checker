import random
import datetime
import subprocess
import os
import re
import time

# --- 配置常量 ---
JAVA_COMMAND = 'java'
MAIN_JAR_FILE = 'plh.jar' 
MAX_COMMANDS_PER_DAY_SIMULATION = 10 
STUDENT_ID_POOL_COUNT = 10
MAX_BOOK_UID_PER_TYPE = 5 
MAX_COPIES_PER_BOOK_ISBN = 3
DAYS_TO_ADVANCE_MIN = 0 
DAYS_TO_ADVANCE_MAX = 3 # Max days to advance after a day is full
DAYS_TO_SKIP_FOR_CLOSED_DAY_MIN = 1 
DAYS_TO_SKIP_FOR_CLOSED_DAY_MAX = 5 
PROBABILITY_TO_SKIP_DAYS = 0.20 
APPOINTMENT_RESERVATION_DAYS = 5 

# --- 辅助类：BookCopy ---
class BookCopy:
    def __init__(self, type_char, uid_str, copy_id_str):
        self.type = type_char
        self.uid = uid_str
        self.copy_id_int = int(copy_id_str)
        self.copy_id_str = copy_id_str
        self.isbn = f"{self.type}-{self.uid}"
        self.full_id = f"{self.isbn}-{self.copy_id_str}"
        self.current_location = "bs" 
        self.reserved_for_student = None 
        self.reservation_arrival_date = None 
        self.is_on_hot_shelf_according_to_program = False 
        self.last_moved_date = None 
        self.trace_history = [] 

    def __repr__(self):
        return self.full_id

    def __eq__(self, other):
        if isinstance(other, BookCopy):
            return self.full_id == other.full_id
        return False

    def __hash__(self):
        return hash(self.full_id)

    def move_to(self, new_location, date, student_id_for_ao=None, from_program_output=False):
        if self.current_location != new_location and from_program_output:
            self.trace_history.append((date, self.current_location, new_location))
        old_location = self.current_location
        self.current_location = new_location
        self.last_moved_date = date
        if new_location == "ao":
            self.reserved_for_student = student_id_for_ao
            if from_program_output: self.reservation_arrival_date = date
        elif old_location == "ao" and new_location != "ao": 
            self.reserved_for_student = None
        if new_location == "hbs": self.is_on_hot_shelf_according_to_program = True
        elif new_location == "bs": self.is_on_hot_shelf_according_to_program = False

# --- 工具函数 ---
def generate_unique_student_id(existing_ids_set):
    while True:
        sid = str(random.randint(23300000, 23399999))
        if sid not in existing_ids_set: existing_ids_set.add(sid); return sid

def generate_book_isbn_details_smarter(existing_isbns_by_type_map, current_isbn_counts_by_type):
    possible_types = ['A', 'B', 'C']
    random.shuffle(possible_types)
    for book_type_attempt in possible_types:
        if current_isbn_counts_by_type.get(book_type_attempt, 0) < MAX_BOOK_UID_PER_TYPE:
            attempts_for_this_type = 0
            while True:
                attempts_for_this_type += 1
                if attempts_for_this_type > MAX_BOOK_UID_PER_TYPE * 3: break
                uid = f"{random.randint(0, MAX_BOOK_UID_PER_TYPE - 1):04d}"
                isbn = f"{book_type_attempt}-{uid}"
                if book_type_attempt not in existing_isbns_by_type_map: existing_isbns_by_type_map[book_type_attempt] = set()
                if isbn not in existing_isbns_by_type_map[book_type_attempt]:
                    existing_isbns_by_type_map[book_type_attempt].add(isbn); return book_type_attempt, uid, isbn
    raise Exception("无法生成新的唯一ISBN，所有书籍类型可能均已达到其UID上限。")

def read_java_program_response(stdout_pipe, output_file_stream):
    response_lines_read = []
    first_line = stdout_pipe.readline().strip()
    if not first_line: return []
    response_lines_read.append(first_line); output_file_stream.write(first_line + "\n")
    lines_to_read_more = 0
    if re.match(r"^\d+$", first_line):
        try: lines_to_read_more = int(first_line)
        except ValueError: pass
    else:
        trace_match = re.search(r"moving trace: (\d+)", first_line)
        if trace_match:
            try: lines_to_read_more = int(trace_match.group(1))
            except ValueError: pass
    if lines_to_read_more > 0:
        for _ in range(lines_to_read_more):
            line = stdout_pipe.readline().strip()
            if not line: break
            response_lines_read.append(line); output_file_stream.write(line + "\n")
    output_file_stream.flush(); return response_lines_read

# --- TestCaseVerifier 类 ---
class TestCaseVerifier:
    def __init__(self, case_idx, all_students_list, initial_book_copies_map, master_inventory_details):
        self.case_idx = case_idx
        self.errors = []
        self.current_date = datetime.date(2025, 1, 1)
        self.is_library_open = False
        self.all_students = set(all_students_list)
        self.book_copies = initial_book_copies_map 
        self.master_inventory = master_inventory_details 
        self.student_borrowed_books = {sid: {} for sid in self.all_students}
        self.student_ordered_books = {sid: {} for sid in self.all_students} 
        self.student_reading_books = {sid: {} for sid in self.all_students} 
        self.student_has_read_today_unreturned = {sid: False for sid in self.all_students}
        self.isbn_became_hot_candidate_this_round = set() 
        self.last_open_date_for_hot_tracking = None

    def add_error(self, message, command_str=""):
        prefix = f"[{self.current_date.strftime('%Y-%m-%d')}]"
        if command_str:
            actual_cmd_part = command_str.split("]", 1)[1].strip() if "]" in command_str else command_str
            prefix += f" (指令: {actual_cmd_part})"
        self.errors.append(f"{prefix} {message}")

    def update_date(self, new_date):
        if new_date > self.current_date:
            for sid in self.all_students: 
                self.student_has_read_today_unreturned[sid] = False
                if sid in self.student_reading_books:
                    self.student_reading_books[sid].clear() 
        self.current_date = new_date

    def _get_book_copy_on_shelf_by_isbn(self, isbn_to_find):
        shelf_books = [b for b in self.book_copies.values() if b.isbn == isbn_to_find and b.current_location in ["bs", "hbs"]]
        if not shelf_books: return None
        bs_books = [b for b in shelf_books if b.current_location == "bs"]
        if bs_books: return random.choice(bs_books)
        return random.choice(shelf_books)

    def _get_book_at_ao_for_student(self, student_id, isbn_to_find):
        for book in self.book_copies.values():
            if book.isbn == isbn_to_find and book.current_location == "ao" and book.reserved_for_student == student_id:
                if book.reservation_arrival_date:
                    if (self.current_date - book.reservation_arrival_date).days >= APPOINTMENT_RESERVATION_DAYS: continue 
                return book 
        return None

    def verify_open_moves(self, move_lines, command_str="OPEN"):
        hot_isbns_from_last_round = set(self.isbn_became_hot_candidate_this_round)
        self.isbn_became_hot_candidate_this_round.clear()
        for move_str in move_lines:
            match_ao_to_other = re.match(r"\[[\d-]+\] move ([\w\d-]+-[\w\d]+-[\w\d]+) from ao to (\w+)(?: for ([\d]+))?", move_str)
            match_to_ao = re.match(r"\[[\d-]+\] move ([\w\d-]+-[\w\d]+-[\w\d]+) from (\w+) to ao for ([\d]+)", move_str)
            match_other_moves = re.match(r"\[[\d-]+\] move ([\w\d-]+-[\w\d]+-[\w\d]+) from (\w+) to (\w+)", move_str)
            book_id, from_loc, to_loc, student_for_ao_in_move = None, None, None, None
            if match_ao_to_other: book_id, from_loc, to_loc = match_ao_to_other.group(1), "ao", match_ao_to_other.group(2)
            elif match_to_ao: book_id,from_loc,to_loc,student_for_ao_in_move = match_to_ao.group(1),match_to_ao.group(2),"ao",match_to_ao.group(3)
            elif match_other_moves: book_id,from_loc,to_loc = match_other_moves.group(1),match_other_moves.group(2),match_other_moves.group(3)
            if not book_id or book_id not in self.book_copies:
                self.add_error(f"OPEN整理: move指令中书号 {book_id} 无效。指令: {move_str}", command_str); continue
            book_obj = self.book_copies[book_id]
            original_location_was_ao = (book_obj.current_location == "ao")
            original_reserved_student_for_book = book_obj.reserved_for_student
            original_isbn_of_book = book_obj.isbn
            book_obj.move_to(to_loc, self.current_date, student_for_ao_in_move, from_program_output=True)
            if original_location_was_ao and to_loc != "ao" and original_reserved_student_for_book:
                if original_reserved_student_for_book in self.student_ordered_books and \
                   original_isbn_of_book in self.student_ordered_books[original_reserved_student_for_book]:
                    order_details = self.student_ordered_books[original_reserved_student_for_book][original_isbn_of_book]
                    if order_details.get("ao_book_copy_id") == book_id or not order_details.get("ao_book_copy_id"):
                        del self.student_ordered_books[original_reserved_student_for_book][original_isbn_of_book]
                        if not self.student_ordered_books[original_reserved_student_for_book]: del self.student_ordered_books[original_reserved_student_for_book]
            if to_loc == "ao" and student_for_ao_in_move:
                if student_for_ao_in_move in self.student_ordered_books and book_obj.isbn in self.student_ordered_books[student_for_ao_in_move]:
                    self.student_ordered_books[student_for_ao_in_move][book_obj.isbn]["ao_book_copy_id"] = book_obj.full_id
        
        for book_id, book in self.book_copies.items(): 
            if book.current_location == "bro": self.add_error(f"OPEN整理后: 书籍 {book.full_id} 仍在借还处(bro)。", command_str)
            if book.current_location == "rr": self.add_error(f"OPEN整理后: 书籍 {book.full_id} 仍在阅览室(rr)。这是不允许的。", command_str) 
            is_isbn_supposed_to_be_hot_now = book.isbn in hot_isbns_from_last_round
            if book.current_location=="hbs" and not is_isbn_supposed_to_be_hot_now: self.add_error(f"OPEN整理后: 非热门ISBN {book.isbn} 副本 {book.full_id} 在热门书架(hbs)。", command_str)
            if book.current_location=="bs" and is_isbn_supposed_to_be_hot_now: self.add_error(f"OPEN整理后: 热门ISBN {book.isbn} 副本 {book.full_id} 在普通书架(bs)。", command_str)
            if book.current_location == "ao" and book.reservation_arrival_date:
                days_held = (self.current_date - book.reservation_arrival_date).days
                if days_held >= APPOINTMENT_RESERVATION_DAYS: 
                    self.add_error(f"OPEN整理后: 书籍 {book.full_id} 在预约处(ao)且已逾期 (送达日 {book.reservation_arrival_date}, 当前日 {self.current_date}, 已持有 {days_held} 天, 阈值 {APPOINTMENT_RESERVATION_DAYS} 天)。应已被移走。", command_str)

    def verify_close_moves(self, move_lines, command_str="CLOSE"):
        for move_str in move_lines:
            match = re.match(r"\[[\d-]+\] move ([\w\d-]+-[\w\d]+-[\w\d]+) from (\w+) to (\w+)", move_str)
            if match:
                book_id, from_loc, to_loc = match.group(1), match.group(2), match.group(3)
                if book_id in self.book_copies:
                    book_obj = self.book_copies[book_id]
                    original_book_location = book_obj.current_location 
                    book_obj.move_to(to_loc, self.current_date, from_program_output=True) 
                    if original_book_location == "rr" and from_loc == "rr": 
                        for sid, reading_map in self.student_reading_books.items():
                            if book_id in reading_map:
                                del self.student_reading_books[sid][book_id]; self.student_has_read_today_unreturned[sid] = False 
                                break 
                else: self.add_error(f"CLOSE整理: move指令中书号 {book_id} 无效。", command_str)

    def verify_ordered(self, student_id, isbn_str, response_lines, is_accepted, command_str):
        book_details = self.master_inventory.get(isbn_str)
        if not book_details: self.add_error(f"ordered: 请求预约不存在的ISBN {isbn_str}。", command_str); return
        book_type = book_details["type"]
        should_reject = False; reject_reason = ""
        if book_type == 'A': should_reject = True; reject_reason = "A类书不可预约"
        if not should_reject and student_id in self.student_ordered_books:
            has_active_existing_reservation = False
            if self.student_ordered_books[student_id]: 
                for existing_isbn, details in self.student_ordered_books[student_id].items():
                    ao_copy_id = details.get("ao_book_copy_id")
                    if ao_copy_id: 
                        if ao_copy_id in self.book_copies:
                            ao_book_obj = self.book_copies[ao_copy_id]
                            if ao_book_obj.current_location == "ao" and ao_book_obj.reserved_for_student == student_id:
                                if ao_book_obj.reservation_arrival_date and (self.current_date - ao_book_obj.reservation_arrival_date).days < APPOINTMENT_RESERVATION_DAYS:
                                    has_active_existing_reservation = True; reject_reason = f"学生已有活跃预约({existing_isbn} 在AO且未逾期)未取书"; break
                    else: has_active_existing_reservation = True; reject_reason = f"学生已有预约({existing_isbn})但书未到AO"; break
            if has_active_existing_reservation: should_reject = True 
        if not should_reject:
            num_b_held = sum(1 for b in self.student_borrowed_books[student_id].values() if b.type == 'B')
            if book_type == 'B' and num_b_held > 0: should_reject = True; reject_reason = "学生已持有B类书，不可预约B类"
            elif book_type == 'C' and any(b.isbn == isbn_str for b in self.student_borrowed_books[student_id].values()):
                should_reject = True; reject_reason = f"学生已持有同ISBN {isbn_str} 的C类书，不可预约"
        if should_reject:
            if is_accepted: self.add_error(f"ordered: 请求应被拒绝({reject_reason})，但程序接受了。新预约ISBN:{isbn_str}", command_str)
        else: 
            if not is_accepted: pass
            else:
                if student_id not in self.student_ordered_books: self.student_ordered_books[student_id] = {}
                self.student_ordered_books[student_id][isbn_str] = {"order_date": self.current_date, "ao_book_copy_id": None}

    def verify_borrowed(self, student_id, isbn_str, response_lines, is_accepted, accepted_book_id_str, command_str):
        book_details = self.master_inventory.get(isbn_str)
        if not book_details: self.add_error(f"borrowed: 请求借阅不存在的ISBN {isbn_str}。", command_str); return
        book_type = book_details["type"]
        should_reject = False; reject_reason = ""
        if book_type == 'A': should_reject = True; reject_reason = "A类书不可借阅"
        if not should_reject:
            book_on_shelf = self._get_book_copy_on_shelf_by_isbn(isbn_str)
            if not book_on_shelf: should_reject = True; reject_reason = f"书架无此ISBN {isbn_str} 的余本"
        if not should_reject:
            num_b_held = sum(1 for b in self.student_borrowed_books[student_id].values() if b.type == 'B')
            if book_type == 'B' and num_b_held > 0: should_reject = True; reject_reason = "学生已持有B类书"
            elif book_type == 'C' and any(b.isbn == isbn_str for b in self.student_borrowed_books[student_id].values()):
                should_reject = True; reject_reason = f"学生已持有同ISBN {isbn_str} 的C类书"
        if should_reject:
            if is_accepted: self.add_error(f"borrowed: 请求应被拒绝({reject_reason})，但程序接受了。ISBN:{isbn_str}", command_str)
        else:
            if not is_accepted: pass
            else:
                if not accepted_book_id_str or accepted_book_id_str not in self.book_copies:
                    self.add_error(f"borrowed: 接受，但返回副本号 {accepted_book_id_str} 无效。", command_str); return
                accepted_book = self.book_copies[accepted_book_id_str]
                if accepted_book.isbn != isbn_str: self.add_error(f"borrowed: 接受，返回副本 {accepted_book_id_str} ISBN与请求 {isbn_str} 不符。", command_str)
                if accepted_book.current_location not in ["bs", "hbs"]: self.add_error(f"borrowed: 接受副本 {accepted_book_id_str} 原本不在书架(位置:{accepted_book.current_location})。", command_str)
                self.student_borrowed_books[student_id][accepted_book.full_id] = accepted_book
                accepted_book.move_to("user", self.current_date, from_program_output=True)
                self.isbn_became_hot_candidate_this_round.add(accepted_book.isbn)

    def verify_returned(self, student_id, book_id_str, response_lines, is_accepted, command_str):
        if book_id_str not in self.student_borrowed_books[student_id]:
            if is_accepted: self.add_error(f"returned: 学生归还了非其持有的书 {book_id_str}，但被接受。", command_str)
            return
        if not is_accepted: self.add_error(f"returned: 学生归还其持有的书 {book_id_str}，但被拒绝。", command_str)
        else:
            self.student_borrowed_books[student_id].pop(book_id_str)
            self.book_copies[book_id_str].move_to("bro", self.current_date, from_program_output=True)

    def verify_picked(self, student_id, isbn_str, response_lines, is_accepted, accepted_book_id_str, command_str):
        should_reject = False; reject_reason = ""
        active_order_exists = False
        book_at_ao_for_student = None
        if student_id in self.student_ordered_books and isbn_str in self.student_ordered_books[student_id]:
            book_at_ao_for_student = self._get_book_at_ao_for_student(student_id, isbn_str) 
            if book_at_ao_for_student: active_order_exists = True
        if not active_order_exists: should_reject = True; reject_reason = f"学生未预约{isbn_str}或预约的书不在AO/已逾期"
        
        if not should_reject and book_at_ao_for_student: 
            book_to_pick_type = self.master_inventory[book_at_ao_for_student.isbn]["type"]
            num_b_held = sum(1 for b in self.student_borrowed_books[student_id].values() if b.type == 'B')
            if book_to_pick_type == 'B' and num_b_held > 0: should_reject = True; reject_reason = "学生已持有B类书，无法再取B类"
            elif book_to_pick_type == 'C' and any(b.isbn == isbn_str for b in self.student_borrowed_books[student_id].values()):
                should_reject = True; reject_reason = f"学生已持有同ISBN {isbn_str} 的C类书，无法再取"
        
        if should_reject:
            if is_accepted: self.add_error(f"picked: 请求应被拒绝({reject_reason})，但程序接受了。ISBN:{isbn_str}", command_str)
        else: 
            if not is_accepted: pass
            else: 
                if not accepted_book_id_str or accepted_book_id_str not in self.book_copies:
                    self.add_error(f"picked: 接受，但返回副本号 {accepted_book_id_str} 无效。", command_str); return
                picked_book_from_resp = self.book_copies[accepted_book_id_str]
                
                if picked_book_from_resp != book_at_ao_for_student:
                     self.add_error(f"picked: 接受，返回副本 {picked_book_from_resp.full_id} 与预约处指定预留的书({book_at_ao_for_student.full_id if book_at_ao_for_student else '无'})不符。", command_str)

                self.student_borrowed_books[student_id][picked_book_from_resp.full_id] = picked_book_from_resp
                picked_book_from_resp.move_to("user", self.current_date, from_program_output=True)
                if isbn_str in self.student_ordered_books.get(student_id, {}):
                    del self.student_ordered_books[student_id][isbn_str]
                    if not self.student_ordered_books[student_id]: del self.student_ordered_books[student_id]

    def verify_read(self, student_id, isbn_str, response_lines, is_accepted, accepted_book_id_str, command_str):
        should_reject = False; reject_reason = ""
        if self.student_has_read_today_unreturned[student_id]: should_reject = True; reject_reason = "学生当日已阅读未归还"
        book_on_shelf_for_read = None
        if not should_reject:
            book_on_shelf_for_read = self._get_book_copy_on_shelf_by_isbn(isbn_str)
            if not book_on_shelf_for_read: should_reject = True; reject_reason = f"书架无此ISBN {isbn_str} 的余本"
        if should_reject:
            if is_accepted: self.add_error(f"read: 请求应被拒绝({reject_reason})，但程序接受了。ISBN:{isbn_str}", command_str)
        else:
            if not is_accepted: pass
            else:
                if not accepted_book_id_str or accepted_book_id_str not in self.book_copies:
                    self.add_error(f"read: 接受，但返回副本号 {accepted_book_id_str} 无效。", command_str); return
                read_book = self.book_copies[accepted_book_id_str]
                if read_book.isbn != isbn_str: self.add_error(f"read: 接受，返回副本 {accepted_book_id_str} ISBN与请求 {isbn_str} 不符。", command_str)
                if read_book.current_location not in ["bs", "hbs"]: self.add_error(f"read: 接受副本 {accepted_book_id_str} 原本不在书架(位置:{read_book.current_location})。", command_str)
                
                if student_id not in self.student_reading_books: self.student_reading_books[student_id] = {} # Ensure student key exists
                self.student_reading_books[student_id][read_book.full_id] = read_book
                read_book.move_to("rr", self.current_date, from_program_output=True)
                self.student_has_read_today_unreturned[student_id] = True
                self.isbn_became_hot_candidate_this_round.add(read_book.isbn)

    def verify_restored(self, student_id, book_id_str, response_lines, is_accepted, command_str):
        if book_id_str not in self.student_reading_books.get(student_id, {}): 
            if is_accepted: self.add_error(f"restored: 学生归还了非其【当日】正在阅读的书 {book_id_str}，但被接受。", command_str)
            return
        if not is_accepted: self.add_error(f"restored: 学生归还其【当日】阅读的书 {book_id_str}，但被拒绝。", command_str)
        else:
            self.student_reading_books[student_id].pop(book_id_str)
            self.book_copies[book_id_str].move_to("bro", self.current_date, from_program_output=True)
            self.student_has_read_today_unreturned[student_id] = False
            
    def verify_queried(self, student_id, book_id_str, response_lines, command_str):
        if book_id_str not in self.book_copies:
            self.add_error(f"queried: 查询了不存在的书籍副本 {book_id_str}。", command_str); return
        
        if not response_lines or \
           not (("moving trace: " in response_lines[0]) and response_lines[0].split("moving trace: ")[-1].isdigit()):
             self.add_error(f"queried: 书籍 {book_id_str} 的轨迹输出格式不正确 (第一行)。响应: {response_lines[0] if response_lines else '无'}", command_str)
             return
        
        try:
            num_traces_reported = int(response_lines[0].split("moving trace: ")[-1])
            if num_traces_reported != len(response_lines) - 1:
                self.add_error(f"queried: 书籍 {book_id_str} 报告的轨迹条数与实际输出行数不符。报告: {num_traces_reported}, 实际: {len(response_lines)-1}", command_str)
        except Exception as e: 
            self.add_error(f"queried: 书籍 {book_id_str} 的轨迹输出格式数字解析失败。响应: {response_lines[0]}. 错误: {e}", command_str)
            return 

        expected_current_location_for_trace = None 
        for i in range(1, len(response_lines)): 
            trace_line = response_lines[i]
            trace_match = re.match(r"^\d+ \[([\d-]+)\] from (\w+) to (\w+)", trace_line)
            if not trace_match:
                self.add_error(f"queried: 书籍 {book_id_str} 的轨迹 {i} 格式不正确: '{trace_line}'", command_str)
                continue 

            trace_date_str, trace_from_loc, trace_to_loc = trace_match.groups()
            try:
                trace_date = datetime.datetime.strptime(trace_date_str, '%Y-%m-%d').date()
                if trace_date > self.current_date:
                    self.add_error(f"queried: 书籍 {book_id_str} 的轨迹 {i} 日期 ({trace_date_str}) 晚于查询日期 ({self.current_date})。", command_str)
            except ValueError:
                self.add_error(f"queried: 书籍 {book_id_str} 的轨迹 {i} 日期格式不正确: '{trace_date_str}'", command_str)

            if expected_current_location_for_trace is not None:
                if trace_from_loc != expected_current_location_for_trace:
                    self.add_error(f"queried: 书籍 {book_id_str} 的轨迹不连续。轨迹 {i-1} 终点为 '{expected_current_location_for_trace}'，但轨迹 {i} 起点为 '{trace_from_loc}'. 错误行: '{trace_line}'", command_str)
            expected_current_location_for_trace = trace_to_loc


def generate_and_execute_test_case(case_idx, num_user_requests_total):
    print(f"开始生成并验证测试用例 {case_idx}...")
    current_simulated_date_for_init = datetime.date(2025, 1, 1)
    generated_student_ids_for_init = set()
    all_simulated_students_for_init = [generate_unique_student_id(generated_student_ids_for_init) for _ in range(STUDENT_ID_POOL_COUNT)]
    
    master_library_inventory_init = {} 
    all_book_copy_instances_map_init = {}
    
    max_possible_distinct_isbns = 3 * MAX_BOOK_UID_PER_TYPE
    upper_bound_num_isbns = min(MAX_BOOK_UID_PER_TYPE * 2 + 5, max_possible_distinct_isbns)
    lower_bound_num_isbns = max(1, MAX_BOOK_UID_PER_TYPE // 2)
    if lower_bound_num_isbns > upper_bound_num_isbns :
        lower_bound_num_isbns = 1; upper_bound_num_isbns = max(1, upper_bound_num_isbns)

    num_distinct_isbns_planned = random.randint(lower_bound_num_isbns, upper_bound_num_isbns)
    initial_inventory_input_lines = [str(num_distinct_isbns_planned)]
    _temp_existing_isbns_map_init = {}
    generated_isbns_count_init = 0
    isbn_counts_by_type_init = {'A': 0, 'B': 0, 'C': 0}

    while generated_isbns_count_init < num_distinct_isbns_planned:
        try:
            book_type_char, book_uid_str, book_isbn_str = generate_book_isbn_details_smarter(
                _temp_existing_isbns_map_init, isbn_counts_by_type_init)
        except Exception: 
            initial_inventory_input_lines[0] = str(generated_isbns_count_init); break
        num_book_copies = random.randint(1, MAX_COPIES_PER_BOOK_ISBN)
        initial_inventory_input_lines.append(f"{book_isbn_str} {num_book_copies}")
        master_library_inventory_init[book_isbn_str] = {"type":book_type_char,"uid":book_uid_str,"total_copies":num_book_copies}
        for i in range(1, num_book_copies + 1):
            copy_id_str_formatted = f"{i:02d}"
            book_copy_instance = BookCopy(book_type_char, book_uid_str, copy_id_str_formatted)
            book_copy_instance.last_moved_date = current_simulated_date_for_init
            all_book_copy_instances_map_init[book_copy_instance.full_id] = book_copy_instance
        isbn_counts_by_type_init[book_type_char] += 1; generated_isbns_count_init += 1
    
    if generated_isbns_count_init < num_distinct_isbns_planned: 
        initial_inventory_input_lines[0] = str(generated_isbns_count_init)
    if generated_isbns_count_init == 0 and not all_book_copy_instances_map_init: 
        print(f"警告: 测试用例 {case_idx} 未能生成任何初始书籍。")

    verifier = TestCaseVerifier(case_idx, list(all_simulated_students_for_init), 
                                dict(all_book_copy_instances_map_init), 
                                dict(master_library_inventory_init))

    input_data_filename = os.path.join("data", f"testcase_{case_idx}.txt")
    program_output_filename = os.path.join("output", f"output_{case_idx}.txt")
    program_stderr_filename = os.path.join("output", f"stderr_{case_idx}.txt")

    java_process = None 

    try:
        with open(input_data_filename, "w", encoding="utf-8") as f_input_handle, \
             open(program_output_filename, "w", encoding="utf-8") as f_output_handle, \
             open(program_stderr_filename, "w", encoding="utf-8") as f_stderr_handle:
            
            try:
                java_process = subprocess.Popen(
                    [JAVA_COMMAND, '-jar', MAIN_JAR_FILE],
                    stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=f_stderr_handle, 
                    text=True, encoding='utf-8', bufsize=1)
            except Exception as e:
                f_stderr_handle.write(f"启动Java进程Popen失败: {e}\n") 
                verifier.add_error(f"启动Java进程Popen失败: {e}")
                print(f"测试用例 {verifier.case_idx} 结果: 失败 (Java进程启动Popen失败)")
                return

            for line in initial_inventory_input_lines: 
                if java_process.poll() is not None: 
                    verifier.add_error(f"Java进程在发送初始库存前已退出。退出码: {java_process.returncode}")
                    raise IOError("Java process terminated prematurely during initial inventory.")
                f_input_handle.write(line + "\n"); java_process.stdin.write(line + "\n")
            java_process.stdin.flush()
            
            commands_generated_on_current_day = 0
            user_requests_generated_count = 0

            while user_requests_generated_count < num_user_requests_total :
                if java_process.poll() is not None:
                    verifier.add_error(f"Java进程在命令循环开始时已退出。退出码: {java_process.returncode}")
                    raise IOError("Java process terminated prematurely in command loop.")

                if random.random() < PROBABILITY_TO_SKIP_DAYS and \
                   commands_generated_on_current_day == 0 and \
                   not verifier.is_library_open : 
                    days_to_skip = random.randint(DAYS_TO_SKIP_FOR_CLOSED_DAY_MIN, DAYS_TO_SKIP_FOR_CLOSED_DAY_MAX) 
                    new_skipped_date = verifier.current_date + datetime.timedelta(days=days_to_skip)
                    verifier.update_date(new_skipped_date)
                    continue 

                date_str_for_cmd = verifier.current_date.strftime('%Y-%m-%d')

                if not verifier.is_library_open or commands_generated_on_current_day >= MAX_COMMANDS_PER_DAY_SIMULATION:
                    if java_process.poll() is not None: raise IOError("Java process terminated before OPEN/CLOSE.")
                    if verifier.is_library_open: 
                        close_cmd_str = f"[{date_str_for_cmd}] CLOSE"
                        f_input_handle.write(close_cmd_str + "\n"); java_process.stdin.write(close_cmd_str + "\n"); java_process.stdin.flush()
                        resp_close = read_java_program_response(java_process.stdout, f_output_handle)
                        if resp_close and resp_close[0].isdigit(): verifier.verify_close_moves(resp_close[1:1+int(resp_close[0])], close_cmd_str)
                        verifier.is_library_open = False
                    
                    # ** MODIFIED SECTION for date advancement after a day full of commands **
                    if commands_generated_on_current_day >= MAX_COMMANDS_PER_DAY_SIMULATION:
                        # Day ended due to command limit. MUST advance to at least the next day.
                        days_to_advance_after_close = random.randint(max(1, DAYS_TO_ADVANCE_MIN), 
                                                                     max(1, DAYS_TO_ADVANCE_MAX))
                        new_date_after_day_end = verifier.current_date + datetime.timedelta(days=days_to_advance_after_close)
                        verifier.update_date(new_date_after_day_end)
                        date_str_for_cmd = new_date_after_day_end.strftime('%Y-%m-%d')
                    # ** END OF MODIFIED SECTION **
                    
                    if java_process.poll() is not None: raise IOError(f"Java process terminated before OPEN on {date_str_for_cmd}.")
                    open_cmd_str = f"[{date_str_for_cmd}] OPEN"
                    f_input_handle.write(open_cmd_str + "\n"); java_process.stdin.write(open_cmd_str + "\n"); java_process.stdin.flush()
                    resp_open = read_java_program_response(java_process.stdout, f_output_handle)
                    if resp_open and resp_open[0].isdigit(): verifier.verify_open_moves(resp_open[1:1+int(resp_open[0])], open_cmd_str)
                    elif resp_open and not resp_open[0].isdigit(): verifier.add_error(f"OPEN指令后首行输出非数字条数: {resp_open[0]}", open_cmd_str)
                    verifier.is_library_open = True; verifier.last_open_date_for_hot_tracking = verifier.current_date; commands_generated_on_current_day = 0

                generated_command_str_for_java = None; chosen_cmd_type_for_java = None
                target_student_for_cmd = random.choice(list(verifier.all_students))
                cmd_type_candidates = []
                if verifier.student_borrowed_books[target_student_for_cmd]: cmd_type_candidates.append("returned")
                if target_student_for_cmd in verifier.student_ordered_books:
                     for isbn_ordered in verifier.student_ordered_books[target_student_for_cmd]:
                         if verifier._get_book_at_ao_for_student(target_student_for_cmd, isbn_ordered):
                             cmd_type_candidates.append("picked"); break
                if verifier.student_reading_books[target_student_for_cmd]: cmd_type_candidates.append("restored")
                has_books_on_any_shelf = any(b.current_location in ["bs", "hbs"] for b in verifier.book_copies.values())
                if has_books_on_any_shelf: cmd_type_candidates.extend(["borrowed", "read"])
                if verifier.master_inventory: cmd_type_candidates.append("ordered")
                if verifier.book_copies: cmd_type_candidates.append("queried")

                if not cmd_type_candidates:
                    if not verifier.book_copies and not verifier.master_inventory : 
                        if user_requests_generated_count < num_user_requests_total: 
                            print(f"警告: 测试用例 {case_idx} 已无任何书籍或可操作项，但仍需生成指令。提前结束。")
                        user_requests_generated_count = num_user_requests_total 
                    else: commands_generated_on_current_day = MAX_COMMANDS_PER_DAY_SIMULATION 
                    continue 
                
                if random.random() < 0.7 and any(c in cmd_type_candidates for c in ["returned", "picked", "restored"]):
                    dep_cmds = [c for c in ["returned", "picked", "restored"] if c in cmd_type_candidates]; 
                    if dep_cmds: chosen_cmd_type_for_java = random.choice(dep_cmds)
                if not chosen_cmd_type_for_java:
                    basic_cmds = [c for c in ["borrowed", "ordered", "read", "queried"] if c in cmd_type_candidates]
                    if basic_cmds: chosen_cmd_type_for_java = random.choice(basic_cmds)
                    else: commands_generated_on_current_day = MAX_COMMANDS_PER_DAY_SIMULATION; continue
                
                if chosen_cmd_type_for_java == "queried":
                    if verifier.book_copies: book_to_query = random.choice(list(verifier.book_copies.values())); generated_command_str_for_java = f"[{date_str_for_cmd}] {target_student_for_cmd} queried {book_to_query.full_id}"
                elif chosen_cmd_type_for_java == "borrowed":
                    shelf_books_b_c = [b for b in verifier.book_copies.values() if b.current_location in ["bs", "hbs"] and verifier.master_inventory.get(b.isbn, {}).get("type") in ['B','C']]
                    if shelf_books_b_c: isbn_to_borrow = random.choice(list(set(b.isbn for b in shelf_books_b_c))); generated_command_str_for_java = f"[{date_str_for_cmd}] {target_student_for_cmd} borrowed {isbn_to_borrow}"
                elif chosen_cmd_type_for_java == "ordered":
                    orderable_isbns = [isbn for isbn, details in verifier.master_inventory.items() if details["type"] in ['B','C']]
                    if orderable_isbns: generated_command_str_for_java = f"[{date_str_for_cmd}] {target_student_for_cmd} ordered {random.choice(orderable_isbns)}"
                elif chosen_cmd_type_for_java == "returned": 
                    if verifier.student_borrowed_books[target_student_for_cmd]: 
                        book_id_to_return = random.choice(list(verifier.student_borrowed_books[target_student_for_cmd].keys()))
                        generated_command_str_for_java = f"[{date_str_for_cmd}] {target_student_for_cmd} returned {book_id_to_return}"
                elif chosen_cmd_type_for_java == "picked":
                    eligible_for_pick = []
                    if target_student_for_cmd in verifier.student_ordered_books:
                        for isbn in verifier.student_ordered_books[target_student_for_cmd]:
                            if verifier._get_book_at_ao_for_student(target_student_for_cmd, isbn):
                                 eligible_for_pick.append(isbn)
                    if eligible_for_pick: generated_command_str_for_java = f"[{date_str_for_cmd}] {target_student_for_cmd} picked {random.choice(eligible_for_pick)}"
                elif chosen_cmd_type_for_java == "read":
                    shelf_books_any_type = [b for b in verifier.book_copies.values() if b.current_location in ["bs", "hbs"]]
                    if shelf_books_any_type: isbn_to_read = random.choice(list(set(b.isbn for b in shelf_books_any_type))); generated_command_str_for_java = f"[{date_str_for_cmd}] {target_student_for_cmd} read {isbn_to_read}"
                elif chosen_cmd_type_for_java == "restored":
                    if verifier.student_reading_books[target_student_for_cmd]: 
                        book_id_to_restore = random.choice(list(verifier.student_reading_books[target_student_for_cmd].keys()))
                        generated_command_str_for_java = f"[{date_str_for_cmd}] {target_student_for_cmd} restored {book_id_to_restore}"

                if not generated_command_str_for_java:
                    if verifier.book_copies and "queried" in cmd_type_candidates : 
                        book_to_query = random.choice(list(verifier.book_copies.values())); generated_command_str_for_java = f"[{date_str_for_cmd}] {target_student_for_cmd} queried {book_to_query.full_id}"; chosen_cmd_type_for_java = "queried" 
                    else: commands_generated_on_current_day = MAX_COMMANDS_PER_DAY_SIMULATION; continue
                
                if java_process.poll() is not None: 
                    verifier.add_error(f"Java进程在发送用户指令 '{generated_command_str_for_java.split(']',1)[1].strip()}' 前已意外退出。退出码: {java_process.returncode}", generated_command_str_for_java)
                    raise IOError("Java process terminated before user command write.")

                f_input_handle.write(generated_command_str_for_java + "\n"); java_process.stdin.write(generated_command_str_for_java + "\n"); java_process.stdin.flush()
                response_from_java = read_java_program_response(java_process.stdout, f_output_handle)
                commands_generated_on_current_day +=1; user_requests_generated_count +=1 

                if response_from_java:
                    first_resp_line = response_from_java[0]; is_accepted_response = "[accept]" in first_resp_line
                    cmd_parts = generated_command_str_for_java.split(" "); req_student_id, req_action, req_book_identity = cmd_parts[1], cmd_parts[2], cmd_parts[3]
                    accepted_book_id_from_resp = None
                    if is_accepted_response and req_action in ["borrowed", "read", "picked"]:
                        match_accept_detail = re.match(r"\[[\d-]+\] \[accept\] [\d]+ \w+ ([\w\d-]+-[\w\d]+-[\w\d]+)", first_resp_line)
                        if match_accept_detail: accepted_book_id_from_resp = match_accept_detail.group(1)
                    
                    if req_action == "borrowed": verifier.verify_borrowed(req_student_id, req_book_identity, response_from_java, is_accepted_response, accepted_book_id_from_resp, generated_command_str_for_java)
                    elif req_action == "returned": verifier.verify_returned(req_student_id, req_book_identity, response_from_java, is_accepted_response, generated_command_str_for_java)
                    elif req_action == "ordered": verifier.verify_ordered(req_student_id, req_book_identity, response_from_java, is_accepted_response, generated_command_str_for_java)
                    elif req_action == "picked": verifier.verify_picked(req_student_id, req_book_identity, response_from_java, is_accepted_response, accepted_book_id_from_resp, generated_command_str_for_java)
                    elif req_action == "read": verifier.verify_read(req_student_id, req_book_identity, response_from_java, is_accepted_response, accepted_book_id_from_resp, generated_command_str_for_java)
                    elif req_action == "restored": verifier.verify_restored(req_student_id, req_book_identity, response_from_java, is_accepted_response, generated_command_str_for_java)
                    elif req_action == "queried": verifier.verify_queried(req_student_id, req_book_identity, response_from_java, generated_command_str_for_java)
                else: 
                    verifier.add_error(f"指令后未收到Java程序响应。", generated_command_str_for_java)
                    user_requests_generated_count -=1 
            
            if verifier.is_library_open: 
                final_close_cmd_date_str = verifier.current_date.strftime('%Y-%m-%d')
                final_close_cmd = f"[{final_close_cmd_date_str}] CLOSE"
                if java_process.poll() is None: 
                    f_input_handle.write(final_close_cmd + "\n"); java_process.stdin.write(final_close_cmd + "\n"); java_process.stdin.flush()
                    resp_final_close = read_java_program_response(java_process.stdout, f_output_handle)
                    if resp_final_close and resp_final_close[0].isdigit(): verifier.verify_close_moves(resp_final_close[1:1+int(resp_final_close[0])], final_close_cmd)
                verifier.is_library_open = False
            
            if java_process.poll() is None: java_process.stdin.close()
            
            stdout_rem, stderr_rem_after_loop = "", "" 
            if java_process.poll() is None: 
                try:
                    stdout_rem, stderr_rem_after_loop = java_process.communicate(timeout=5) 
                except subprocess.TimeoutExpired:
                    java_process.kill()
                    stdout_rem, stderr_rem_after_loop = java_process.communicate()
                    f_stderr_handle.write("错误: Java程序在最终通信时超时(communicate)，已被终止。\n")
                    verifier.add_error("Java程序在最终通信时超时(communicate)。")
            
            if stdout_rem: f_output_handle.write(stdout_rem)

    except IOError as e: 
        verifier.add_error(f"IO错误，与Java进程的通信中断: {e}")
        print(f"测试用例 {verifier.case_idx} 中发生IO错误: {e}。检查stderr文件。")
    except Exception as e_outer: 
        verifier.add_error(f"Checker发生意外错误: {e_outer}")
        print(f"测试用例 {verifier.case_idx} Checker发生意外错误: {e_outer}")
        import traceback
        traceback.print_exc(file=f_stderr_handle) 

    finally:
        if java_process and java_process.poll() is None: 
            try:
                if hasattr(java_process, 'stdin') and java_process.stdin and not java_process.stdin.closed: 
                    java_process.stdin.close()
            except: pass 
            try:
                java_process.kill()
                java_process.communicate(timeout=2) 
            except: pass 

        print("-" * 40)
        if not verifier.errors: print(f"测试用例 {verifier.case_idx} 结果: 通过")
        else:
            print(f"测试用例 {verifier.case_idx} 结果: 失败 ({len(verifier.errors)} 个错误)")
            for err_idx, err_msg in enumerate(verifier.errors):
                print(f"  错误 {err_idx+1}: {err_msg}")
                if err_idx >= 19 : print(f"  ... (及其他 {len(verifier.errors) - 20} 个错误)"); break
        print("-" * 40)


if __name__ == "__main__":
    if not os.path.exists("data"): os.makedirs("data")
    if not os.path.exists("output"): os.makedirs("output")
    try:
        num_files = int(input("请输入要生成的测试数据集数量: "))
        num_cmds_per_file_str = input("请输入每个测试文件大约包含的用户请求指令数量: ") 
        if not num_cmds_per_file_str.isdigit() or int(num_cmds_per_file_str) <=0 :
            print("用户请求指令数量必须为正整数。")
        else:
            num_cmds_user_requests = int(num_cmds_per_file_str)
            if num_files <= 0: print("测试数据集数量必须为正整数。")
            else:
                for i in range(1, num_files + 1):
                    generate_and_execute_test_case(i, num_cmds_user_requests)
                print("\n所有测试数据生成和验证完毕。")
    except ValueError: print("输入无效，请输入数字。")
    except Exception as e_main_run: 
        print(f"程序发生意外错误: {e_main_run}")
        import traceback
        traceback.print_exc()