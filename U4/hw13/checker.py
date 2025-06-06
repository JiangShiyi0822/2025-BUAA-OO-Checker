import random
import subprocess
import datetime
import os
import re
import time

# --- 配置 ---
JAR_PATH = "wmt.jar" 
JAVA_EXECUTABLE = "java"
DEBUG_MODE = False 

# --- 辅助类 ---
class Book: # ... (no change)
    def __init__(self, type_char, uid_str, copy_id_str):
        self.type = type_char; self.uid = uid_str; self.copy_id = copy_id_str
    @property
    def isbn_str(self): return f"{self.type}-{self.uid}"
    @property
    def book_id_str(self): return f"{self.type}-{self.uid}-{self.copy_id}"
    def __repr__(self): return f"Book({self.book_id_str})"
    def __eq__(self, other): return isinstance(other, Book) and self.book_id_str == other.book_id_str
    def __hash__(self): return hash(self.book_id_str)

class ReservationInfo: # ... (no change)
    def __init__(self, book_obj, arrival_date, for_student_id, is_from_open_organize):
        self.book = book_obj; self.student_id = for_student_id
        self.arrival_at_ao_date = arrival_date
        if is_from_open_organize: self.first_pickable_day_count_starts = arrival_date
        else: self.first_pickable_day_count_starts = arrival_date + datetime.timedelta(days=1)
        self.last_pickable_date = self.first_pickable_day_count_starts + datetime.timedelta(days=4)
        self.pick_commands_generated_count = 0 
    def is_expired(self, current_query_date): return current_query_date > self.last_pickable_date
    def __repr__(self): return f"ResInfo({self.book.book_id_str} for {self.student_id}, Arr:{self.arrival_at_ao_date}, LastPick:{self.last_pickable_date}, PicksGen:{self.pick_commands_generated_count})"

class LibraryState:
    def __init__(self):
        self.current_date = datetime.date(2025, 1, 1)
        self.is_logically_open = False 
        self.last_event_was_close = False 
        self.all_books_details = {}
        self.books_on_shelf = {} 
        self.books_at_bro = set()
        self.books_at_ao = set() 
        self.reservations_at_ao = {}
        self.user_holds = {} 
        self.user_pending_order_intents = {} 
        self.student_ids = [f"2337{i:04d}" for i in range(1, 21)]

    def add_book_to_system(self, book_obj): # ... (no change)
        self.all_books_details[book_obj.book_id_str] = book_obj
        if book_obj.isbn_str not in self.books_on_shelf: self.books_on_shelf[book_obj.isbn_str] = set()
        self.books_on_shelf[book_obj.isbn_str].add(book_obj)

    def get_book_by_id_str(self, book_id_str): return self.all_books_details.get(book_id_str) # ... (no change)
    def get_book_by_isbn(self, isbn_str): # ... (no change)
        if isbn_str in self.books_on_shelf and self.books_on_shelf[isbn_str]:
            return next(iter(self.books_on_shelf[isbn_str]))
        for book_obj_detail in self.all_books_details.values():
            if book_obj_detail.isbn_str == isbn_str: return book_obj_detail
        return None
    def is_student_notfetch(self, student_id): return student_id in self.user_pending_order_intents or student_id in self.reservations_at_ao # ... (no change)
    def get_held_book_types_and_isbns(self, student_id): # ... (no change)
        held_b_count = 0; held_c_isbns = set()
        if student_id in self.user_holds:
            for book in self.user_holds[student_id]:
                if book.type == 'B': held_b_count += 1
                elif book.type == 'C': held_c_isbns.add(book.isbn_str)
        return held_b_count, held_c_isbns
    def record_book_arrival_at_ao(self, book_obj, for_student_id, arrival_date, is_arrival_after_open_event): # ... (no change)
        res_info = ReservationInfo(book_obj, arrival_date, for_student_id, is_arrival_after_open_event)
        self.reservations_at_ao[for_student_id] = res_info
        self.books_at_ao.add(book_obj)
        if for_student_id in self.user_pending_order_intents and \
           self.user_pending_order_intents[for_student_id] == book_obj.isbn_str:
            del self.user_pending_order_intents[for_student_id]
    def record_book_picked_from_ao(self, student_id, picked_book_obj): # ... (no change)
        if student_id in self.reservations_at_ao and self.reservations_at_ao[student_id].book == picked_book_obj:
            del self.reservations_at_ao[student_id]
            if picked_book_obj in self.books_at_ao: self.books_at_ao.remove(picked_book_obj)
            return True
        return False

    # NEW: Method for consistency check
    def get_all_book_objects_in_system_from_checker_view(self):
        all_books_found = set()
        for isbn_str_key in self.books_on_shelf: # Iterate keys to avoid issues if set is empty
            all_books_found.update(self.books_on_shelf[isbn_str_key])
        all_books_found.update(self.books_at_bro)
        # books_at_ao is a general set, reservations_at_ao holds specific assignments
        all_books_found.update(self.books_at_ao) # Books generally at AO
        # Ensure books specifically reserved are also covered (they should be in books_at_ao too)
        # for res_info in self.reservations_at_ao.values():
        #     all_books_found.add(res_info.book) # Adding to set handles duplicates
        for user_id_key in self.user_holds: # Iterate keys
            all_books_found.update(self.user_holds[user_id_key])
        return all_books_found

    def check_book_total_consistency(self):
        # This function will use the global check_and_update_logic_error
        books_from_state_view = self.get_all_book_objects_in_system_from_checker_view()
        
        # Check 1: All books in current locations must be known from initialization
        unknown_books_in_state = books_from_state_view - set(self.all_books_details.values())
        if unknown_books_in_state:
            check_and_update_logic_error(True, 
                f"逻辑错误(总量校验): 系统中出现未知书籍: "
                f"{[b.book_id_str for b in list(unknown_books_in_state)[:3]]}")
            return False 

        # Check 2: All initially known books must be found in the current state view
        missing_books_from_init = set(self.all_books_details.values()) - books_from_state_view
        if missing_books_from_init:
            check_and_update_logic_error(True, 
                f"逻辑错误(总量校验): 书籍丢失! 应有 {len(self.all_books_details)}, "
                f"实际定位到 {len(books_from_state_view)}. "
                f"丢失示例: {[b.book_id_str for b in list(missing_books_from_init)[:3]]}")
            return False
        
        # Check 3: Total count must match (covers books appearing multiple times if not handled by set logic, or other discrepancies)
        if len(books_from_state_view) != len(self.all_books_details):
            # This case might be redundant if above checks are comprehensive, but as a fallback
            check_and_update_logic_error(True,
                f"逻辑错误(总量校验): 书籍总数不匹配。初始: {len(self.all_books_details)}, "
                f"当前checker视图中: {len(books_from_state_view)}.")
            return False
        return True


