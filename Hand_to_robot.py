#!/usr/bin/env python3
"""
Home Position then X-Y-Z Axis + Gripper Control
===============================================
First moves Dobot to home position, then allows full 3D control + gripper.
Move your wrist to control all 3 axes: left/right, up/down, forward/back.
Open/close your hand to control the gripper.
"""

import cv2
import mediapipe as mp
import time
import glob
import numpy as np
from pydobot import Dobot

class WristXYZController:
    def __init__(self, x_range=(200, 300), y_range=(-100, 100), z_range=(50, 250)):
        # Initialize MediaPipe hands
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.5
        )
        self.mp_draw = mp.solutions.drawing_utils
        
        # X, Y and Z axis ranges (min, max) in mm
        self.x_min, self.x_max = x_range  # Forward/back
        self.y_min, self.y_max = y_range  # Left/right
        self.z_min, self.z_max = z_range  # Up/down
        
        # Camera frame bounds for wrist tracking (expanded for better range)
        self.camera_bounds = {
            'x_min': 0.15, 'x_max': 0.85,  # Expanded from 0.2-0.8 for more range
            'y_min': 0.15, 'y_max': 0.85   # Expanded from 0.2-0.8 for more range
        }
        
        # Movement smoothing (reduced for faster response)
        self.last_x = None
        self.last_y = None
        self.last_z = None
        self.xyz_history = []
        self.history_size = 2  # Reduced from 3 to 2 for faster response
        self.min_movement_threshold = 1  # Reduced from 2 to 1mm for more sensitivity
        
        # Gripper control (reduced delay)
        self.last_gripper_state = None
        self.gripper_state_change_time = 0
        self.min_gripper_state_duration = 0.3  # Reduced from 0.5 to 0.3 seconds
        
        # Current robot position (will be updated after homing)
        # For this Dobot: X=forward/back, Y=left/right, Z=up/down
        self.current_r = 0  # Store home R (rotation)
        
    def map_wrist_to_xyz(self, wrist_x, wrist_y, hand_landmarks):
        """
        Map normalized wrist position and hand depth to robot X,Y,Z coordinates.
        
        Args:
            wrist_x: Normalized wrist X position (0-1, where 0=left, 1=right)
            wrist_y: Normalized wrist Y position (0-1, where 0=top, 1=bottom)
            hand_landmarks: MediaPipe hand landmarks for depth calculation
        
        Returns:
            (X, Y, Z) coordinates in robot coordinates (mm)
        """
        # Clamp wrist positions to valid range
        wrist_x = max(0.0, min(1.0, wrist_x))
        wrist_y = max(0.0, min(1.0, wrist_y))
        
        # Map X coordinate to Y-axis (left wrist = left robot, right wrist = right robot)
        robot_y = np.interp(wrist_x, 
                           [self.camera_bounds['x_min'], self.camera_bounds['x_max']], 
                           [self.y_min, self.y_max])
        
        # Map Y coordinate to Z-axis (top wrist = high robot, bottom wrist = low robot)
        robot_z = np.interp(wrist_y, 
                           [self.camera_bounds['y_min'], self.camera_bounds['y_max']], 
                           [self.z_max, self.z_min])  # Inverted: top = high Z, bottom = low Z
        
        # Calculate hand size to estimate depth (larger hand = closer, smaller hand = farther)
        # Use distance between thumb tip and pinky tip as size indicator
        thumb_tip = hand_landmarks[4]  # Thumb tip
        pinky_tip = hand_landmarks[20]  # Pinky tip
        
        # Calculate hand span (width) in normalized coordinates
        hand_span = np.sqrt((thumb_tip.x - pinky_tip.x)**2 + (thumb_tip.y - pinky_tip.y)**2)
        
        # Map hand span to robot X (forward/back) - larger span = closer = forward
        # Typical hand span ranges from ~0.1 (far) to ~0.25 (close)
        robot_x = np.interp(hand_span, [0.08, 0.25], [self.x_max, self.x_min])  # Inverted: large span = forward
        
        # Clamp to safe ranges
        robot_x = max(self.x_min, min(self.x_max, robot_x))
        robot_y = max(self.y_min, min(self.y_max, robot_y))
        robot_z = max(self.z_min, min(self.z_max, robot_z))
        
        return robot_x, robot_y, robot_z
    
    def smooth_xyz(self, new_x, new_y, new_z):
        """Apply smoothing to reduce jitter in XYZ movement."""
        self.xyz_history.append((new_x, new_y, new_z))
        
        # Keep only recent positions
        if len(self.xyz_history) > self.history_size:
            self.xyz_history.pop(0)
        
        # Calculate average position
        if len(self.xyz_history) == 1:
            return new_x, new_y, new_z
        
        avg_x = sum(pos[0] for pos in self.xyz_history) / len(self.xyz_history)
        avg_y = sum(pos[1] for pos in self.xyz_history) / len(self.xyz_history)
        avg_z = sum(pos[2] for pos in self.xyz_history) / len(self.xyz_history)
        
        return avg_x, avg_y, avg_z
    
    def should_move_xyz(self, new_x, new_y, new_z):
        """Determine if robot should move based on minimum threshold."""
        if self.last_x is None or self.last_y is None or self.last_z is None:
            return True
        
        # Calculate distance from last position in 3D
        dx = new_x - self.last_x
        dy = new_y - self.last_y
        dz = new_z - self.last_z
        distance = np.sqrt(dx**2 + dy**2 + dz**2)
        
        return distance >= self.min_movement_threshold
    
    def calculate_hand_openness(self, landmarks):
        """
        Calculate if hand is open or closed based on finger positions.
        Returns a value between 0 (closed) and 1 (open).
        """
        # Get landmark positions
        thumb_tip = landmarks[4]
        thumb_mcp = landmarks[2]
        index_tip = landmarks[8]
        index_pip = landmarks[6]
        middle_tip = landmarks[12]
        middle_pip = landmarks[10]
        ring_tip = landmarks[16]
        ring_pip = landmarks[14]
        pinky_tip = landmarks[20]
        pinky_pip = landmarks[18]
        
        # Count extended fingers
        extended_fingers = 0
        
        # Thumb (different logic due to orientation)
        if thumb_tip.x > thumb_mcp.x:  # Thumb extended (assuming right hand)
            extended_fingers += 1
            
        # Other fingers (tip should be above pip when extended)
        if index_tip.y < index_pip.y:
            extended_fingers += 1
        if middle_tip.y < middle_pip.y:
            extended_fingers += 1
        if ring_tip.y < ring_pip.y:
            extended_fingers += 1
        if pinky_tip.y < pinky_pip.y:
            extended_fingers += 1
            
        # Return openness ratio (0-1)
        return extended_fingers / 5.0
    
    def is_hand_open(self, landmarks):
        """
        Determine if hand is open or closed.
        Returns True for open, False for closed.
        """
        openness = self.calculate_hand_openness(landmarks)
        return openness > 0.6  # Threshold for "open" hand

