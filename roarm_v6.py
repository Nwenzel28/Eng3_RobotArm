import requests
import argparse
import time
from enum import Enum, auto
from typing import List, Tuple, Dict
from dataclasses import dataclass


class StateResult(Enum):
    """Return values for state execution"""
    SUCCESS = auto()
    FAILURE = auto()
    ABORT = auto()


@dataclass
class RobotPose:
    """Represents a robot arm joint configuration"""
    base: float
    shoulder: float
    elbow: float
    wrist: float
    roll: float
    hand: float


def make_t102_command(pose: RobotPose, spd: int = 0, acc: int = 254) -> str:
    """Generate T:102 command string from a pose"""
    return (f'{{"T":102,"base":{pose.base},"shoulder":{pose.shoulder},'
            f'"elbow":{pose.elbow},"wrist":{pose.wrist},"roll":{pose.roll},'
            f'"hand":{pose.hand},"spd":{spd},"acc":{acc}}}')


class RobotState:
    """Base class for robot arm states"""

    def __init__(self, name: str):
        self.name = name

    def execute(self, ip_addr: str, session: requests.Session) -> StateResult:
        """Execute this state. Override in subclasses."""
        raise NotImplementedError

    def _send_command(self, ip_addr: str, session: requests.Session,
                     command_str: str, delay: float) -> StateResult:
        """Helper method to send a command and wait"""
        try:
            url = f"http://{ip_addr}/js?json={command_str}"
            print(f"    → Sending command...")
            response = session.get(url, timeout=0.2)
            print(f"    ✓ Response: {response.text}")

            if delay > 0:
                print(f"    ⏱  Waiting {delay}s...")
                time.sleep(delay)

            return StateResult.SUCCESS
        except requests.exceptions.Timeout:
            print(f"    ⚠  Timeout (command may have been sent)")
            return StateResult.SUCCESS
        except requests.exceptions.RequestException as e:
            print(f"    ✗ HTTP error: {e}")
            return StateResult.FAILURE
        except Exception as e:
            print(f"    ✗ Unexpected error: {e}")
            return StateResult.FAILURE


class SimpleRobotState(RobotState):
    """State that executes a sequence of poses with delays"""

    def __init__(self, name: str, commands: List[Tuple[str, float]]):
        super().__init__(name)
        self.commands = commands

    def execute(self, ip_addr: str, session: requests.Session) -> StateResult:
        print(f"\n{'='*60}")
        print(f"  STATE: {self.name}")
        print(f"{'='*60}")

        for i, (command, delay) in enumerate(self.commands, 1):
            print(f"  Step {i}/{len(self.commands)}:")
            result = self._send_command(ip_addr, session, command, delay)
            if result != StateResult.SUCCESS:
                return result
        return StateResult.SUCCESS


class PoseState(SimpleRobotState):
    """Convenience class to create states from RobotPose objects"""

    def __init__(self, name: str, poses: List[Tuple[RobotPose, float]], acc: int = 255):
        commands = [(make_t102_command(pose, acc=acc), delay) for pose, delay in poses]
        super().__init__(name, commands)


class DropoffSelectionState(RobotState):
    """State that prompts user to select a dropoff location"""

    def __init__(self, name: str, dropoff_map: Dict[str, str]):
        super().__init__(name)
        self.dropoff_map = dropoff_map

    def execute(self, ip_addr: str, session: requests.Session) -> StateResult:
        print(f"\n{'='*60}")
        print(f"  STATE: {self.name}")
        print(f"{'='*60}")
        print(f"  Select dropoff position:")
        for key, state_name in sorted(self.dropoff_map.items()):
            print(f"     [{key}] {state_name}")
        print(f"     [s] Skip")
        print(f"     [a] Abort")

        try:
            user_input = input("  → ").lower().strip()

            if user_input == 's':
                print("  ↷ Skipping dropoff")
                return StateResult.SUCCESS
            elif user_input == 'a':
                print("  ⊘ Aborted by user")
                return StateResult.ABORT
            elif user_input in self.dropoff_map:
                print(f"  ✓ Selected: {self.dropoff_map[user_input]}")
                return user_input  # Return the key to indicate which dropoff to use
            else:
                print(f"  ✗ Invalid selection: {user_input}")
                return StateResult.FAILURE
        except (KeyboardInterrupt, EOFError):
            print("  ⊘ Aborted by user")
            return StateResult.ABORT


class WaitForInputState(RobotState):
    """Pause and wait for user input with manual overrides"""

    def execute(self, ip_addr: str, session: requests.Session) -> StateResult:
        print(f"\n{'='*60}")
        print(f"  STATE: {self.name}")
        print(f"{'='*60}")
        print(f"  ⏸  Press ENTER to continue...")
        print(f"     [s] Skip to next state")
        print(f"     [r] Repeat previous state")
        try:
            user_input = input("  → ").lower().strip()

            if user_input == 's':
                print("  ↷ Skipping to next state")
                return StateResult.SUCCESS
            elif user_input == 'r':
                print("  ↶ Repeating previous state")
                return "REPEAT"
            else:
                print("  ✓ Continuing")
                return StateResult.SUCCESS
        except (KeyboardInterrupt, EOFError):
            print("  ⊘ Aborted by user")
            return StateResult.ABORT