# --- 指令生成逻辑 (generate_return_command_v2, generate_pick_command_v2 - 与上一版本相同) ---
def generate_initial_books(state, max_isbn_types=15, max_uid_val=50): # ... (no change)
    initial_input_lines = []; num_isbn_types = random.randint(5, max_isbn_types)
    initial_input_lines.append(str(num_isbn_types)); generated_isbns = set()
    for _ in range(num_isbn_types):
        while True:
            book_type = random.choice(['A', 'B', 'C']); uid = f"{random.randint(0, max_uid_val):04d}"
            isbn = f"{book_type}-{uid}"
            if isbn not in generated_isbns: generated_isbns.add(isbn); break
        copies = random.randint(1, 10); initial_input_lines.append(f"{isbn} {copies}")
        for i in range(1, copies + 1):
            state.add_book_to_system(Book(book_type, uid, f"{i:02d}"))
    return initial_input_lines
def generate_student_id(state): return random.choice(state.student_ids) # ... (no change)
def generate_borrow_command(state, date_str_formatted): # ... (no change)
    student_id = generate_student_id(state); shelf_isbns = list(state.books_on_shelf.keys()); random.shuffle(shelf_isbns)
    for isbn in shelf_isbns:
        books_on_shelf_for_isbn = state.books_on_shelf.get(isbn)
        if books_on_shelf_for_isbn:
            book_example = next(iter(books_on_shelf_for_isbn))
            if book_example.type in ['B', 'C']:
                held_b_count, held_c_isbns = state.get_held_book_types_and_isbns(student_id)
                can_borrow = (book_example.type == 'B' and held_b_count == 0) or \
                             (book_example.type == 'C' and book_example.isbn_str not in held_c_isbns)
                if can_borrow: return f"[{date_str_formatted}] {student_id} borrowed {isbn}"
    return None
