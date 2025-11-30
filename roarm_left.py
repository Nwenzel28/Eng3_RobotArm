import requests
import argparse
import time
from enum import Enum, auto
from typing import List, Tuple, Optional


class StateResult(Enum):
    """Return values for state execution"""
    SUCCESS = auto()
    FAILURE = auto()
    ABORT = auto()


class RobotState:
    """Base class for robot arm states"""
    
    def __init__(self, name: str):
        self.name = name
    
    def execute(self, ip_addr: str) -> StateResult:
        """
        Execute this state. Override in subclasses.
        Returns StateResult indicating success/failure.
        """
        raise NotImplementedError
    
    def _send_command(self, ip_addr: str, command_str: str, delay: float) -> StateResult:
        """Helper method to send a command and wait"""
        try:
            url = f"http://{ip_addr}/js?json={command_str}"
            print(f"    → Sending command...")
            response = requests.get(url, timeout=5)
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


# ============================================================================
# SAMPLE STATE TEMPLATE - Copy and modify this for each new state
# ============================================================================
class TemplateState(RobotState):
    """
    Template state - copy this for new states.
    Replace 'Template' with your state name and update commands list.
    """
    
    def __init__(self):
        super().__init__("Template")
    
    def execute(self, ip_addr: str) -> StateResult:
        print(f"\n{'='*60}")
        print(f"  STATE: {self.name}")
        print(f"{'='*60}")
        
        # Define your command sequence here
        # Format: (command_string, delay_in_seconds)
        commands: List[Tuple[str, float]] = [
            ('{"T":102,"base":0.0,"shoulder":0.0,"elbow":0.0,"wrist":0.0,"roll":0.0,"hand":0.0,"spd":0,"acc":10}', 2.0),
        ]
        
        for i, (command, delay) in enumerate(commands, 1):
            print(f"  Step {i}/{len(commands)}:")
            result = self._send_command(ip_addr, command, delay)
            if result != StateResult.SUCCESS:
                return result
        
        return StateResult.SUCCESS


# ============================================================================
# ACTUAL STATES - Your robot arm states
# ============================================================================
class HomeState(RobotState):
    """Return robot arm to home position"""
    
    def __init__(self):
        super().__init__("Home")
    
    def execute(self, ip_addr: str) -> StateResult:
        print(f"\n{'='*60}")
        print(f"  STATE: {self.name}")
        print(f"{'='*60}")
        commands = [
            ('{"T":102,"base":0.033747577,"shoulder":-0.093572828,"elbow":1.610679827,"wrist":0.013805827,"roll":0,"hand":1.578466231,"spd":0,"acc":50}', 1.0),
        ]
        for i, (command, delay) in enumerate(commands, 1):
            print(f"  Step {i}/{len(commands)}:")
            result = self._send_command(ip_addr, command, delay)
            if result != StateResult.SUCCESS:
                return result
        return StateResult.SUCCESS


class LeftPickupState(RobotState):
    """Execute left pickup sequence"""
    
    def __init__(self):
        super().__init__("Left Pickup")
    
    def execute(self, ip_addr: str) -> StateResult:
        print(f"\n{'='*60}")
        print(f"  STATE: {self.name}")
        print(f"{'='*60}")
        commands = [
            #Initial Pos
            ('{"T":102,"base":1.333029305,"shoulder":-0.187145656,"elbow":2.296369239,"wrist":1.164291418,"roll":2.925301362,"hand":2.813320765,"spd":0,"acc":100}', 1.0),
            
            #Go Down
            ('{"T":102,"base":1.279339977,"shoulder":0.230097118,"elbow":2.58935957,"wrist":0.527689391,"roll":2.925301362,"hand":2.813320765,"spd":0,"acc":100}', 2.0),
            #close claw
            ('{"T":102,"base":1.279339977,"shoulder":0.230097118,"elbow":2.58935957,"wrist":0.527689391,"roll":2.925301362,"hand":3.112447019,"spd":0,"acc":100}', 0.75),
            
            #lift up
            ('{"T":102,"base":1.412971055,"shoulder":-0.159534002,"elbow":2.370000317,"wrist":1.015495282,"roll":2.906893593,"hand":3.126252846,"spd":0,"acc":100}',1.25)
        ]
        for i, (command, delay) in enumerate(commands, 1):
            print(f"  Step {i}/{len(commands)}:")
            result = self._send_command(ip_addr, command, delay)
            if result != StateResult.SUCCESS:
                return result
        return StateResult.SUCCESS