# Pose definitions
HOME_POSE = RobotPose(1.553922538, -0.113514578, 2.406815856, 0.905048665, -0.076699039, 2.664524629)

LEFT_PICKUP_POSES = [
    (RobotPose(1.553922538, -0.113514578, 2.406815856, 0.905048665, -0.076699039, 2.664524629), 0.42),
    (RobotPose(1.279339977, 0.230097118, 2.58935957, 0.527689391, -0.216291563, 2.553320765), 0.3),
    (RobotPose(1.290077843, 0.176407791, 2.658388705, 0.40803889, -0.260776734, 3.183301384), 0.15),
    (RobotPose(1.412971055, -0.159534002, 2.370000317, 1.015495282, -0.234699332, 3.126252846), 0.14),
]

MIDDLE_DROPOFF_POSES = [
    (RobotPose(0.401902966, 0.110446617, 2.311709047, 0.852893318, -1.202640938, 3.046485845), 0.55),
    (RobotPose(0.348213639, 0.059825251, 2.126097372, 1.113670052, -1.225650921, 2.536621726), 0.14),
]

FRONT_DROPOFF_POSES = [
    (RobotPose(0.584776797, 0.335941793, 1.960427447, 1.11060209, -0.741864204, 3.051087787), 0.62),
    (RobotPose(0.584776797, 0.335941793, 1.960427447, 1.11060209, -0.741864204, 2.551087787), 0.17),
    (RobotPose(0.635689412, 0.141126232, 2.034058525, 1.086058398, -0.889708857, 2.758097457), 0.27),
]

BACK_DROPOFF_POSES = [
    (RobotPose(-0.09817477, 0.018407769, 2.205922623, 1.063048686, -1.659767484, 3.224835364), 0.95),
    (RobotPose(-0.09817477, 0.018407769, 2.205922623, 1.063048686, -1.659767484, 2.536621726), 0.175),
]

PUSH_OFF_POSES = [
    (RobotPose(0.931126338, 0.352815581, 1.684310905, 0.975029284, -0.878971263, 2.721650903), 0.125),
    (RobotPose(0.920388473, 0.415708794, 1.998776967, 0.65761176, -0.878971263, 3.121650903), 0.23),
    (RobotPose(-0.403436947, 0.181009733, 2.462039165, 0.559902988, -1.67165101, 3.118582942), 0.5),
]

PUSH_ON_HALF_POSES = [
    (RobotPose(-0.242368964, -0.073631078, 2.02485464, 1.283941919, -0.302194215, 3.118582942), 0.01),
    (RobotPose(0.862097203, 0.162601964, 1.681242944, 1.374446786, 0.776194279, 3.113980999), 0.28),
]

PUSH_ON_FULL_POSES = [
    (RobotPose(1.141281706, 0.794602048, 0.682621451, 1.529378846, 1.038504993, 3.106311095), 1.6),
    (RobotPose(1.224116669, 0.849825356, 0.957204012, 1.222582688, 1.199572976, 3.092505268), 0.7),
    (RobotPose(1.113670052, 0.656543777, 1.435806017, 1.135145783, 1.12900986, 3.112447019), 0.2),
    (RobotPose(0.882038953, 0.460194236, 1.94662162, 0.960271973, 0.983281685, 3.121650903), 0.2),
    (RobotPose(0.883572934, 0.274582561, 1.702718675, 1.288543862, 0.912718569, 3.113980999), 0.35),
]

BACK_PUSH_POSES = [
    (RobotPose(1.141281706, 0.794602048, 0.682621451, 1.529378846, 1.038504993, 3.106311095), 0.52),
    (RobotPose(1.224116669, 0.849825356, 0.957204012, 1.222582688, 1.199572976, 3.092505268), 0.15),
    (RobotPose(1.113670052, 0.656543777, 1.435806017, 1.135145783, 1.12900986, 3.112447019), 0.135),
    (RobotPose(0.882038953, 0.460194236, 1.94662162, 0.960271973, 0.983281685, 3.121650903), 0.1),
    (RobotPose(0.883572934, 0.274582561, 1.702718675, 1.288543862, 0.912718569, 3.113980999), 0.25),
]

FAR_MIDDLE_POSES = [
    (RobotPose(1.093728302, 0.608990373, 1.049242859, 1.500233211, -0.549165122, 3.117048961), 2.5),
    (RobotPose(1.093728302, 0.608990373, 1.049242859, 1.500233211, -0.549165122, 2.517048961), 0.5),
]