def generate_order_command(state, date_str_formatted): # ... (no change)
    student_id = generate_student_id(state)
    if state.is_student_notfetch(student_id): return None
    all_orderable_isbns = set()
    for isbn_str, books_set in state.books_on_shelf.items():
        if books_set and next(iter(books_set)).type in ['B', 'C']: all_orderable_isbns.add(isbn_str)
    for book_obj in state.books_at_bro:
         if book_obj.type in ['B', 'C']: all_orderable_isbns.add(book_obj.isbn_str)
    if not all_orderable_isbns: return None
    shuffled_isbns = list(all_orderable_isbns); random.shuffle(shuffled_isbns)
    for isbn_to_order in shuffled_isbns:
        book_type_to_order = isbn_to_order[0]
        held_b_count, held_c_isbns = state.get_held_book_types_and_isbns(student_id)
        can_order = (book_type_to_order == 'B' and held_b_count == 0) or \
                    (book_type_to_order == 'C' and isbn_to_order not in held_c_isbns)
        if can_order: return f"[{date_str_formatted}] {student_id} ordered {isbn_to_order}"
    return None
def generate_query_command(state, date_str_formatted): # ... (no change)
    if not state.all_books_details: return None
    return f"[{date_str_formatted}] {generate_student_id(state)} queried {random.choice(list(state.all_books_details.keys()))}"
def generate_return_command_v2(state, date_str_formatted, planned_returns_book_ids_today): # ... (no change)
    eligible_returns = [] 
    for sid, books_held in state.user_holds.items():
        for book in books_held:
            if book.book_id_str not in planned_returns_book_ids_today:
                eligible_returns.append((sid, book))
    if eligible_returns:
        student_id, book_to_return = random.choice(eligible_returns)
        return f"[{date_str_formatted}] {student_id} returned {book_to_return.book_id_str}", book_to_return
    return None, None
def generate_pick_command_v2(state, date_str_formatted, planned_picked_book_objects_today): # ... (no change)
    eligible_picks_info = []
    reservations_items = list(state.reservations_at_ao.items()); random.shuffle(reservations_items)
    for student_id, res_info in reservations_items:
        if res_info.book not in planned_picked_book_objects_today and \
           not res_info.is_expired(state.current_date) and \
           res_info.pick_commands_generated_count < 2:
            book_to_be_picked = res_info.book
            held_b_count, held_c_isbns = state.get_held_book_types_and_isbns(student_id)
            can_actually_pick_now = (book_to_be_picked.type == 'B' and held_b_count == 0) or \
                                    (book_to_be_picked.type == 'C' and book_to_be_picked.isbn_str not in held_c_isbns)
            if can_actually_pick_now: eligible_picks_info.append((student_id, res_info))         
    if eligible_picks_info:
        student_id, chosen_res_info = random.choice(eligible_picks_info)
        chosen_res_info.pick_commands_generated_count += 1 
        return f"[{date_str_formatted}] {student_id} picked {chosen_res_info.book.isbn_str}", chosen_res_info.book
    return None, None

# --- 输出解析逻辑 ---
MOVE_PATTERN = re.compile(r"\[(\d{4}-\d{2}-\d{2})\] move ([\w\d-]+-\d{2}) from (\w+) to (\w+)(?: for (\d+))?")
ACCEPT_REJECT_PATTERN = re.compile(r"\[(\d{4}-\d{2}-\d{2})\] \[(accept|reject)\] (\d+) (queried|borrowed|ordered|returned|picked) ([\w\d-]+(?:-\d{2})?)")
ACCEPT_BORROWED_PICKED_FULL_ID_PATTERN = re.compile(r"\[(\d{4}-\d{2}-\d{2})\] \[accept\] (\d+) (borrowed|picked) ([\w\d-]+)-(\d{2})")
current_test_case_logic_passed = True; current_test_case_logic_error_msg = "" # Global for simplicity
def check_and_update_logic_error(condition, error_msg_on_fail): # ... (no change)
    global current_test_case_logic_passed, current_test_case_logic_error_msg
    if current_test_case_logic_passed and condition:
        current_test_case_logic_passed = False; current_test_case_logic_error_msg = error_msg_on_fail
        if DEBUG_MODE: print(f"  [逻辑校验失败] {error_msg_on_fail}")
ORIG_CMD_PATTERN = re.compile(r"\[\d{4}-\d{2}-\d{2}\] (\d+) (borrowed|ordered|picked|returned|queried) ([\w\d-]+(?:-\d{2})?)") # ... (no change)
def parse_original_command_details(original_command_str): # ... (no change)
    match = ORIG_CMD_PATTERN.match(original_command_str)
    if match: return {'student_id': match.group(1), 'action': match.group(2), 'item_id': match.group(3)}
    return {}