class MiddleDropoffState(RobotState):
    """Execute middle dropoff sequence"""
    
    def __init__(self):
        super().__init__("Middle Dropoff")
    
    def execute(self, ip_addr: str) -> StateResult:
        print(f"\n{'='*60}")
        print(f"  STATE: {self.name}")
        print(f"{'='*60}")
        commands = [
            
            ('{"T":102,"base":0.348213639,"shoulder":0.059825251,"elbow":2.126097372,"wrist":1.113670052,"roll":1.915942004,"hand":3.113980999,"spd":0,"acc":100}', 0.75),
            ('{"T":102,"base":0.348213639,"shoulder":0.059825251,"elbow":2.126097372,"wrist":1.113670052,"roll":1.915942004,"hand":2.736621726,"spd":0,"acc":100}', 0.5),
        ]
        for i, (command, delay) in enumerate(commands, 1):
            print(f"  Step {i}/{len(commands)}:")
            result = self._send_command(ip_addr, command, delay)
            if result != StateResult.SUCCESS:
                return result
        return StateResult.SUCCESS


class FrontDropoffState(RobotState):
    """Execute front dropoff sequence"""
    
    def __init__(self):
        super().__init__("Front Dropoff")
    
    def execute(self, ip_addr: str) -> StateResult:
        print(f"\n{'='*60}")
        print(f"  STATE: {self.name}")
        print(f"{'='*60}")
        commands = [
            
            (' {"T":102,"base":0.644271931,"shoulder":0.187145656,"elbow":1.958893466,"wrist":1.191903072,"roll":2.262621662,"hand":3.123980999,"spd":0,"acc":100}', 0.75),
            (' {"T":102,"base":0.644271931,"shoulder":0.187145656,"elbow":1.958893466,"wrist":1.191903072,"roll":2.262621662,"hand":2.736621726,"spd":0,"acc":100}', 0.5),

        ]
        for i, (command, delay) in enumerate(commands, 1):
            print(f"  Step {i}/{len(commands)}:")
            result = self._send_command(ip_addr, command, delay)
            if result != StateResult.SUCCESS:
                return result
        return StateResult.SUCCESS


class BackDropoffState(RobotState):
    """Execute back dropoff sequence"""
    
    def __init__(self):
        super().__init__("Back Dropoff")
    
    def execute(self, ip_addr: str) -> StateResult:
        print(f"\n{'='*60}")
        print(f"  STATE: {self.name}")
        print(f"{'='*60}")
        commands = [
            ('{"T":102,"base":-0.09817477,"shoulder":0.018407769,"elbow":2.185922623,"wrist":1.063048686,"roll":1.481825441,"hand":3.224835364,"spd":0,"acc":100}', 1.0),
            ('{"T":102,"base":-0.09817477,"shoulder":0.018407769,"elbow":2.185922623,"wrist":1.063048686,"roll":1.481825441,"hand":2.736621726,"spd":0,"acc":100}', 0.75),

        ]
        for i, (command, delay) in enumerate(commands, 1):
            print(f"  Step {i}/{len(commands)}:")
            result = self._send_command(ip_addr, command, delay)
            if result != StateResult.SUCCESS:
                return result
        return StateResult.SUCCESS
    

class PushOffState(RobotState):
    """Execute push off  sequence"""
    
    def __init__(self):
        super().__init__("Middle Dropoff")
    
    def execute(self, ip_addr: str) -> StateResult:
        print(f"\n{'='*60}")
        print(f"  STATE: {self.name}")
        print(f"{'='*60}")
        commands = [
            ('{"T":102,"base":0.931126338,"shoulder":0.352815581,"elbow":1.684310905,"wrist":1.175029284,"roll":0.943398185,"hand":3.121650903,"spd":0,"acc":100}',1.0),
            ('{"T":102,"base":0.920388473,"shoulder":0.415708794,"elbow":1.998776967,"wrist":0.81761176,"roll":1.004757416,"hand":3.121650903,"spd":0,"acc":100}', 0.75),
            ('{"T":102,"base":-0.403436947,"shoulder":0.181009733,"elbow":2.462039165,"wrist":0.559902988,"roll":-0.391165101,"hand":3.118582942,"spd":0,"acc":100}', 1.25),
            
        ]
        for i, (command, delay) in enumerate(commands, 1):
            print(f"  Step {i}/{len(commands)}:")
            result = self._send_command(ip_addr, command, delay)
            if result != StateResult.SUCCESS:
                return result
        return StateResult.SUCCESS

