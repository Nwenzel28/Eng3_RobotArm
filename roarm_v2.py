import requests
import argparse
import time
from enum import Enum, auto
from typing import List, Tuple, Dict, Type


class StateResult(Enum):
    """Return values for state execution"""
    SUCCESS = auto()
    FAILURE = auto()
    ABORT = auto()


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================
def make_t102_command(base: float, shoulder: float, elbow: float, 
                      wrist: float, roll: float, hand: float, 
                      spd: int = 0, acc: int = 255) -> str:
    """Generate T:102 command string"""
    return (f'{{"T":102,"base":{base},"shoulder":{shoulder},"elbow":{elbow},'
            f'"wrist":{wrist},"roll":{roll},"hand":{hand},"spd":{spd},"acc":{acc}}}')


# ============================================================================
# BASE STATE CLASS
# ============================================================================
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
            response = session.get(url, timeout=0.5)
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
    """Simplified state with common execute logic"""
    
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


# ============================================================================
# ROBOT ARM STATES (WITH ROTATED WRIST)
# ============================================================================
class HomeState(SimpleRobotState):
    """Return robot arm to home position"""
    def __init__(self):
        super().__init__("Home", [
            (make_t102_command(1.247126381, -0.139592252, 2.135301257, 1.239456477, -0.360485485, 2.517048961), 0.5),
        ])


class LeftPickupState(SimpleRobotState):
    """Execute left pickup sequence (roll rotated 180° CCW)"""
    def __init__(self):
        super().__init__("Left Pickup", [
            #Go to initial position
            (make_t102_command(1.333029305, -0.057145656, 2.226369239, 1.164291418, -0.216291563, 2.413320765), 0.66),
            #Go Down
            (make_t102_command(1.279339977, 0.230097118, 2.58935957, 0.527689391, -0.216291563, 2.553320765), 0.43),
            #Close Claw
            (make_t102_command(1.290077843, 0.176407791, 2.658388705, 0.40803889, -0.260776734, 3.183301384), 0.15),
            #Go Up
            (make_t102_command(1.412971055, -0.159534002, 2.370000317, 1.015495282, -0.234699332, 3.126252846), 0.14),
        ])


class MiddleDropoffState(SimpleRobotState):
    """Execute middle dropoff sequence (roll rotated 180° CCW)"""
    def __init__(self):
        super().__init__("Middle Dropoff", [
            (make_t102_command(0.348213639, 0.059825251, 2.126097372, 1.113670052, -1.225650921, 3.113980999), 0.62),
            (make_t102_command(0.348213639, 0.059825251, 2.126097372, 1.113670052, -1.225650921, 2.536621726), 0.14),
        ])


class FrontDropoffState(SimpleRobotState):
    """Execute front dropoff sequence (roll rotated 180° CCW)"""
    def __init__(self):
        super().__init__("Front Dropoff", [
            (make_t102_command(0.644271931, 0.187145656, 1.958893466, 1.191903072, -0.878971263, 3.123980999), 0.62),
            (make_t102_command(0.644271931, 0.187145656, 1.958893466, 1.191903072, -0.878971263, 2.536621726), 0.14),
        ])


class BackDropoffState(SimpleRobotState):
    """Execute back dropoff sequence (roll rotated 180° CCW)"""
    def __init__(self):
        super().__init__("Back Dropoff", [
            (make_t102_command(-0.09817477, 0.018407769, 2.205922623, 1.063048686, -1.659767484, 3.224835364), 0.95),
            (make_t102_command(-0.09817477, 0.018407769, 2.205922623, 1.063048686, -1.659767484, 2.536621726), 0.175),
        ])


class PushOffState(SimpleRobotState):
    """Execute push off sequence"""
    def __init__(self):
        super().__init__("Push Off", [
            (make_t102_command(0.931126338, 0.352815581, 1.684310905, 0.975029284, -0.878971263, 3.121650903), 0.275),
            (make_t102_command(0.920388473, 0.415708794, 1.998776967, 0.65761176, -0.878971263, 3.121650903), 0.25),
            (make_t102_command(-0.403436947, 0.181009733, 2.462039165, 0.559902988, -1.67165101, 3.118582942), 1.2),
        ])


class PushOnState(SimpleRobotState):
    """Execute push on sequence"""
    def __init__(self):
        super().__init__("Push On", [
            #Lift Up
            (make_t102_command(-0.242368964, -0.073631078, 2.02485464, 1.283941919, -0.302194215, 3.118582942, acc=255), 0.01),
            #Halfway
            (make_t102_command(0.862097203, 0.162601964, 1.681242944, 1.374446786, 0.776194279, 3.113980999, acc=255), 0.28),
            #Full Ways
            (make_t102_command(1.141281706, 0.794602048, 0.682621451, 1.529378846, 1.038504993, 3.106311095, acc=255), 0.52),
            #Hop 1
            (make_t102_command(1.224116669, 0.849825356, 0.957204012, 1.222582688, 1.199572976, 3.092505268, acc=255), 0.2),
            #hop 2
            (make_t102_command(1.113670052, 0.656543777, 1.435806017, 1.135145783, 1.12900986, 3.112447019, acc=255), 0.14),
            #halfway
            (make_t102_command(0.882038953, 0.460194236, 1.94662162, 0.960271973, 0.983281685, 3.121650903, acc=255), 0.2),
            #Finish
            (make_t102_command(0.883572934, 0.274582561, 1.702718675, 1.288543862, 0.912718569, 3.113980999, acc=255), 0.35),
        ])