def parse_java_output_line(line, state, current_date_obj, original_command_str=""): # MODIFIED
    global current_test_case_logic_passed, current_test_case_logic_error_msg
    if DEBUG_MODE: print(f"  [调试] 解析JAR输出: {line.strip()} (来自命令: {original_command_str})")
    
    orig_cmd_details = parse_original_command_details(original_command_str)
    action_orig = orig_cmd_details.get('action')
    sid_orig = orig_cmd_details.get('student_id')
    item_id_orig = orig_cmd_details.get('item_id') 

    match_accept_bp_full = ACCEPT_BORROWED_PICKED_FULL_ID_PATTERN.match(line)
    if match_accept_bp_full:
        _date_j, sid_j, act_j, isbn_base_j, cpy_s_j = match_accept_bp_full.groups()
        bid_s_j = f"{isbn_base_j}-{cpy_s_j}"; book_o_j = state.get_book_by_id_str(bid_s_j)

        if not book_o_j:
            check_and_update_logic_error(True, f"逻辑错误(accept_bp): JAR {act_j} accept 输出未知书籍ID {bid_s_j}。")
            return
        if book_o_j.type == 'A': 
            check_and_update_logic_error(True, f"逻辑错误(accept_bp): JAR accept {act_j} A类书籍 {bid_s_j}。")

        student_held_b_count_before, student_held_c_isbns_before = state.get_held_book_types_and_isbns(sid_j)

        if act_j == "borrowed":
            shelf_books_for_isbn = state.books_on_shelf.get(book_o_j.isbn_str, set())
            if book_o_j not in shelf_books_for_isbn: # MODIFIED: Check if specific book_o_j was on shelf
                 check_and_update_logic_error(True, f"逻辑错误(borrow): JAR accept借阅书 {bid_s_j}，但Checker状态显示其不在书架。")
            if book_o_j.type == 'B' and student_held_b_count_before > 0:
                check_and_update_logic_error(True, f"逻辑错误(borrow): JAR accept借阅B类书 {bid_s_j} 给学生 {sid_j} (已持有B)。")
            if book_o_j.type == 'C' and book_o_j.isbn_str in student_held_c_isbns_before:
                check_and_update_logic_error(True, f"逻辑错误(borrow): JAR accept借阅C类书 {bid_s_j} 给学生 {sid_j} (已持有该ISBN)。")
            
            if book_o_j.isbn_str in state.books_on_shelf and book_o_j in state.books_on_shelf.get(book_o_j.isbn_str, set()):
                state.books_on_shelf[book_o_j.isbn_str].remove(book_o_j)
                if not state.books_on_shelf[book_o_j.isbn_str]: del state.books_on_shelf[book_o_j.isbn_str]
            if sid_j not in state.user_holds: state.user_holds[sid_j] = set()
            state.user_holds[sid_j].add(book_o_j)
        
        elif act_j == "picked":
            res_info = state.reservations_at_ao.get(sid_j)
            if not res_info:
                check_and_update_logic_error(True, f"逻辑错误(picked): JAR accept取书 {bid_s_j} 给学生 {sid_j}，但Checker未记录其在AO有任何预约。")
            elif res_info.book != book_o_j: 
                check_and_update_logic_error(True, f"逻辑错误(picked): JAR为学生{sid_j}取的书({bid_s_j})与Checker记录的预约副本({res_info.book.book_id_str})不符。")
            elif res_info.is_expired(current_date_obj): 
                check_and_update_logic_error(True, f"逻辑错误(picked): JAR accept取学生 {sid_j} 的过期书 {bid_s_j} (末次 {res_info.last_pickable_date}, 当前 {current_date_obj})。")
            
            if book_o_j.type == 'B' and student_held_b_count_before > 0:
                 check_and_update_logic_error(True, f"逻辑错误(picked): JAR accept取B类书 {bid_s_j} 给学生 {sid_j}，这将导致其持有超限B类书。")
            if book_o_j.type == 'C' and book_o_j.isbn_str in student_held_c_isbns_before:
                 check_and_update_logic_error(True, f"逻辑错误(picked): JAR accept取C类书 {bid_s_j} 给学生 {sid_j}，但他已持有该ISBN。")

            state.record_book_picked_from_ao(sid_j, book_o_j) 
            if sid_j not in state.user_holds: state.user_holds[sid_j] = set()
            state.user_holds[sid_j].add(book_o_j)
        return

    match_ar = ACCEPT_REJECT_PATTERN.match(line)
    if match_ar:
        _date_j, status_j, sid_j, act_j, item_s_j = match_ar.groups()
        student_held_b_count_before, student_held_c_isbns_before = state.get_held_book_types_and_isbns(sid_j)
        item_is_A_type = item_s_j.startswith('A-')

        if item_is_A_type and status_j == "accept" and act_j in ["ordered", "borrowed"]:
            check_and_update_logic_error(True, f"逻辑错误(gen_ar): JAR accept {act_j} A类项目 {item_s_j}。")

        if act_j == "ordered": # item_s_j is ISBN
            if status_j == "accept":
                if state.is_student_notfetch(sid_j): 
                     check_and_update_logic_error(True, f"逻辑错误(ordered): JAR accept预约 {item_s_j} 给学生 {sid_j}，但他已有未完成预约。")
                book_type_of_item = item_s_j[0]
                if book_type_of_item == 'B' and student_held_b_count_before > 0:
                     check_and_update_logic_error(True, f"逻辑错误(ordered): JAR accept预约B类ISBN {item_s_j} 给学生 {sid_j} (已持有B)。")
                if book_type_of_item == 'C' and item_s_j in student_held_c_isbns_before:
                     check_and_update_logic_error(True, f"逻辑错误(ordered): JAR accept预约C类ISBN {item_s_j} 给学生 {sid_j} (已持有该ISBN)。")
                state.user_pending_order_intents[sid_j] = item_s_j
        
        elif act_j == "borrowed" and status_j == "reject": # item_s_j is ISBN
            target_isbn_for_borrow = item_s_j
            book_example = state.get_book_by_isbn(target_isbn_for_borrow)
            should_have_been_accepted_by_checker = False
            if book_example and book_example.type != 'A':
                if state.books_on_shelf.get(target_isbn_for_borrow): # Copies on shelf
                    if book_example.type == 'B' and student_held_b_count_before == 0: should_have_been_accepted_by_checker = True
                    elif book_example.type == 'C' and target_isbn_for_borrow not in student_held_c_isbns_before: should_have_been_accepted_by_checker = True
            if should_have_been_accepted_by_checker: # JAR rejected when checker thought it should be accepted
                check_and_update_logic_error(True, 
                    f"逻辑不一致(borrow reject): JAR reject借阅 {target_isbn_for_borrow} 给学生 {sid_j}，"
                    f"但Checker认为条件满足 (书架有书，学生资格符合)。")

        elif act_j == "picked" and status_j == "reject": # item_s_j is ISBN
             if sid_orig == sid_j and item_id_orig == item_s_j: 
                res_info = state.reservations_at_ao.get(sid_j)
                if res_info and res_info.book.isbn_str == item_s_j and not res_info.is_expired(current_date_obj):
                    can_pick_hypothetically = (res_info.book.type == 'B' and student_held_b_count_before == 0) or \
                                         (res_info.book.type == 'C' and res_info.book.isbn_str not in student_held_c_isbns_before)
                    if can_pick_hypothetically:
                        check_and_update_logic_error(True, f"逻辑不一致(picked reject): JAR reject取书 {item_s_j} 学生 {sid_j}，但Checker认为条件满足。")
        
        elif act_j == "returned": # item_s_j is BookID
            book_o_j = state.get_book_by_id_str(item_s_j) 
            if status_j == "accept":
                if not (book_o_j and sid_j in state.user_holds and book_o_j in state.user_holds[sid_j]):
                     check_and_update_logic_error(True, f"逻辑错误(returned accept): JAR accept归还 {item_s_j} 学生 {sid_j}，但Checker记录其不持有。")
                if book_o_j and sid_j in state.user_holds and book_o_j in state.user_holds.get(sid_j,set()):
                    state.user_holds[sid_j].remove(book_o_j);
                    if not state.user_holds[sid_j]: del state.user_holds[sid_j]
                    state.books_at_bro.add(book_o_j)
            elif status_j == "reject": 
                if book_o_j and sid_j in state.user_holds and book_o_j in state.user_holds[sid_j]:
                     check_and_update_logic_error(True, f"逻辑错误(returned reject): JAR reject归还 {item_s_j} 学生 {sid_j}，但Checker记录其持有。")
        return

    match_move = MOVE_PATTERN.match(line)
    if match_move:
        _date_m, bid_s_m, from_l, to_l, for_sid_m = match_move.groups(); book_o_m = state.get_book_by_id_str(bid_s_m)
        if not book_o_m:
            check_and_update_logic_error(True, f"逻辑错误(move): JAR移动未知ID {bid_s_m}。"); return
        
        valid_locations = {"bs", "bro", "ao"}
        if from_l not in valid_locations or to_l not in valid_locations : 
            check_and_update_logic_error(True, f"逻辑错误(move): 无效地点 from '{from_l}' to '{to_l}' ({bid_s_m})。")
        if from_l == to_l:
            check_and_update_logic_error(True, f"逻辑错误(move): 起点终点相同 '{from_l}' ({bid_s_m})。")

        if to_l == "ao" and for_sid_m:
            expected_isbn_intent = state.user_pending_order_intents.get(for_sid_m)
            if expected_isbn_intent != book_o_m.isbn_str:
                check_and_update_logic_error(True, 
                    f"逻辑错误(move to ao): JAR移动书 {bid_s_m} 给学生 {for_sid_m}，"
                    f"但其预约意图为'{expected_isbn_intent}' (应为'{book_o_m.isbn_str}'或无)。")
        
        # Update state from_l
        if from_l == "bs":
            if book_o_m.isbn_str in state.books_on_shelf and book_o_m in state.books_on_shelf.get(book_o_m.isbn_str, set()):
                state.books_on_shelf[book_o_m.isbn_str].remove(book_o_m);
                if not state.books_on_shelf[book_o_m.isbn_str]: del state.books_on_shelf[book_o_m.isbn_str]
        elif from_l == "bro":
            if book_o_m in state.books_at_bro: state.books_at_bro.remove(book_o_m)
        elif from_l == "ao":
            if book_o_m in state.books_at_ao: state.books_at_ao.remove(book_o_m)
            sid_whose_book_moved = next((sid for sid, res_i in state.reservations_at_ao.items() if res_i.book == book_o_m), None)
            if sid_whose_book_moved: del state.reservations_at_ao[sid_whose_book_moved]
        
        # Update state to_l
        if to_l == "bs": 
            if book_o_m.isbn_str not in state.books_on_shelf: state.books_on_shelf[book_o_m.isbn_str] = set()
            state.books_on_shelf[book_o_m.isbn_str].add(book_o_m)
        elif to_l == "bro": state.books_at_bro.add(book_o_m)
        elif to_l == "ao":
            if for_sid_m: 
                state.record_book_arrival_at_ao(book_o_m, for_sid_m, current_date_obj, state.is_logically_open and not state.last_event_was_close)
            else: state.books_at_ao.add(book_o_m)
        return