class PushOnState(RobotState):
    """Execute push on sequence"""
    
    def __init__(self):
        super().__init__("Middle Dropoff")
    
    def execute(self, ip_addr: str) -> StateResult:
        print(f"\n{'='*60}")
        print(f"  STATE: {self.name}")
        print(f"{'='*60}")
        commands = [
            ('{"T":102,"base":-0.242368964,"shoulder":-0.073631078,"elbow":2.02485464,"wrist":1.283941919,"roll":-0.302194215,"hand":3.118582942,"spd":0,"acc":10}',1.5),
            ('{"T":102,"base":0.862097203,"shoulder":0.162601964,"elbow":1.681242944,"wrist":1.374446786,"roll":0.776194279,"hand":3.113980999,"spd":0,"acc":10}',2.0),
            ('{"T":102,"base":1.141281706,"shoulder":0.794602048,"elbow":0.682621451,"wrist":1.529378846,"roll":1.038504993,"hand":3.106311095,"spd":0,"acc":10}',2.5),
            ('{"T":102,"base":1.141281706,"shoulder":0.951068088,"elbow":0.690291355,"wrist":1.472621556,"roll":1.12900986,"hand":3.109379057,"spd":0,"acc":10}',1.0),
            ('{"T":102,"base":1.113670052,"shoulder":0.656543777,"elbow":1.435806017,"wrist":1.135145783,"roll":1.12900986,"hand":3.112447019,"spd":0,"acc":10}',1.25),
            ('{"T":102,"base":0.882038953,"shoulder":0.460194236,"elbow":1.94662162,"wrist":0.960271973,"roll":0.983281685,"hand":3.121650903,"spd":0,"acc":10}',1.5),
            ('{"T":102,"base":0.883572934,"shoulder":0.274582561,"elbow":1.702718675,"wrist":1.288543862,"roll":0.912718569,"hand":3.113980999,"spd":0,"acc":10}',1.0),
            
           


        ]
        for i, (command, delay) in enumerate(commands, 1):
            print(f"  Step {i}/{len(commands)}:")
            result = self._send_command(ip_addr, command, delay)
            if result != StateResult.SUCCESS:
                return result
        return StateResult.SUCCESS


class WaitForInputState(RobotState):
    """Pause and wait for user input"""
    
    def __init__(self):
        super().__init__("Wait For Input")
    
    def execute(self, ip_addr: str) -> StateResult:
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
# STATE MACHINE RUNNER
# ============================================================================
class StateMachine:
    """Manages execution of robot arm states"""
    
    def __init__(self, ip_addr: str):
        self.ip_addr = ip_addr
        self.states: List[RobotState] = []
    
    def add_state(self, state: RobotState):
        """Add a state to the execution sequence"""
        self.states.append(state)
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
                result = state.execute(self.ip_addr)
                
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
    machine = StateMachine(args.ip)
    
    # Add states in the order you want them executed
    machine.add_state(HomeState())

    machine.add_state(LeftPickupState())
    machine.add_state(MiddleDropoffState())
    machine.add_state(WaitForInputState())  # Uncomment to add pause
    machine.add_state(LeftPickupState())
    machine.add_state(BackDropoffState())
    machine.add_state(WaitForInputState())  # Uncomment to add pause
    machine.add_state(LeftPickupState())
    machine.add_state(FrontDropoffState())

    #----------------------------
    # ADD PUSH NEXT CAR FEATcleaURE    
    #----------------------------
    machine.add_state(WaitForInputState())  # Uncomment to add pause
    machine.add_state(PushOffState())
    machine.add_state(WaitForInputState())  # Uncomment to add pause
    machine.add_state(PushOnState()) #DO NOT UNCOMMENT - MAY DAMAGE ROBOT ARM

    #Reapeat the dropoff sequence


    machine.add_state(HomeState())
    
    # Run the state machine
    machine.run()


if __name__ == "__main__":
    main()