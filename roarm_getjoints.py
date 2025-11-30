import requests
import argparse
import json
from enum import Enum, auto
from typing import Optional


class StateResult(Enum):
    """Return values for state execution"""
    SUCCESS = auto()
    FAILURE = auto()
    QUIT = auto()


class RecorderState:
    """Base class for recorder states"""
    
    def __init__(self, name: str):
        self.name = name
    
    def execute(self, ip_addr: str) -> StateResult:
        """Execute this state. Override in subclasses."""
        raise NotImplementedError


class MenuState(RecorderState):
    """Display menu and get user choice"""
    
    def __init__(self):
        super().__init__("Menu")
    
    def execute(self, ip_addr: str) -> StateResult:
        print("\n" + "="*60)
        print("  ROBOT ARM POSITION RECORDER")
        print("="*60)
        print("\n  Options:")
        print("    [ENTER] - Record current position (T:105)")
        print("    [q] - Quit")
        print("\n" + "="*60)
        
        choice = input("  Your choice: ").strip().lower()
        
        if choice == 'q':
            return StateResult.QUIT
        elif choice == '':
            return StateResult.SUCCESS
        else:
            print("  ⚠ Invalid choice. Press ENTER to record or 'q' to quit.")
            return StateResult.SUCCESS


class RecordPositionState(RecorderState):
    """Send T:105 command and convert response to T:102 format"""
    
    def __init__(self):
        super().__init__("RecordPosition")
    
    def execute(self, ip_addr: str) -> StateResult:
        print("\n" + "-"*60)
        print("  Recording Position...")
        print("-"*60)
        
        try:
            # Send T:105 command to get current position
            url = f"http://{ip_addr}/js?json=" + '{"T":105}'
            print(f"  → Sending T:105 command...")
            response = requests.get(url, timeout=5)
            
            print(f"  ✓ Response received")
            
            # Parse the JSON response
            try:
                data = json.loads(response.text)
                
                # Extract both joint angles AND XYZ coordinates from T:105 response
                has_joints = all(key in data for key in ['b', 's', 'e', 't', 'r', 'g'])
                has_coords = all(key in data for key in ['x', 'y', 'z', 'tit', 'r', 'g'])
                
                if has_joints and has_coords:
                    # Joint angles for T:102
                    base = data['b']
                    shoulder = data['s']
                    elbow = data['e']
                    wrist = data['t']  # 't' in joint angles = wrist joint
                    roll = data['r']
                    hand = data['g']
                    
                    # XYZ coordinates for T:1041
                    x = data['x']
                    y = data['y']
                    z = data['z']
                    tilt = data['tit']  # 'tit' in coordinates = tilt/pitch angle
                    r = data['r']
                    g = data['g']
                    
                    # Create T:102 command format
                    t102_command = (
                        f'(make_t102_command({base}, {shoulder}, {elbow}, '
                        f'{wrist}, {roll}, {hand}), 0.5),'
                    )
                    
                    # Create T:1041 command format with correct tilt parameter
                    t1041_command = (
                        f'(make_t1041_command({x}, {y}, {z}, '
                        f'{tilt}, {r}, {g}), 0.5),'
                    )
                    
                    print("\n" + "="*60)
                    print("  ✓ POSITION RECORDED")
                    print("="*60)
                    print(f"\n  T:102 (Joint Control):")
                    print(f"    {t102_command}")
                    print(f"\n  T:1041 (Cartesian Control):")
                    print(f"    {t1041_command}")
                    print("\n" + "="*60)
                    print("  Copy either line above and paste into your state commands")
                    print("  T:102 = Joint angle control (curved paths)")
                    print("  T:1041 = Cartesian control (straight-line paths)")
                    print("  (Default delay: 0.5s - adjust as needed)")
                    print("="*60 + "\n")
                    
                else:
                    print(f"  ⚠ Response missing required fields")
                    print(f"  Raw response: {response.text}")
                
            except json.JSONDecodeError:
                print(f"  ⚠ Could not parse JSON response")
                print(f"  Raw response: {response.text}")
            
            return StateResult.SUCCESS
            
        except requests.exceptions.Timeout:
            print(f"  ✗ Timeout - no response received")
            return StateResult.FAILURE
        except requests.exceptions.RequestException as e:
            print(f"  ✗ HTTP error: {e}")
            return StateResult.FAILURE
        except Exception as e:
            print(f"  ✗ Unexpected error: {e}")
            return StateResult.FAILURE


class RecorderStateMachine:
    """State machine for recording robot positions"""
    
    def __init__(self, ip_addr: str):
        self.ip_addr = ip_addr
        self.menu_state = MenuState()
        self.record_state = RecordPositionState()
    
    def run(self):
        """Run the recorder state machine"""
        print("\n" + "="*60)
        print("  ROBOT ARM POSITION RECORDER")
        print(f"  Target IP: {self.ip_addr}")
        print("="*60)
        print("\n  Manually move the robot arm to desired positions.")
        print("  Press ENTER to record each position.")
        print("  Outputs both T:102 (joint) and T:1041 (cartesian) formats.")
        print("="*60)
        
        try:
            while True:
                # Show menu
                result = self.menu_state.execute(self.ip_addr)
                
                if result == StateResult.QUIT:
                    print("\n" + "="*60)
                    print("  Exiting recorder...")
                    print("="*60 + "\n")
                    break
                
                # Record position
                result = self.record_state.execute(self.ip_addr)
                
                if result == StateResult.FAILURE:
                    print("  ⚠ Failed to record position. Try again.")
                
        except KeyboardInterrupt:
            print("\n\n" + "="*60)
            print("  ⊘ Program terminated by user (Ctrl+C)")
            print("="*60 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="Record robot arm positions in both T:102 and T:1041 formats"
    )
    parser.add_argument("ip", type=str, help="IP address (e.g., 192.168.4.1)")
    args = parser.parse_args()
    
    # Create and run the recorder
    recorder = RecorderStateMachine(args.ip)
    recorder.run()


if __name__ == "__main__":
    main()