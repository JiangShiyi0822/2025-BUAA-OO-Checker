# gen.py
import random
import time
import sys
import os
import re
import math  # No longer strictly needed but keep for now
from typing import List, Dict, Optional, Tuple, Set
import argparse
# 修改后，生成的数据无时间间隔
# --- Constants --- (Updated Dense constants)
FLOORS = ["B4", "B3", "B2", "B1", "F1", "F2", "F3", "F4", "F5", "F6", "F7"]
FLOOR_MAP = {name: i for i, name in enumerate(FLOORS)}
NUM_FLOORS = len(FLOORS)
UPDATE_TARGET_FLOORS = ["B2", "B1", "F1", "F2", "F3", "F4", "F5"]
SCHE_TARGET_FLOORS = ["B2", "B1", "F1", "F2", "F3", "F4", "F5"]
SCHE_SPEEDS = [0.2, 0.3, 0.4, 0.5]
NUM_ELEVATORS = 6
DEFAULT_ELEVATOR_SPEED = 0.4
DOUBLE_CAR_SPEED = 0.2
MIN_REQUESTS = 1
MAX_PASSENGER_ID = 999
DEFAULT_PUBLIC_MAX_TIMESTAMP = 50.0
DEFAULT_PUBLIC_MAX_TOTAL_REQUESTS = 100
DEFAULT_PUBLIC_MAX_SCHE_TOTAL = 20
DEFAULT_PUBLIC_MAX_SCHE_PER_ELEVATOR = float("inf")
DEFAULT_PUBLIC_MAX_UPDATE_TOTAL = NUM_ELEVATORS // 2
DEFAULT_MUTUAL_MAX_TIMESTAMP = 50.0
DEFAULT_MUTUAL_MAX_TOTAL_REQUESTS = 70
DEFAULT_MUTUAL_MAX_SCHE_TOTAL = 6
DEFAULT_MUTUAL_MAX_SCHE_PER_ELEVATOR = 1
DEFAULT_MUTUAL_MAX_UPDATE_TOTAL = 6
MIN_TIMESTAMP = 1.0
MIN_SCHE_SEPARATION_PER_ELEVATOR = 8.0
MIN_SCHE_TO_UPDATE_SEPARATION = 8.0
# --- Dense Time Point Constants ---
MIN_DENSE_TARGET_POINTS = 2
MAX_DENSE_TARGET_POINTS = 4  # Updated range to 2-4
MIN_DENSE_POINT_SEPARATION = 5.0  # Min seconds between chosen target points