# --- 主模拟循环 ---
def run_test_case(jar_file_path, test_case_num, num_target_commands, output_dir, data_dir):
    global current_test_case_logic_passed, current_test_case_logic_error_msg
    current_test_case_logic_passed = True; current_test_case_logic_error_msg = ""
    state = LibraryState()
    # ... (rest of run_test_case, including send_to_jar_and_log, and main loop structure)
    testcase_file_path = os.path.join(data_dir, f"testcase_{test_case_num}.txt")
    output_file_path = os.path.join(output_dir, f"output_{test_case_num}.txt")
    generated_user_commands_count = 0
    communication_passed = True; comm_error_message = ""
    active_jar_process = None
    
    with open(testcase_file_path, "w", encoding="utf-8") as tf, \
         open(output_file_path, "w", encoding="utf-8") as of:
        
        def send_to_jar_and_log(command_str, proc): 
            nonlocal generated_user_commands_count, communication_passed, comm_error_message
            if command_str is None: return False
            is_user_request = "OPEN" not in command_str and "CLOSE" not in command_str
            if is_user_request: generated_user_commands_count +=1
            if DEBUG_MODE: print(f"Checker -> JAR: {command_str}")
            tf.write(command_str + "\n"); tf.flush()
            try:
                proc.stdin.write(command_str + "\n"); proc.stdin.flush()
            except BrokenPipeError:
                if communication_passed: comm_error_message = f"错误: BrokenPipeError. 命令: {command_str}"
                communication_passed = False; return False
            response_lines = []
            try: 
                if "OPEN" in command_str or "CLOSE" in command_str:
                    header_line = proc.stdout.readline().strip()
                    if not header_line and proc.poll() is not None: raise EOFError("JAR closed stream prematurely after OPEN/CLOSE")
                    response_lines.append(header_line)
                    if header_line.isdigit():
                        for _ in range(int(header_line)): response_lines.append(proc.stdout.readline().strip())
                else:
                    first_resp_line = proc.stdout.readline().strip()
                    if not first_resp_line and proc.poll() is not None: raise EOFError(f"JAR closed stream prematurely after {command_str}")
                    response_lines.append(first_resp_line)
                    if "moving trace:" in first_resp_line and first_resp_line.split(":")[-1].strip().isdigit():
                         for _ in range(int(first_resp_line.split(":")[-1].strip())): response_lines.append(proc.stdout.readline().strip())
            except Exception as e:
                if communication_passed: comm_error_message = f"错误: 从JAR读取时发生异常: {e}"
                communication_passed = False; return False
            for resp_line in response_lines:
                if DEBUG_MODE: print(f"JAR -> Checker: {resp_line}")
                of.write(resp_line + "\n")
                if communication_passed and current_test_case_logic_passed: 
                    parse_java_output_line(resp_line, state, state.current_date, command_str) 
            of.flush()
            return communication_passed
        
        active_jar_process = subprocess.Popen(
            [JAVA_EXECUTABLE, "-jar", jar_file_path],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, encoding="utf-8", bufsize=1
        )
        time.sleep(0.05) # Even shorter sleep

        if active_jar_process.poll() is not None: 
            communication_passed = False; comm_error_message = f"错误: JAR未能启动。返回码: {active_jar_process.returncode}"
        else:
            initial_book_lines = generate_initial_books(state)
            for line in initial_book_lines:
                tf.write(line + "\n")
                try: active_jar_process.stdin.write(line + "\n")
                except BrokenPipeError: communication_passed = False; comm_error_message = "错误: 写入初始书籍列表时JAR终止。"; break
            if communication_passed: active_jar_process.stdin.flush(); tf.flush()

        # Main Loop
        while communication_passed and current_test_case_logic_passed and \
              generated_user_commands_count < num_target_commands:
            
            if active_jar_process.poll() is not None: 
                if communication_passed: comm_error_message = f"错误: JAR意外终止。返回码: {active_jar_process.returncode}"
                communication_passed = False; break 
            
            current_date_str = state.current_date.strftime('%Y-%m-%d')
            
            todays_planned_user_commands = []
            todays_planned_returns_book_ids = set() 
            todays_planned_picked_book_objects = set()

            if generated_user_commands_count < num_target_commands:
                max_cmds_today = random.randint(0, 2) 
                for _ in range(max_cmds_today):
                    if (generated_user_commands_count + len(todays_planned_user_commands)) >= num_target_commands: break
                    action_choices = ['return', 'pick', 'borrow', 'order', 'query']
                    random.shuffle(action_choices)
                    generated_cmd_this_iteration = None
                    for action_type_try in action_choices:
                        cmd_str = None; book_obj_involved = None
                        if action_type_try == 'return':
                            cmd_str, book_obj_involved = generate_return_command_v2(state, current_date_str, todays_planned_returns_book_ids)
                            if cmd_str: todays_planned_returns_book_ids.add(book_obj_involved.book_id_str)
                        elif action_type_try == 'pick':
                            cmd_str, book_obj_involved = generate_pick_command_v2(state, current_date_str, todays_planned_picked_book_objects)
                            if cmd_str: todays_planned_picked_book_objects.add(book_obj_involved)
                        elif action_type_try == 'borrow': cmd_str = generate_borrow_command(state, current_date_str)
                        elif action_type_try == 'order': cmd_str = generate_order_command(state, current_date_str)
                        elif action_type_try == 'query': cmd_str = generate_query_command(state, current_date_str)
                        if cmd_str: generated_cmd_this_iteration = cmd_str; break 
                    if generated_cmd_this_iteration: todays_planned_user_commands.append(generated_cmd_this_iteration)
                    else: break 
            
            if todays_planned_user_commands:
                state.last_event_was_close = False
                open_cmd = f"[{current_date_str}] OPEN"
                if not send_to_jar_and_log(open_cmd, active_jar_process): break
                state.is_logically_open = True
                if len(state.books_at_bro) > 0: check_and_update_logic_error(True, f"逻辑错误: {current_date_str} 开馆后借还处仍有书。")
                expired_ao = sum(1 for r_i in state.reservations_at_ao.values() if r_i.is_expired(state.current_date))
                if expired_ao > 0: check_and_update_logic_error(True, f"逻辑错误: {current_date_str} 开馆后预约处仍有过期书。")
                # Call consistency check after OPEN organization moves are parsed
                if communication_passed and current_test_case_logic_passed: state.check_book_total_consistency()
                if not (communication_passed and current_test_case_logic_passed): break

                for user_cmd in todays_planned_user_commands:
                    if not send_to_jar_and_log(user_cmd, active_jar_process): break
                    # Call consistency check after each user command's effects are parsed
                    if communication_passed and current_test_case_logic_passed: state.check_book_total_consistency()
                if not (communication_passed and current_test_case_logic_passed): break

                if state.is_logically_open: 
                    close_cmd = f"[{current_date_str}] CLOSE"
                    if not send_to_jar_and_log(close_cmd, active_jar_process): break
                    state.is_logically_open = False; state.last_event_was_close = True
                    # Call consistency check after CLOSE organization moves are parsed
                    if communication_passed and current_test_case_logic_passed: state.check_book_total_consistency()

            state.current_date += datetime.timedelta(days=1)
            if generated_user_commands_count >= num_target_commands and not todays_planned_user_commands: break
            if not (communication_passed and current_test_case_logic_passed): break
        
        final_error_message_to_report = ""
        if not communication_passed: final_error_message_to_report = comm_error_message
        elif not current_test_case_logic_passed: final_error_message_to_report = current_test_case_logic_error_msg
        
        if state.is_logically_open and active_jar_process.poll() is None and communication_passed and current_test_case_logic_passed :
            send_to_jar_and_log(f"[{state.current_date.strftime('%Y-%m-%d')}] CLOSE", active_jar_process) # Use state.current_date as it might have advanced
            if communication_passed and current_test_case_logic_passed: state.check_book_total_consistency()


        try: # ... (subprocess cleanup, same as before)
            if active_jar_process:
                if active_jar_process.stdin and not active_jar_process.stdin.closed: active_jar_process.stdin.close()
                if active_jar_process.poll() is None:
                    outs, errs = active_jar_process.communicate(timeout=1)
                    if errs and not final_error_message_to_report: final_error_message_to_report = f"JAR STDERR (at end):\n{errs}"
                    if errs: of.write(f"JAR STDERR (at end):\n{errs}")
        except subprocess.TimeoutExpired:
            if active_jar_process: active_jar_process.kill(); active_jar_process.wait()
            if not final_error_message_to_report: final_error_message_to_report = "错误: JAR清理时超时。"
        except Exception as e_clean:
            if not final_error_message_to_report: final_error_message_to_report = f"错误: JAR清理时异常: {e_clean}"
        if final_error_message_to_report and not DEBUG_MODE:
            of.write(f"\n--- CHECKER DETECTED ERROR ---\n{final_error_message_to_report}\n")

    overall_passed = communication_passed and current_test_case_logic_passed
    return overall_passed, final_error_message_to_report