def find_dobot_port():
    """Find the Dobot port automatically."""
    candidate_ports = (
        sorted(glob.glob('/dev/cu.usbmodem*')) +
        sorted(glob.glob('/dev/cu.usbserial*'))
    )
    
    for port in candidate_ports:
        try:
            dobot = Dobot(port)
            dobot.close()
            return port
        except:
            continue
    
    return None

def main():
    print("Home Position then X-Y-Z Axis + Gripper Control")
    print("=" * 48)
    print("Steps:")
    print("1. Connect to Dobot")
    print("2. Move to home position")
    print("3. Start full 3D + gripper control with hand gestures")
    print()
    print("Hand Control Instructions:")
    print("- Move your wrist to control robot position:")
    print("  • Wrist LEFT/RIGHT → Robot moves LEFT/RIGHT (Y-axis)")
    print("  • Wrist UP/DOWN → Robot moves UP/DOWN (Z-axis)")
    print("  • SPREAD/CLOSE fingers → Robot moves FORWARD/BACK (X-axis)")
    print("    * Spread fingers wide = Move FORWARD")
    print("    * Close fingers together = Move BACK")
    print("- Open/close your hand to control gripper:")
    print("  • Open hand → Open gripper")
    print("  • Closed hand (fist) → Close gripper")
    print("- Robot R (rotation) remains unchanged")
    print("- Press 'q' to quit")
    print("- Press 'c' to show current robot position")
    print()
    
    # Find and connect to Dobot
    port = find_dobot_port()
    if not port:
        print("✗ Could not find Dobot. Make sure it's connected via USB.")
        return
    
    try:
        # Step 1: Connect to Dobot
        print(f"Step 1: Connecting to Dobot on port: {port}")
        bot = Dobot(port)
        print("✓ Connected to Dobot!")
        
        # Show initial position
        initial_pose = bot.get_pose()
        print(f"Initial position: x={initial_pose.position.x:.1f}, y={initial_pose.position.y:.1f}, z={initial_pose.position.z:.1f}, r={initial_pose.position.r:.1f}")
        
        # Step 2: Move to home position
        print("\nStep 2: Moving to home position...")
        print("This may take a moment...")
        cmd_id = bot.home()
        if cmd_id:
            bot.wait_for_cmd(cmd_id)
        else:
            time.sleep(3)  # Wait a bit if no command ID returned
        print("✓ Moved to home position!")
        
        # Get home position and store X, R (Y and Z will be controlled)
        home_pose = bot.get_pose()
        controller = WristXYZController(x_range=(200, 300), y_range=(-100, 100), z_range=(50, 250))  # X: forward/back, Y: left/right, Z: up/down
        controller.current_x = home_pose.position.x  # Store home X (forward/back)
        controller.current_r = home_pose.position.r
        
        print(f"Home position: x={controller.current_x:.1f}, y={home_pose.position.y:.1f}, z={home_pose.position.z:.1f}, r={controller.current_r:.1f}")
        print(f"Forward/Back range: {controller.x_min}-{controller.x_max}mm (X-axis)")
        print(f"Left/Right range: {controller.y_min}-{controller.y_max}mm (Y-axis)")
        print(f"Up/Down range: {controller.z_min}-{controller.z_max}mm (Z-axis)")
        
        # Step 3: Start full 3D axis control
        print("\nStep 3: Starting X-Y-Z axis control...")
        print("✓ Ready for full 3D control!")
        
    except Exception as e:
        print(f"✗ Error during setup: {e}")
        return
    
    # Initialize camera
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("✗ Error: Could not open camera")
        bot.close()
        return
    
    print("✓ Camera opened successfully!")
    print("\nMove your wrist to control Y-Z axes!")
    print("- Left/Right wrist → Left/Right robot movement")
    print("- Up/Down wrist → Up/Down robot movement")
    print("(Robot stays at home X forward/back position)")
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Failed to grab frame")
                break
            
            # Flip frame horizontally for mirror effect
            frame = cv2.flip(frame, 1)
            frame_height, frame_width = frame.shape[:2]
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Draw control zone (rectangle for YZ movement)
            x_left = int(controller.camera_bounds['x_min'] * frame_width)
            x_right = int(controller.camera_bounds['x_max'] * frame_width)
            y_top = int(controller.camera_bounds['y_min'] * frame_height)
            y_bottom = int(controller.camera_bounds['y_max'] * frame_height)
            
            # Draw rectangle to show YZ control zone
            cv2.rectangle(frame, (x_left, y_top), (x_right, y_bottom), (255, 255, 0), 2)
            cv2.putText(frame, "Y-Z Control Zone", (x_left, y_top - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
            cv2.putText(frame, "LEFT/RIGHT = Y-axis", (x_left, y_top - 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)
            cv2.putText(frame, "UP/DOWN = Z-axis", (x_left, y_top - 50),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)
            
            # Draw YZ range indicators
            cv2.putText(frame, f"Y Range: {controller.y_min}-{controller.y_max}mm (left/right)", 
                       (10, frame_height - 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            cv2.putText(frame, f"Z Range: {controller.z_min}-{controller.z_max}mm (up/down)", 
                       (10, frame_height - 40), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            cv2.putText(frame, f"Home X: {controller.current_x:.1f}mm (fixed forward/back)", 
                       (10, frame_height - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            
            # Process frame for hand detection
            results = controller.hands.process(rgb_frame)
            
            # Track wrist and control Y-Z axes
            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    # Draw hand landmarks
                    controller.mp_draw.draw_landmarks(
                        frame, hand_landmarks, controller.mp_hands.HAND_CONNECTIONS
                    )
                    
                    # Get wrist position (landmark 0)
                    wrist = hand_landmarks.landmark[0]
                    
                    # Map to XYZ coordinates
                    robot_x, robot_y, robot_z = controller.map_wrist_to_xyz(wrist.x, wrist.y, hand_landmarks.landmark)
                    
                    # Apply smoothing
                    smooth_x, smooth_y, smooth_z = controller.smooth_xyz(robot_x, robot_y, robot_z)
                    
                    # Check gripper state
                    is_hand_open = controller.is_hand_open(hand_landmarks.landmark)
                    current_time = time.time()
                    
                    # Debug output (reduced for performance)
                    # Only print when moving to reduce console spam
                    if controller.should_move_xyz(smooth_x, smooth_y, smooth_z):
                        # Calculate hand span for debug
                        thumb_tip = hand_landmarks.landmark[4]
                        pinky_tip = hand_landmarks.landmark[20]
                        hand_span = np.sqrt((thumb_tip.x - pinky_tip.x)**2 + (thumb_tip.y - pinky_tip.y)**2)
                        print(f"Hand span: {hand_span:.3f} -> X={smooth_x:.1f}, Y={smooth_y:.1f}, Z={smooth_z:.1f}")
                    
                    # Check if we should move the robot
                    if controller.should_move_xyz(smooth_x, smooth_y, smooth_z):
                        try:
                            # Move robot to new XYZ position (only R remains unchanged)
                            # For this Dobot: X=forward/back, Y=left/right, Z=up/down
                            # Reduced debug output for better performance
                            
                            cmd_id = bot.move_to(smooth_x, smooth_y, smooth_z, controller.current_r)
                            controller.last_x = smooth_x
                            controller.last_y = smooth_y
                            controller.last_z = smooth_z
                            
                            # Visual feedback - green circle for successful movement
                            cv2.circle(frame, 
                                     (int(wrist.x * frame_width), int(wrist.y * frame_height)), 
                                     10, (0, 255, 0), -1)
                            
                        except Exception as e:
                            print(f"Error moving robot to Y={smooth_y:.1f}, Z={smooth_z:.1f}: {e}")
                            # Visual feedback - red circle for error
                            cv2.circle(frame, 
                                     (int(wrist.x * frame_width), int(wrist.y * frame_height)), 
                                     10, (0, 0, 255), -1)
                    else:
                        # Show that movement was filtered out
                        cv2.circle(frame, 
                                 (int(wrist.x * frame_width), int(wrist.y * frame_height)), 
                                 5, (255, 255, 0), -1)
                    
                    # Handle gripper control
                    if (controller.last_gripper_state != is_hand_open and 
                        current_time - controller.gripper_state_change_time > controller.min_gripper_state_duration):
                        
                        try:
                            if is_hand_open:
                                print("Hand OPEN -> Opening gripper")
                                bot.grip(False)  # Open gripper
                            else:
                                print("Hand CLOSED -> Closing gripper")
                                bot.grip(True)   # Close gripper
                            
                            controller.last_gripper_state = is_hand_open
                            controller.gripper_state_change_time = current_time
                            
                        except Exception as e:
                            print(f"Error controlling gripper: {e}")
                    
                    # Display current XYZ position and gripper state
                    xyz_text = f"Robot X: {smooth_x:.1f}mm, Y: {smooth_y:.1f}mm, Z: {smooth_z:.1f}mm"
                    cv2.putText(frame, xyz_text, (10, 100), 
                              cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                    
                    # Display gripper state
                    gripper_text = f"Gripper: {'OPEN' if is_hand_open else 'CLOSED'}"
                    gripper_color = (0, 255, 0) if is_hand_open else (0, 0, 255)
                    cv2.putText(frame, gripper_text, (10, 130), 
                              cv2.FONT_HERSHEY_SIMPLEX, 0.7, gripper_color, 2)
                    
                    # Display wrist position and hand span
                    thumb_tip = hand_landmarks.landmark[4]
                    pinky_tip = hand_landmarks.landmark[20]
                    hand_span = np.sqrt((thumb_tip.x - pinky_tip.x)**2 + (thumb_tip.y - pinky_tip.y)**2)
                    
                    wrist_text = f"Wrist: ({wrist.x:.2f}, {wrist.y:.2f})"
                    cv2.putText(frame, wrist_text, (10, 160), 
                              cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                    
                    hand_span_text = f"Hand span: {hand_span:.3f} (X-axis depth)"
                    cv2.putText(frame, hand_span_text, (10, 190), 
                              cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
                    
                    # Draw X position indicator bar (horizontal, top)
                    x_bar_width = int((smooth_x - controller.x_min) / (controller.x_max - controller.x_min) * 180)
                    cv2.rectangle(frame, (frame_width - 200, frame_height - 120), 
                                (frame_width - 20, frame_height - 105), (100, 100, 100), -1)
                    cv2.rectangle(frame, (frame_width - 200, frame_height - 120), 
                                (frame_width - 200 + x_bar_width, frame_height - 105), (255, 255, 0), -1)
                    cv2.putText(frame, "X", (frame_width - 210, frame_height - 110), 
                              cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
                    
                    # Draw Y position indicator bar (horizontal, middle)
                    y_bar_width = int((smooth_y - controller.y_min) / (controller.y_max - controller.y_min) * 180)
                    cv2.rectangle(frame, (frame_width - 200, frame_height - 60), 
                                (frame_width - 20, frame_height - 45), (100, 100, 100), -1)
                    cv2.rectangle(frame, (frame_width - 200, frame_height - 60), 
                                (frame_width - 200 + y_bar_width, frame_height - 45), (0, 255, 0), -1)
                    cv2.putText(frame, "Y", (frame_width - 210, frame_height - 50), 
                              cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
                    
                    # Draw Z position indicator bar (horizontal)
                    z_bar_width = int((smooth_z - controller.z_min) / (controller.z_max - controller.z_min) * 180)
                    cv2.rectangle(frame, (frame_width - 200, frame_height - 35), 
                                (frame_width - 20, frame_height - 20), (100, 100, 100), -1)
                    cv2.rectangle(frame, (frame_width - 200, frame_height - 35), 
                                (frame_width - 200 + z_bar_width, frame_height - 20), (0, 0, 255), -1)
                    cv2.putText(frame, "Z", (frame_width - 210, frame_height - 25), 
                              cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
            else:
                cv2.putText(frame, "Show your hand in the X-Y-Z control zone", (10, 100), 
                          cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
            
            # Display frame
            cv2.imshow('Home then X-Y-Z Axis + Gripper Control', frame)
            
            # Handle key presses
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('c'):
                try:
                    current_pos = bot.get_pose()
                    print(f"Current robot position: x={current_pos.position.x:.1f}, y={current_pos.position.y:.1f}, z={current_pos.position.z:.1f}, r={current_pos.position.r:.1f}")
                except Exception as e:
                    print(f"Error getting position: {e}")
    
    except KeyboardInterrupt:
        print("\nInterrupted by user")
    
    finally:
        # Cleanup
        cap.release()
        cv2.destroyAllWindows()
        try:
            bot.close()
            print("✓ Dobot connection closed")
        except:
            pass
        print("Goodbye!")

if __name__ == "__main__":
    main()