def generate_hw7_data(
    total_requests_target: int,
    mutual_mode: bool,
    pattern: str = "random",
    max_time_override: Optional[float] = None,
    max_sche_per_elevator_override: Optional[int] = None,
    max_update_total_override: Optional[int] = None,
) -> List[str]:
    """
    Generates test data for HW7 v4 based on specified pattern.
    Patterns: 'random', 'uniform', 'dense', 'frequent'.
    'dense' concentrates proposals around 2-4 scattered time points.
    Enforces 8s SCHE->UPDATE gap. No INFO/WARN printouts.
    Output is intended for stdin.txt. Mode is set via parameter.
    """

    # --- Determine Effective Constraints --- (Same)
    if mutual_mode:
        max_timestamp = DEFAULT_MUTUAL_MAX_TIMESTAMP
        max_total_requests_limit = DEFAULT_MUTUAL_MAX_TOTAL_REQUESTS
        max_sche_total_limit = DEFAULT_MUTUAL_MAX_SCHE_TOTAL
        max_sche_per_elevator_limit = DEFAULT_MUTUAL_MAX_SCHE_PER_ELEVATOR
        max_update_total_limit = DEFAULT_MUTUAL_MAX_UPDATE_TOTAL
    else:  # Public Mode
        max_timestamp = DEFAULT_PUBLIC_MAX_TIMESTAMP
        max_total_requests_limit = DEFAULT_PUBLIC_MAX_TOTAL_REQUESTS
        max_sche_total_limit = DEFAULT_PUBLIC_MAX_SCHE_TOTAL
        if (
            max_sche_per_elevator_override is not None
            and max_sche_per_elevator_override >= 0
        ):
            max_sche_per_elevator_limit = max_sche_per_elevator_override
        else:
            max_sche_per_elevator_limit = DEFAULT_PUBLIC_MAX_SCHE_PER_ELEVATOR
        if max_update_total_override is not None and max_update_total_override >= 0:
            max_update_total_limit = max_update_total_override
        else:
            max_update_total_limit = DEFAULT_PUBLIC_MAX_UPDATE_TOTAL

    if max_time_override is not None and max_time_override >= MIN_TIMESTAMP:
        max_timestamp = max_time_override
    elif max_time_override is not None:
        pass

    # --- Validate and Adjust Total Requests --- (Same)
    if total_requests_target < MIN_REQUESTS:
        total_requests_target = MIN_REQUESTS
    if total_requests_target > max_total_requests_limit:
        total_requests = max_total_requests_limit
    else:
        total_requests = total_requests_target

    # --- Determine Number of Each Request Type based on Pattern --- (Same)
    num_passengers, num_sche, num_update = 0, 0, 0
    max_sche_possible_overall = min(total_requests, max_sche_total_limit)
    if mutual_mode:
        max_sche_possible_overall = min(
            max_sche_possible_overall, int(NUM_ELEVATORS * max_sche_per_elevator_limit)
        )
    elif max_sche_per_elevator_limit != float("inf"):
        max_sche_possible_overall = min(
            max_sche_possible_overall, int(NUM_ELEVATORS * max_sche_per_elevator_limit)
        )
    max_update_possible_overall = min(
        total_requests, max_update_total_limit, NUM_ELEVATORS // 2
    )
    # (Uniform/Frequent/Random/Dense count logic remains the same)
    if pattern == "uniform":
        target_per_type = total_requests // 3
        rem = total_requests % 3
        num_sche = min(target_per_type, max_sche_possible_overall)
        num_update = min(target_per_type, max_update_possible_overall)
        num_passengers = total_requests - num_sche - num_update
        if rem > 0 and num_passengers < (target_per_type + rem):
            num_passengers += 1
            rem -= 1
        if rem > 0 and num_sche < min(target_per_type + rem, max_sche_possible_overall):
            num_sche += 1
            rem -= 1
        if rem > 0 and num_update < min(
            target_per_type + rem, max_update_possible_overall
        ):
            num_update += 1
            rem -= 1
        num_passengers = total_requests - num_sche - num_update
    elif pattern == "frequent":
        num_sche = max_sche_possible_overall
        num_update = random.randint(
            0, min(max_update_possible_overall, total_requests - num_sche)
        )
        num_passengers = total_requests - num_sche - num_update
        if num_passengers < 0:
            reduction = abs(num_passengers)
            reduce_update = min(reduction, num_update)
            num_update -= reduce_update
            reduction -= reduce_update
            if reduction > 0:
                num_sche -= reduction
            num_passengers = 0
    elif pattern == "dense" or pattern == "random":
        potential_update = random.randint(0, max_update_possible_overall)
        remaining_for_sche = max(0, total_requests - potential_update)
        potential_sche = random.randint(
            0, min(max_sche_possible_overall, remaining_for_sche)
        )
        num_update = potential_update
        num_sche = potential_sche
        num_passengers = total_requests - num_sche - num_update
        if num_passengers < 0:
            num_sche = min(num_sche, max_sche_possible_overall)
            num_update = min(num_update, max_update_possible_overall)
            needed_reduction = num_sche + num_update - total_requests
            can_reduce_update = min(num_update, needed_reduction)
            num_update -= can_reduce_update
            needed_reduction -= can_reduce_update
            if needed_reduction > 0:
                num_sche -= min(num_sche, needed_reduction)
            num_passengers = total_requests - num_sche - num_update

    # --- Initialization for Generation --- (Same)
    generated_requests: List[Tuple[float, str]] = []
    current_time = 0.0  # Tracks LAST PLACED request time after clamping
    passenger_ids_pool = random.sample(
        range(1, max(MAX_PASSENGER_ID + 1, num_passengers * 2)), num_passengers
    )
    last_sche_time_per_elevator: Dict[int, float] = {}
    sche_count_per_elevator: Dict[int, int] = {
        eid: 0 for eid in range(1, NUM_ELEVATORS + 1)
    }
    update_involved_elevators: Set[int] = set()
    update_timestamp_per_elevator: Dict[int, float] = {}
    update_generated_count = 0
    sche_generated_count = 0
    passenger_generated_count = 0
    generated_count = 0

    # --- Create Single Combined Pool --- (Same)
    request_pool = []
    p_idx = 0
    for _ in range(num_passengers):
        if p_idx < len(passenger_ids_pool):
            passenger_id = passenger_ids_pool[p_idx]
            priority = random.randint(1, 100)
            start_floor = random.choice(FLOORS)
            end_floor = random.choice(FLOORS)
            while start_floor == end_floor:
                end_floor = random.choice(FLOORS)
            request_pool.append(
                {
                    "type": "passenger",
                    "id": passenger_id,
                    "priority": priority,
                    "from": start_floor,
                    "to": end_floor,
                }
            )
            p_idx += 1
    for _ in range(num_sche):
        speed = random.choice(SCHE_SPEEDS)
        target_floor = random.choice(SCHE_TARGET_FLOORS)
        request_pool.append({"type": "sche", "speed": speed, "target": target_floor})
    for _ in range(num_update):
        target_floor = random.choice(UPDATE_TARGET_FLOORS)
        request_pool.append({"type": "update", "target": target_floor})
    while len(request_pool) < total_requests and p_idx < len(passenger_ids_pool):
        passenger_id = passenger_ids_pool[p_idx]
        priority = random.randint(1, 100)
        start_floor = random.choice(FLOORS)
        end_floor = random.choice(FLOORS)
        while start_floor == end_floor:
            end_floor = random.choice(FLOORS)
        request_pool.append(
            {
                "type": "passenger",
                "id": passenger_id,
                "priority": priority,
                "from": start_floor,
                "to": end_floor,
            }
        )
        p_idx += 1
    request_pool = request_pool[:total_requests]
    random.shuffle(request_pool)

    # --- Dense Pattern: Select Target Time Points and Assign to Requests ---
    dense_target_times = []
    if pattern == "dense" and total_requests > 0:
        num_points = random.randint(MIN_DENSE_TARGET_POINTS, MAX_DENSE_TARGET_POINTS)
        # Try to pick N distinct points with minimum separation
        attempts = 0
        max_attempts = num_points * 5  # Limit attempts to find points
        potential_points = []
        while len(potential_points) < num_points and attempts < max_attempts:
            attempts += 1
            # Pick a random point, ensuring it's not too close to start/end
            pt = random.uniform(
                MIN_TIMESTAMP + MIN_DENSE_POINT_SEPARATION / 2,
                max_timestamp - MIN_DENSE_POINT_SEPARATION / 2,
            )
            is_far_enough = True
            for existing_pt in potential_points:
                if abs(pt - existing_pt) < MIN_DENSE_POINT_SEPARATION:
                    is_far_enough = False
                    break
            if is_far_enough:
                potential_points.append(pt)

        if len(potential_points) >= MIN_DENSE_TARGET_POINTS:
            dense_target_times = sorted(potential_points)
            # Assign a target time to each request in the pool
            for req in request_pool:
                req["target_time"] = random.choice(dense_target_times)
            # print(f"DEBUG: Dense pattern targets assigned: {dense_target_times}", file=sys.stderr)
        else:
            print(
                f"NOTE: Could not select {MIN_DENSE_TARGET_POINTS} sufficiently separated target times. Falling back to random pattern.",
                file=sys.stderr,
            )
            pattern = "random"  # Fallback

    # --- Initialize Skip Counters --- (Same)
    skipped_sche_limit = 0
    skipped_sche_time = 0
    skipped_sche_after_update = 0
    skipped_update_pairing = 0
    skipped_update_sche_interval = 0
    skipped_due_type_limit = 0

    # --- Generate Requests by Iterating Through Shuffled Pool ---
    pool_index = 0
    while generated_count < total_requests and pool_index < len(request_pool):
        req_data = request_pool[pool_index]
        req_type = req_data["type"]
        pool_index += 1
        # Type limits checks (same)
        if req_type == "passenger" and passenger_generated_count >= num_passengers:
            skipped_due_type_limit += 1
            continue
        if req_type == "sche" and sche_generated_count >= num_sche:
            skipped_due_type_limit += 1
            continue
        if req_type == "update" and update_generated_count >= num_update:
            skipped_due_type_limit += 1
            continue

        # Check if last placed request time already reached max_timestamp
        last_placed_time = generated_requests[-1][0] if generated_count > 0 else 0.0
        if last_placed_time > max_timestamp:
            break

        # --- Generate Base Timestamp (Pattern Aware) ---
        # earliest_possible depends on the *actual* time of the last placed request
        earliest_possible_time = max(
            MIN_TIMESTAMP, last_placed_time if generated_count > 0 else 0.0
        )
        base_timestamp = 0.0

        if pattern == "dense" and dense_target_times:
            # Use the pre-assigned target time for the request
            base_timestamp = req_data["target_time"]
            # Add tiny jitter - might not be needed, 0.1s rule dominates
            # base_timestamp += random.uniform(-0.01, 0.01)
            base_timestamp = max(MIN_TIMESTAMP, base_timestamp)  # Ensure not below min
        else:  # random, uniform, frequent use spreading based on *last placed time*
            # We base interval calculation from the last actual placed time
            effective_current_time_for_spreading = (
                last_placed_time if generated_count > 0 else 0.0
            )
            remaining_to_generate = total_requests - generated_count
            avg_remaining_interval = (
                max(
                    0.05,
                    (max_timestamp - effective_current_time_for_spreading)
                    / remaining_to_generate,
                )
                if remaining_to_generate > 0
                else 0.1
            )
            time_increment = random.uniform(
                0.0, avg_remaining_interval * 1.7
            )  # Ensure minimum 0.1 increment base
            base_timestamp = effective_current_time_for_spreading + time_increment

        # Clamp proposal to max_timestamp
        base_timestamp = min(base_timestamp, max_timestamp)

        # Tentative proposed time, might be pushed forward by constraints or 0.1s gap
        # Must respect the *actual* earliest possible time for *this* request
        timestamp = round(max(earliest_possible_time, base_timestamp), 1)

        # --- Handle Request Generation ---
        success = False
        request_str_content = ""
        final_timestamp = -1.0
        # Use 'timestamp' (initial proposal respecting earliest possible time) for interval checks
        if req_type == "passenger":
            request_str_content = f"{req_data['id']}-PRI-{req_data['priority']}-FROM-{req_data['from']}-TO-{req_data['to']}"
            final_timestamp = (
                timestamp  # Passenger constraints checked by clamping below
            )
            success = True
        elif req_type == "sche":
            found_slot = False
            candidate_elevator = -1
            candidate_timestamp = -1.0
            potential_candidates = []
            elevator_ids_to_try = list(range(1, NUM_ELEVATORS + 1))
            random.shuffle(elevator_ids_to_try)
            for elevator_id in elevator_ids_to_try:
                if sche_count_per_elevator[elevator_id] >= max_sche_per_elevator_limit:
                    continue
                update_time = update_timestamp_per_elevator.get(
                    elevator_id, float("inf")
                )
                last_sche = last_sche_time_per_elevator.get(elevator_id, -float("inf"))
                required_sche_start_time_interval = (
                    last_sche + MIN_SCHE_SEPARATION_PER_ELEVATOR
                )
                earliest_allowed_sche = max(
                    timestamp, required_sche_start_time_interval
                )  # Max of proposal & interval rule
                latest_allowed_sche = min(max_timestamp, update_time - 0.001)
                if earliest_allowed_sche <= latest_allowed_sche:
                    potential_candidates.append((earliest_allowed_sche, elevator_id))
            if potential_candidates:
                potential_candidates.sort(key=lambda x: x[0])
                final_ts_proposal, selected_elevator_id = potential_candidates[0]
                candidate_timestamp = round(
                    final_ts_proposal, 1
                )  # Time respecting specific constraints
                if candidate_timestamp <= max_timestamp:
                    candidate_elevator = selected_elevator_id
                    found_slot = True
            if found_slot:
                request_str_content = f"SCHE-{candidate_elevator}-{req_data['speed']:.1f}-{req_data['target']}"
                final_timestamp = (
                    candidate_timestamp  # Pass this time to final clamping
                )
                success = True
            else:  # SCHE failed - skip logic same
                if all(
                    sche_count_per_elevator[eid] >= max_sche_per_elevator_limit
                    for eid in range(1, NUM_ELEVATORS + 1)
                ):
                    skipped_sche_limit += 1
                elif any(
                    update_timestamp_per_elevator.get(eid, float("inf"))
                    <= timestamp + MIN_SCHE_SEPARATION_PER_ELEVATOR
                    for eid in range(1, NUM_ELEVATORS + 1)
                ):
                    skipped_sche_after_update += 1
                else:
                    skipped_sche_time += 1
        elif req_type == "update":
            found_pair_and_time = False
            elevator_a = -1
            elevator_b = -1
            final_timestamp_update = -1.0
            eligible_elevators = [
                e
                for e in range(1, NUM_ELEVATORS + 1)
                if e not in update_involved_elevators
            ]
            random.shuffle(eligible_elevators)
            if len(eligible_elevators) >= 2:
                for i in range(len(eligible_elevators)):
                    for j in range(i + 1, len(eligible_elevators)):
                        e1, e2 = eligible_elevators[i], eligible_elevators[j]
                        potential_a, potential_b = (
                            (e1, e2) if random.random() < 0.5 else (e2, e1)
                        )
                        last_sche_A = last_sche_time_per_elevator.get(
                            potential_a, -float("inf")
                        )
                        last_sche_B = last_sche_time_per_elevator.get(
                            potential_b, -float("inf")
                        )
                        min_req_update_time_8s = max(
                            last_sche_A + MIN_SCHE_TO_UPDATE_SEPARATION,
                            last_sche_B + MIN_SCHE_TO_UPDATE_SEPARATION,
                        )
                        actual_earliest_update_time = max(
                            timestamp, min_req_update_time_8s
                        )  # Max of proposal & interval rule
                        if actual_earliest_update_time <= max_timestamp:
                            candidate_ts = round(
                                actual_earliest_update_time, 1
                            )  # Time respecting specific constraints
                            elevator_a = potential_a
                            elevator_b = potential_b
                            final_timestamp_update = candidate_ts
                            found_pair_and_time = True
                            break
                    if found_pair_and_time:
                        break
            if found_pair_and_time:
                request_str_content = (
                    f"UPDATE-{elevator_a}-{elevator_b}-{req_data['target']}"
                )
                final_timestamp = (
                    final_timestamp_update  # Pass this time to final clamping
                )
                success = True
            else:  # UPDATE failed - skip logic same
                if len(eligible_elevators) < 2:
                    skipped_update_pairing += 1
                else:
                    skipped_update_sche_interval += 1

        # --- Record Successful Generation & Advance Time (Critical Clamping) ---
        if success and final_timestamp >= 0:
            # Take the timestamp proposal determined after interval checks (SCHE/UPDATE) or direct proposal (PASSENGER)
            clamped_final_ts = final_timestamp

            # >>> Enforce 0.1s gap from last actual placement time <<<
            """ if generated_count > 0:
                clamped_final_ts = max(
                    clamped_final_ts, generated_requests[-1][0] + 0.1
                ) """

            # Ensure >= MIN_TIMESTAMP
            clamped_final_ts = max(MIN_TIMESTAMP, clamped_final_ts)

            # Round AFTER all clamping
            clamped_final_ts = round(clamped_final_ts, 1)

            # Final check against max_timestamp
            if clamped_final_ts <= max_timestamp:
                # SUCCESS: Add request with the validated & clamped timestamp
                generated_requests.append((clamped_final_ts, request_str_content))
                generated_count += 1

                # Update specific tracking using the FINAL clamped time
                if req_type == "passenger":
                    passenger_generated_count += 1
                elif req_type == "sche":
                    sche_generated_count += 1
                    last_sche_time_per_elevator[candidate_elevator] = clamped_final_ts
                    sche_count_per_elevator[candidate_elevator] += 1
                elif req_type == "update":
                    update_generated_count += 1
                    update_involved_elevators.add(elevator_a)
                    update_involved_elevators.add(elevator_b)
                    update_timestamp_per_elevator[elevator_a] = clamped_final_ts
                    update_timestamp_per_elevator[elevator_b] = clamped_final_ts
            else:
                pass  # Skip if clamping pushed past max_timestamp

    # --- Final Formatting ---
    final_requests = []
    for ts, content in generated_requests:
        formatted_ts = f"{ts:.1f}"
        new_req = f"[{formatted_ts}]{content}"
        final_requests.append(new_req)

    return final_requests