def create_state_registry():
    """Create the state registry with all available states"""
    return {
        "Home": lambda: PoseState("Home", [(HOME_POSE, 0.1)]),
        "LeftPickup": lambda: PoseState("Left Pickup", LEFT_PICKUP_POSES),
        "MiddleDropoff": lambda: PoseState("Middle Dropoff", MIDDLE_DROPOFF_POSES),
        "FrontDropoff": lambda: PoseState("Front Dropoff", FRONT_DROPOFF_POSES),
        "BackDropoff": lambda: PoseState("Back Dropoff", BACK_DROPOFF_POSES),
        "PushOff": lambda: PoseState("Push Off", PUSH_OFF_POSES),
        "PushOnHalf": lambda: PoseState("Push On", PUSH_ON_HALF_POSES, acc=255),
        "PushOnFull": lambda: PoseState("Push On", PUSH_ON_FULL_POSES, acc=255),
        "BackPush": lambda: PoseState("Back Push", BACK_PUSH_POSES, acc=255),
        "FarMiddle": lambda: PoseState("Far Middle Dropoff", FAR_MIDDLE_POSES),
        "Wait": lambda: WaitForInputState("Wait For Input"),
        "SelectDropoff": lambda: DropoffSelectionState("Select Dropoff", {
            "1": "Middle Dropoff",
            "2": "Front Dropoff",
            "3": "Back Dropoff",
            "4": "Far Middle Dropoff"
        }),
    }


class StateMachine:
    """Manages execution of robot arm states"""

    def __init__(self, ip_addr: str, state_registry: dict):
        self.ip_addr = ip_addr
        self.session = requests.Session()
        self.states = []
        self.state_registry = state_registry

    def add_state(self, state: RobotState) -> 'StateMachine':
        """Add a state to the execution sequence"""
        self.states.append(state)
        return self

    def add_states_from_sequence(self, sequence: List[str]) -> 'StateMachine':
        """Add states from a list of state names"""
        for state_name in sequence:
            if state_name in self.state_registry:
                self.states.append(self.state_registry[state_name]())
            else:
                print(f"⚠ Warning: Unknown state '{state_name}' - skipping")
        return self

    def run(self):
        """Execute all states in sequence"""
        print("\n" + "="*60)
        print(f"  ROBOT ARM STATE MACHINE")
        print(f"  Target IP: {self.ip_addr}")
        print(f"  Total States: {len(self.states)}")
        print("="*60)

        # Mapping from selection keys to state names
        dropoff_mapping = {
            "1": "MiddleDropoff",
            "2": "FrontDropoff",
            "3": "BackDropoff",
            "4": "FarMiddle"
        }

        try:
            i = 0
            while i < len(self.states):
                state = self.states[i]
                print(f"\n[{i+1}/{len(self.states)}] Starting: {state.name}")
                result = state.execute(self.ip_addr, self.session)

                if result == StateResult.SUCCESS:
                    print(f"[{i+1}/{len(self.states)}] ✓ COMPLETED: {state.name}")
                    i += 1
                elif result == "REPEAT":
                    print(f"[{i+1}/{len(self.states)}] ↶ REPEATING: {state.name}")
                    i -= 2
                elif result in dropoff_mapping:
                    # User selected a dropoff position, inject it into the sequence
                    dropoff_state_name = dropoff_mapping[result]
                    print(f"[{i+1}/{len(self.states)}] → INJECTING: {dropoff_state_name}")
                    self.states.insert(i + 1, self.state_registry[dropoff_state_name]())
                    i += 1
                elif result == StateResult.ABORT:
                    print(f"[{i+1}/{len(self.states)}] ⊘ ABORTED")
                    return
                else:
                    print(f"[{i+1}/{len(self.states)}] ✗ FAILED: {state.name}")
                    return

            print("\n" + "="*60)
            print("  ✓ STATE MACHINE COMPLETED SUCCESSFULLY!")
            print("="*60 + "\n")

        except KeyboardInterrupt:
            print("\n\n" + "="*60)
            print("  ⊘ Program terminated by user (Ctrl+C)")
            print("="*60 + "\n")
        finally:
            self.session.close()


def get_joints(ip_addr: str):
    """Get current joint positions and print as command string"""
    try:
        url = f"http://{ip_addr}/js?json={{'T':104}}"
        session = requests.Session()
        print("Fetching current joint positions...")
        response = session.get(url, timeout=0.5)
        print(f"Response: {response.text}")
        print("\nPress Ctrl+C to quit and print command string\n")

        # Keep fetching until user interrupts
        try:
            while True:
                response = session.get(url, timeout=0.5)
                print(f"Positions: {response.text}")
                time.sleep(0.5)
        except KeyboardInterrupt:
            print("\n\nFinal positions command string:")
            print(response.text)
            session.close()
    except Exception as e:
        print(f"Error: {e}")


def main():
    parser = argparse.ArgumentParser(description="Robot Arm State Machine Controller")
    parser.add_argument("ip", type=str, help="IP address (e.g., 192.168.4.1)")
    parser.add_argument("--get-joints", action="store_true", help="Get current joint positions")
    args = parser.parse_args()

    if args.get_joints:
        get_joints(args.ip)
        return

    sequence = [
        "Home",
        "LeftPickup",
        "SelectDropoff",  # User selects dropoff with number keys
        "PushOff",
        "Home",
    ]

    state_registry = create_state_registry()
    machine = StateMachine(args.ip, state_registry)
    machine.add_states_from_sequence(sequence)
    machine.run()


if __name__ == "__main__":
    main()