if __name__ == "__main__": # ... (same main execution block as before)
    if not os.path.exists(JAR_PATH): print(f"错误: JAR文件未在 '{JAR_PATH}'找到。"); exit(1)
    try:
        num_test_cases_str = input("请输入要生成的测试数据组数: ")
        if not num_test_cases_str.isdigit() or int(num_test_cases_str) <= 0: raise ValueError("组数必须为正整数")
        num_test_cases = int(num_test_cases_str)
        num_commands_per_case_str = input("请输入每个测试用例的指令数 (不包括OPEN/CLOSE/初始书籍): ")
        if not num_commands_per_case_str.isdigit() or int(num_commands_per_case_str) <=0 : raise ValueError("指令数必须为正整数")
        num_commands_per_case = int(num_commands_per_case_str)
    except ValueError as e: print(f"输入无效: {e}"); exit(1)
    data_folder = "data"; output_folder = "output"
    os.makedirs(data_folder, exist_ok=True); os.makedirs(output_folder, exist_ok=True)
    print(f"\n开始测试 (DEBUG_MODE: {DEBUG_MODE})...\n")
    for i in range(1, num_test_cases + 1):
        print(f"--- 正在运行测试用例 {i} ---")
        current_test_case_logic_passed = True; current_test_case_logic_error_msg = "" 
        passed, msg = run_test_case(JAR_PATH, i, num_commands_per_case, output_folder, data_folder)
        if passed: print(f"--- 测试用例 {i}: 通过 ---")
        else:
            print(f"--- 测试用例 {i}: 失败 ---")
            if msg: print(f"  错误详情: {msg.splitlines()[0] if msg.splitlines() else msg}")
            print(f"  请检查 data/testcase_{i}.txt 和 output/output_{i}.txt 获取详细信息。")
    print("\nChecker 已完成所有测试。")