# --- Main Program Entry --- (Argument parsing and final output unchanged)
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate HW7 elevator test data to stdin.txt. Mode (public/mutual) and pattern must be specified."
    )
    parser.add_argument(
        "total_requests", type=int, help="Target total number of requests."
    )
    parser.add_argument(
        "--mode",
        choices=["public", "mutual"],
        required=True,
        help="Specify the testing mode (public or mutual constraints).",
    )
    parser.add_argument(
        "--pattern",
        choices=["random", "uniform", "dense", "frequent"],
        default="random",
        help="Specify the request generation pattern. Defaults to 'random'.",
    )
    parser.add_argument(
        "--max_time", type=float, default=None, help="Override default max timestamp."
    )
    parser.add_argument(
        "--max_sche_per_elevator",
        type=int,
        default=None,
        help="Override public max SCHE per elevator (only used if mode is public).",
    )
    parser.add_argument(
        "--max_update_total",
        type=int,
        default=None,
        help="Override default max total UPDATE requests (only used if mode is public).",
    )
    parser.epilog = """
Writes generated data directly to 'stdin.txt' in the current directory.

Generation Patterns:
  random    : Random distribution of request types (Default).
  uniform   : Attempts roughly equal numbers of Passenger, SCHE, UPDATE requests.
  dense     : Concentrates request proposals around 2-4 scattered time points.
  frequent  : Maximizes the number of SCHE requests within constraints.

Examples:
  Default (Public, random pattern):
    python gen.py 50 --mode public
  Mutual mode, Uniform pattern:
    python gen.py 60 --mode mutual --pattern uniform
  Public mode, Dense pattern (concentrated):
    python gen.py 100 --mode public --pattern dense
  Mutual mode, Frequent SCHE pattern:
    python gen.py 70 --mode mutual --pattern frequent --max_time 40.0
"""
    args = parser.parse_args()
    if args.total_requests <= 0:
        print("ERROR: Total requests must be positive.", file=sys.stderr)
        sys.exit(1)
    is_mutual_mode = args.mode == "mutual"
    output_filename = "stdin.txt"
    try:
        generated_data = generate_hw7_data(
            total_requests_target=args.total_requests,
            mutual_mode=is_mutual_mode,
            pattern=args.pattern,
            max_time_override=args.max_time,
            max_sche_per_elevator_override=args.max_sche_per_elevator,
            max_update_total_override=args.max_update_total,
        )
        try:
            with open(output_filename, "w", encoding="utf-8") as f:
                [f.write(line + "\n") for line in generated_data]
            print(
                f"Successfully generated {len(generated_data)} requests to {output_filename} (mode: {args.mode}, pattern: {args.pattern})",
                file=sys.stderr,
            )
        except IOError as e:
            print(
                f"ERROR: Could not write to file {output_filename}: {e}",
                file=sys.stderr,
            )
            sys.exit(1)
    except Exception as e:
        print(
            f"\nERROR: An error occurred during data generation: {e}", file=sys.stderr
        )
        import traceback

        traceback.print_exc(file=sys.stderr)
        sys.exit(1)
    sys.exit(0)


""" generate_hw7_data(
            total_requests_target=100,
            mutual_mode=False,
            pattern="random",
            max_time_override = 2
        ) """