class BackPushState(SimpleRobotState):
    """Execute back push on sequence"""
    def __init__(self):
        super().__init__("Push On", [
            #Need?
            (make_t102_command(1.141281706, 0.794602048, 0.682621451, 1.529378846, 1.038504993, 3.106311095, acc=255), 0.52),
            #Hop 1
            (make_t102_command(1.224116669, 0.849825356, 0.957204012, 1.222582688, 1.199572976, 3.092505268, acc=255), 0.15),
            #hop 2
            (make_t102_command(1.113670052, 0.656543777, 1.435806017, 1.135145783, 1.12900986, 3.112447019, acc=255), 0.135),
            #halfway
            (make_t102_command(0.882038953, 0.460194236, 1.94662162, 0.960271973, 0.983281685, 3.121650903, acc=255), 0.1),
            #Finish
            (make_t102_command(0.883572934, 0.274582561, 1.702718675, 1.288543862, 0.912718569, 3.113980999, acc=255), 0.25),
        ])

class FarMiddleDropoffState(SimpleRobotState):
    """Execute Far Middle Dropoff sequence"""
    def __init__(self):
        super().__init__("Push Off", [
            
            (make_t102_command(1.093728302, 0.608990373, 1.049242859, 1.500233211, -0.549165122, 3.117048961), 2.5),
            (make_t102_command(1.093728302, 0.608990373, 1.049242859, 1.500233211, -0.549165122, 2.517048961), 0.5),
        ])
        

class WaitForInputState(RobotState):
    """Pause and wait for user input"""
    def __init__(self):
        super().__init__("Wait For Input")
    
    def execute(self, ip_addr: str, session: requests.Session) -> StateResult:
        print(f"\n{'='*60}")
        print(f"  STATE: {self.name}")
        print(f"{'='*60}")
        print(f"  ⏸  Press ENTER to continue...")
        try:
            input()
            return StateResult.SUCCESS
        except (KeyboardInterrupt, EOFError):
            print("  ⊘ Aborted by user")
            return StateResult.ABORT


# ============================================================================
# STATE REGISTRY
# ============================================================================
STATE_REGISTRY: Dict[str, Type[RobotState]] = {
    "Home": HomeState,
    "LeftPickup": LeftPickupState,
    "MiddleDropoff": MiddleDropoffState,
    "FrontDropoff": FrontDropoffState,
    "BackDropoff": BackDropoffState,
    "PushOff": PushOffState,
    "PushOn": PushOnState,
    "FarMiddle": FarMiddleDropoffState,
    "BackPush": BackPushState,
    "Wait": WaitForInputState,

}


# ============================================================================
# STATE MACHINE RUNNER
# ============================================================================
class StateMachine:
    """Manages execution of robot arm states"""
    
    def __init__(self, ip_addr: str):
        self.ip_addr = ip_addr
        self.session = requests.Session()
        self.states: List[RobotState] = []
    
    def add_state(self, state: RobotState):
        """Add a state to the execution sequence"""
        self.states.append(state)
        return self
    
    def add_states_from_sequence(self, sequence: List[str]):
        """Add states from a list of state names"""
        for state_name in sequence:
            if state_name in STATE_REGISTRY:
                self.states.append(STATE_REGISTRY[state_name]())
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
        
        try:
            for i, state in enumerate(self.states, 1):
                print(f"\n[{i}/{len(self.states)}] Starting: {state.name}")
                result = state.execute(self.ip_addr, self.session)
                
                if result == StateResult.SUCCESS:
                    print(f"[{i}/{len(self.states)}] ✓ COMPLETED: {state.name}")
                elif result == StateResult.ABORT:
                    print(f"[{i}/{len(self.states)}] ⊘ ABORTED")
                    return
                else:
                    print(f"[{i}/{len(self.states)}] ✗ FAILED: {state.name}")
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


# ============================================================================
# MAIN - Configure your state sequence here
# ============================================================================
def main():
    parser = argparse.ArgumentParser(description="Robot Arm State Machine Controller")
    parser.add_argument("ip", type=str, help="IP address (e.g., 192.168.4.1)")
    args = parser.parse_args()
    
    # ========================================
    # CONFIGURE YOUR STATE SEQUENCE HERE
    # ========================================
    sequence = [
        "Home",

        

        "LeftPickup",
        "MiddleDropoff",

        #"Wait",
        #"LeftPickup",
        #"BackDropoff",

        "Wait",
        "LeftPickup",
        "FrontDropoff",

        "Wait",
        "PushOff",

        #"Wait",
        #"LeftPickup",
        #"FarMiddle",

        #"Wait",
        #"BackPush",

        #"BackDropoff",
        #"Wait",


        "PushOn",  
        "Home",
    ]
    
    machine = StateMachine(args.ip)
    machine.add_states_from_sequence(sequence)
    
    # Run the state machine
    machine.run()


if __name__ == "__main__":
    main()