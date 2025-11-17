#!/usr/bin/env python3
"""
Video Hand Processor with MANO Points
====================================
Processes uploaded videos to extract hand tracking with MANO points,
colors right hand red and left hand green, and prepares position data
for robot control.
"""

import cv2
import mediapipe as mp
import numpy as np
import os
import json
from typing import List, Dict, Tuple, Optional
import time
from dataclasses import dataclass, asdict

@dataclass
class HandFrame:
    """Data structure for hand tracking data in a single frame."""
    frame_number: int
    timestamp: float
    left_hand: Optional[List[Dict]] = None  # MANO landmarks for left hand
    right_hand: Optional[List[Dict]] = None  # MANO landmarks for right hand
    left_hand_3d: Optional[List[Dict]] = None  # 3D coordinates for left hand
    right_hand_3d: Optional[List[Dict]] = None  # 3D coordinates for right hand

class VideoHandProcessor:
    """
    Processes videos to extract hand tracking with MANO points.
    Colors right hand red, left hand green, and extracts position data.
    """
    
    def __init__(self):
        # Initialize MediaPipe hands with improved settings for video processing
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=True,  # Use static mode to avoid timestamp issues
            max_num_hands=2,  # Track both hands
            min_detection_confidence=0.5,  # Lowered for better detection
            min_tracking_confidence=0.3,  # Lowered for better tracking
            model_complexity=0  # Lower complexity for better performance
        )
        self.mp_draw = mp.solutions.drawing_utils
        self.mp_draw_styles = mp.solutions.drawing_styles
        
        # Color configuration
        self.right_hand_color = (0, 0, 255)  # Red for right hand
        self.left_hand_color = (0, 255, 0)   # Green for left hand
        
        # Hand tracking data storage
        self.tracking_data: List[HandFrame] = []
        
        # Frame counter for consistent processing
        self.frame_counter = 0
        
    def process_video(self, input_video_path: str, output_video_path: str = None, 
                     tracking_data_path: str = None, progress_callback=None) -> bool:
        """
        Process video to extract hand tracking and create color-coded output.
        
        Args:
            input_video_path: Path to input video file
            output_video_path: Path to save processed video (optional)
            tracking_data_path: Path to save tracking data JSON (optional)
            progress_callback: Optional callback function for progress updates (progress, eta)
            
        Returns:
            bool: True if processing successful, False otherwise
        """
        if not os.path.exists(input_video_path):
            print(f"Error: Input video file not found: {input_video_path}")
            return False
            
        # Open input video
        cap = cv2.VideoCapture(input_video_path)
        if not cap.isOpened():
            print(f"Error: Could not open video file: {input_video_path}")
            return False
            
        # Get video properties
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        print(f"Processing video: {width}x{height} @ {fps}FPS, {total_frames} frames")
        
        # Calculate output dimensions with 16:9 aspect ratio
        target_aspect_ratio = 16 / 9
        max_width = 1280
        max_height = 720  # 720p (1280x720 is 16:9)
        
        # Calculate the best fit while maintaining 16:9 aspect ratio
        current_aspect_ratio = width / height
        
        if current_aspect_ratio > target_aspect_ratio:
            # Video is wider than 16:9, fit to width
            output_width = min(max_width, width)
            output_height = int(output_width / target_aspect_ratio)
        else:
            # Video is taller than 16:9, fit to height
            output_height = min(max_height, height)
            output_width = int(output_height * target_aspect_ratio)
        
        # Ensure dimensions are even numbers (required for some codecs)
        output_width = output_width if output_width % 2 == 0 else output_width - 1
        output_height = output_height if output_height % 2 == 0 else output_height - 1
        
        print(f"Converting to 16:9 aspect ratio: {output_width}x{output_height} (from {width}x{height})")
        
        # Setup video writer with H.264 codec if output path provided
        out = None
        if output_video_path:
            # Allow overriding codec order via env (HAND_VIDEO_CODECS=mp4v,avc1,...)
            codec_env = os.getenv("HAND_VIDEO_CODECS", "mp4v,avc1,H264,X264")
            codec_order = [c.strip().lower() for c in codec_env.split(",") if c.strip()]
            
            codec_map = {
                "mp4v": ("MPEG-4 (mp4v)", cv2.VideoWriter_fourcc(*"mp4v")),
                "avc1": ("H.264 (avc1)", cv2.VideoWriter_fourcc(*"avc1")),
                "h264": ("H.264 (H264)", cv2.VideoWriter_fourcc(*"H264")),
                "x264": ("H.264 (X264)", cv2.VideoWriter_fourcc(*"X264"))
            }
            
            for codec_key in codec_order:
                if codec_key not in codec_map:
                    continue
                codec_name, fourcc = codec_map[codec_key]
                out = cv2.VideoWriter(output_video_path, fourcc, fps, (output_width, output_height))
                if out.isOpened():
                    print(f"Using codec: {codec_name}")
                    break
                out.release()
                out = None
            
            if out is None:
                print("Warning: Could not initialize video writer with any codec, skipping output video")
        
        # Clear previous tracking data
        self.tracking_data = []
        
        frame_number = 0
        start_time = time.time()
        consecutive_errors = 0  # Track consecutive MediaPipe errors
        max_consecutive_errors = 10  # Skip MediaPipe processing after this many consecutive errors
        
        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                    
                # Process frame for hand detection with error handling
                try:
                    if consecutive_errors < max_consecutive_errors:
                        processed_frame, hand_data = self._process_frame(frame, frame_number, fps)
                        consecutive_errors = 0  # Reset error counter on success
                    else:
                        # Skip MediaPipe processing after too many consecutive errors
                        processed_frame = frame
                        hand_data = None
                        print(f"Skipping MediaPipe processing for frame {frame_number} due to consecutive errors")
                except Exception as e:
                    consecutive_errors += 1
                    print(f"Frame processing error on frame {frame_number} (consecutive errors: {consecutive_errors}): {e}")
                    # Skip this frame
                    frame_number += 1
                    continue
                
                # Store hand tracking data
                if hand_data:
                    self.tracking_data.append(hand_data)
                
                # Write processed frame with 16:9 conversion if output enabled
                if out:
                    converted_frame = self._convert_to_16_9(processed_frame, output_width, output_height)
                    out.write(converted_frame)
                
                frame_number += 1
                
                # Progress update (more frequent updates)
                if frame_number % 10 == 0:  # Every 10 frames for more frequent updates
                    progress = (frame_number / total_frames) * 100
                    elapsed = time.time() - start_time
                    eta = (elapsed / frame_number) * (total_frames - frame_number)
                    print(f"Progress: {progress:.1f}% ({frame_number}/{total_frames}) - ETA: {eta:.1f}s")
                    
                    # Call progress callback if provided
                    if progress_callback:
                        progress_callback(progress, eta)
                    
        except Exception as e:
            print(f"Error processing video: {e}")
            return False
            
        finally:
            cap.release()
            if out:
                out.release()
            
        if output_video_path:
            print(f"Video processing complete! Output saved to: {output_video_path}")
        print(f"Extracted hand data for {len(self.tracking_data)} frames")
        
        # Save tracking data if path provided
        if tracking_data_path:
            self._save_tracking_data(tracking_data_path)
            
        return True
    
    def _convert_to_16_9(self, frame, target_width, target_height):
        """
        Convert frame to 16:9 aspect ratio with letterboxing/pillarboxing.
        
        Args:
            frame: Input frame
            target_width: Target width (16:9 ratio)
            target_height: Target height (16:9 ratio)
            
        Returns:
            Frame with 16:9 aspect ratio
        """
        h, w = frame.shape[:2]
        target_aspect = target_width / target_height
        current_aspect = w / h
        
        if abs(current_aspect - target_aspect) < 0.01:
            # Already close to 16:9, just resize
            return cv2.resize(frame, (target_width, target_height))
        
        # Create black canvas with target dimensions
        canvas = np.zeros((target_height, target_width, 3), dtype=np.uint8)
        
        if current_aspect > target_aspect:
            # Frame is wider than 16:9, add letterboxing (black bars top/bottom)
            new_height = int(target_width / current_aspect)
            resized_frame = cv2.resize(frame, (target_width, new_height))
            
            # Center the frame vertically
            y_offset = (target_height - new_height) // 2
            canvas[y_offset:y_offset + new_height, :] = resized_frame
            
        else:
            # Frame is taller than 16:9, add pillarboxing (black bars left/right)
            new_width = int(target_height * current_aspect)
            resized_frame = cv2.resize(frame, (new_width, target_height))
            
            # Center the frame horizontally
            x_offset = (target_width - new_width) // 2
            canvas[:, x_offset:x_offset + new_width] = resized_frame
        
        return canvas
    
    def _process_frame(self, frame: np.ndarray, frame_number: int, fps: int) -> Tuple[np.ndarray, Optional[HandFrame]]:
        """
        Process a single frame for hand detection and tracking.
        
        Args:
            frame: Input frame
            frame_number: Current frame number
            fps: Video FPS for timestamp calculation
            
        Returns:
            Tuple of (processed_frame, hand_data)
        """
        # Convert BGR to RGB for MediaPipe
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Process frame for hand detection with error handling
        try:
            # Use MediaPipe with proper timestamp handling
            # Convert to uint8 if needed
            if rgb_frame.dtype != np.uint8:
                rgb_frame = (rgb_frame * 255).astype(np.uint8)
            
            # Use consistent frame counter for MediaPipe processing
            self.frame_counter += 1
            results = self.hands.process(rgb_frame)
        except Exception as e:
            print(f"MediaPipe processing error on frame {frame_number}: {e}")
            # Return frame without hand detection
            return frame, None
        
        # Create a copy for drawing
        output_frame = frame.copy()
        
        # Initialize hand data with original timestamp
        timestamp = frame_number / fps if fps > 0 else frame_number * 0.033  # Default to ~30fps if fps is 0
        hand_data = HandFrame(
            frame_number=frame_number,
            timestamp=timestamp
        )
        
        # Process detected hands
        if results.multi_hand_landmarks and results.multi_handedness:
            for hand_landmarks, handedness in zip(results.multi_hand_landmarks, results.multi_handedness):
                # Determine if this is left or right hand (inverted for correct labeling)
                hand_label = handedness.classification[0].label
                is_right_hand = hand_label == "Left"  # Inverted: MediaPipe's "Left" is viewer's "Right"
                
                # Choose color based on hand
                if is_right_hand:
                    color = self.right_hand_color
                    landmark_color = self.right_hand_color
                    connection_color = (128, 0, 128)  # Dark red for connections
                else:
                    color = self.left_hand_color
                    landmark_color = self.left_hand_color
                    connection_color = (0, 128, 0)  # Dark green for connections
                
                # Extract landmark data
                landmarks_data = []
                landmarks_3d = []
                
                for i, landmark in enumerate(hand_landmarks.landmark):
                    # 2D landmark data (MANO-style)
                    landmarks_data.append({
                        'id': i,
                        'x': landmark.x,
                        'y': landmark.y,
                        'z': landmark.z,
                        'visibility': landmark.visibility if hasattr(landmark, 'visibility') else 1.0
                    })
                    
                    # 3D coordinates for robot control
                    landmarks_3d.append({
                        'id': i,
                        'x': landmark.x,
                        'y': landmark.y,
                        'z': landmark.z
                    })
                
                # Store hand data
                if is_right_hand:
                    hand_data.right_hand = landmarks_data
                    hand_data.right_hand_3d = landmarks_3d
                else:
                    hand_data.left_hand = landmarks_data
                    hand_data.left_hand_3d = landmarks_3d
                
                # Draw hand landmarks and connections with color coding
                self._draw_colored_landmarks(
                    output_frame, hand_landmarks, landmark_color, connection_color
                )
                
                # Add hand label
                h, w, _ = output_frame.shape
                label_pos = (
                    int(hand_landmarks.landmark[0].x * w),
                    int(hand_landmarks.landmark[0].y * h) - 20
                )
                # Display correct hand label (inverted from MediaPipe's classification)
                display_label = "Right" if is_right_hand else "Left"
                cv2.putText(output_frame, f"{display_label} Hand", label_pos,
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
        
        # Add frame info
        cv2.putText(output_frame, f"Frame: {frame_number}", (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(output_frame, f"Time: {frame_number/fps:.2f}s", (10, 60),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        # Color legend
        cv2.rectangle(output_frame, (10, 90), (30, 110), self.right_hand_color, -1)
        cv2.putText(output_frame, "Right Hand", (40, 105),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        cv2.rectangle(output_frame, (10, 120), (30, 140), self.left_hand_color, -1)
        cv2.putText(output_frame, "Left Hand", (40, 135),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        return output_frame, hand_data if (hand_data.left_hand or hand_data.right_hand) else None
    
    def _draw_colored_landmarks(self, image: np.ndarray, landmarks, landmark_color: Tuple[int, int, int], 
                               connection_color: Tuple[int, int, int]):
        """Draw hand landmarks with custom colors."""
        h, w, _ = image.shape
        
        # Draw connections
        for connection in self.mp_hands.HAND_CONNECTIONS:
            start_idx = connection[0]
            end_idx = connection[1]
            
            start_point = (
                int(landmarks.landmark[start_idx].x * w),
                int(landmarks.landmark[start_idx].y * h)
            )
            end_point = (
                int(landmarks.landmark[end_idx].x * w),
                int(landmarks.landmark[end_idx].y * h)
            )
            
            cv2.line(image, start_point, end_point, connection_color, 2)
        
        # Draw landmarks
        for i, landmark in enumerate(landmarks.landmark):
            x = int(landmark.x * w)
            y = int(landmark.y * h)
            
            # Different sizes for different landmark types
            if i in [4, 8, 12, 16, 20]:  # Fingertips
                radius = 6
            elif i == 0:  # Wrist
                radius = 8
            else:
                radius = 4
                
            cv2.circle(image, (x, y), radius, landmark_color, -1)
            cv2.circle(image, (x, y), radius, (255, 255, 255), 1)  # White border
    
    def _save_tracking_data(self, output_path: str):
        """Save tracking data to JSON file."""
        try:
            data_to_save = [asdict(frame_data) for frame_data in self.tracking_data]
            
            with open(output_path, 'w') as f:
                json.dump({
                    'metadata': {
                        'total_frames': len(self.tracking_data),
                        'processing_timestamp': time.time(),
                        'format': 'MANO-style landmarks with 3D coordinates'
                    },
                    'frames': data_to_save
                }, f, indent=2)
                
            print(f"Tracking data saved to: {output_path}")
            
        except Exception as e:
            print(f"Error saving tracking data: {e}")
    
    def get_tracking_data(self) -> List[HandFrame]:
        """Get the extracted tracking data."""
        return self.tracking_data
    
    def extract_robot_positions(self, target_hand: str = 'right') -> List[Dict]:
        """
        Extract position data suitable for robot control.
        
        Args:
            target_hand: 'right' or 'left' - which hand to extract positions for
            
        Returns:
            List of position dictionaries with robot coordinates
        """
        positions = []
        
        for frame_data in self.tracking_data:
            hand_data = frame_data.right_hand_3d if target_hand == 'right' else frame_data.left_hand_3d
            
            if hand_data:
                # Extract wrist position (landmark 0) as primary control point
                wrist = hand_data[0]
                
                # Extract key finger positions for gripper control
                thumb_tip = hand_data[4] if len(hand_data) > 4 else None
                index_tip = hand_data[8] if len(hand_data) > 8 else None
                
                position_data = {
                    'frame': frame_data.frame_number,
                    'timestamp': frame_data.timestamp,
                    'wrist': wrist,
                    'thumb_tip': thumb_tip,
                    'index_tip': index_tip,
                    'all_landmarks': hand_data
                }
                
                positions.append(position_data)
        
        return positions


class RobotPositionConverter:
    """Convert hand tracking data to robot commands."""
    
    def __init__(self, x_range=(200, 300), y_range=(-100, 100), z_range=(50, 250)):
        """Initialize with robot workspace bounds."""
        self.x_min, self.x_max = x_range
        self.y_min, self.y_max = y_range
        self.z_min, self.z_max = z_range
    
    def load_tracking_data(self, tracking_data_path: str) -> Optional[Dict]:
        """Load tracking data from JSON file."""
        try:
            with open(tracking_data_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading tracking data: {e}")
            return None
    
    def convert_to_robot_commands(self, tracking_data: Dict, target_hand: str = "right") -> List[Dict]:
        """Convert tracking data to robot movement commands."""
        commands = []
        
        frames_data = tracking_data.get('frames', [])
        for frame in frames_data:
            # Get target hand data
            hand_data = None
            if target_hand == "left" and frame.get('left_hand'):
                hand_data = frame['left_hand']
            elif target_hand == "right" and frame.get('right_hand'):
                hand_data = frame['right_hand']
            
            if not hand_data:
                continue
            
            # Get wrist position (landmark 0)
            wrist = hand_data[0]
            
            # Convert to robot coordinates (matching Hand_to_robot.py mapping)
            # X-axis: Use hand span (thumb to pinky distance) for forward/back movement
            thumb_tip = hand_data[4]  # Thumb tip
            pinky_tip = hand_data[20]  # Pinky tip
            hand_span = np.sqrt((thumb_tip['x'] - pinky_tip['x'])**2 + (thumb_tip['y'] - pinky_tip['y'])**2)
            robot_x = np.interp(hand_span, [0.08, 0.25], [self.x_max, self.x_min])  # Inverted: large span = forward
            
            # Y-axis: Use wrist X-coordinate for left/right movement
            robot_y = np.interp(wrist['x'], [0.0, 1.0], [self.y_min, self.y_max])
            
            # Z-axis: Use wrist Y-coordinate for up/down movement (inverted)
            robot_z = np.interp(wrist['y'], [0.0, 1.0], [self.z_max, self.z_min])  # Inverted: top = high Z, bottom = low Z
            
            # Determine gripper state based on hand openness
            # Calculate distance between thumb tip and index finger tip
            index_tip = hand_data[8]  # Index finger tip
            
            # Use the same hand openness calculation as Hand_to_robot.py
            gripper_open = self._calculate_hand_openness(hand_data)
            
            # Create robot command
            command = {
                'frame': frame['frame_number'],
                'timestamp': frame['timestamp'],
                'x': round(robot_x, 2),
                'y': round(robot_y, 2),
                'z': round(robot_z, 2),
                'r': 0.0,  # No rotation for now
                'gripper': 1 if gripper_open else 0,
                'confidence': hand_data[0].get('visibility', 1.0)
            }
            
            commands.append(command)
        
        return commands
    
    def _calculate_hand_openness(self, hand_data: List[Dict]) -> bool:
        """
        Calculate if hand is open or closed based on finger positions.
        Returns True for open, False for closed (matching Hand_to_robot.py).
        """
        if len(hand_data) < 21:  # Need all 21 landmarks
            return False
            
        # Get landmark positions (matching Hand_to_robot.py logic)
        thumb_tip = hand_data[4]
        thumb_mcp = hand_data[2]
        index_tip = hand_data[8]
        index_pip = hand_data[6]
        middle_tip = hand_data[12]
        middle_pip = hand_data[10]
        ring_tip = hand_data[16]
        ring_pip = hand_data[14]
        pinky_tip = hand_data[20]
        pinky_pip = hand_data[18]
        
        # Count extended fingers
        extended_fingers = 0
        
        # Thumb (different logic due to orientation)
        if thumb_tip['x'] > thumb_mcp['x']:  # Thumb extended (assuming right hand)
            extended_fingers += 1
            
        # Other fingers (tip should be above pip when extended)
        if index_tip['y'] < index_pip['y']:
            extended_fingers += 1
        if middle_tip['y'] < middle_pip['y']:
            extended_fingers += 1
        if ring_tip['y'] < ring_pip['y']:
            extended_fingers += 1
        if pinky_tip['y'] < pinky_pip['y']:
            extended_fingers += 1
            
        # Return openness ratio (0-1)
        openness = extended_fingers / 5.0
        
        # Return True for open hand (matching Hand_to_robot.py threshold)
        return openness > 0.6
    
    def smooth_commands(self, commands: List[Dict], window_size: int = 3) -> List[Dict]:
        """Apply smoothing to reduce jitter in robot commands."""
        if len(commands) < window_size:
            return commands
        
        smoothed = []
        
        for i in range(len(commands)):
            # Get window around current command
            start_idx = max(0, i - window_size // 2)
            end_idx = min(len(commands), i + window_size // 2 + 1)
            window = commands[start_idx:end_idx]
            
            # Calculate smoothed position
            avg_x = sum(cmd['x'] for cmd in window) / len(window)
            avg_y = sum(cmd['y'] for cmd in window) / len(window)
            avg_z = sum(cmd['z'] for cmd in window) / len(window)
            
            # Create smoothed command
            smoothed_cmd = commands[i].copy()
            smoothed_cmd.update({
                'x': round(avg_x, 2),
                'y': round(avg_y, 2),
                'z': round(avg_z, 2)
            })
            
            smoothed.append(smoothed_cmd)
        
        return smoothed
    
    def filter_minimal_movement(self, commands: List[Dict], min_distance: float = 2.0) -> List[Dict]:
        """Filter out commands with minimal movement to reduce unnecessary robot movements."""
        if not commands:
            return commands
        
        filtered = [commands[0]]  # Always include first command
        
        for cmd in commands[1:]:
            last_cmd = filtered[-1]
            
            # Calculate distance from last command
            distance = np.sqrt(
                (cmd['x'] - last_cmd['x'])**2 + 
                (cmd['y'] - last_cmd['y'])**2 + 
                (cmd['z'] - last_cmd['z'])**2
            )
            
            # Include command if movement is significant or gripper state changed
            if distance >= min_distance or cmd['gripper'] != last_cmd['gripper']:
                filtered.append(cmd)
        
        return filtered
    
    def save_commands(self, commands: List[Dict], output_path: str):
        """Save robot commands to JSON file."""
        command_data = {
            'metadata': {
                'total_commands': len(commands),
                'workspace': {
                    'x_range': [self.x_min, self.x_max],
                    'y_range': [self.y_min, self.y_max],
                    'z_range': [self.z_min, self.z_max]
                },
                'generated_at': time.time()
            },
            'commands': commands
        }
        
        with open(output_path, 'w') as f:
            json.dump(command_data, f, indent=2)
        
        print(f"Robot commands saved to: {output_path}")


def main():
    """Demo function to test video processing."""
    processor = VideoHandProcessor()
    
    # Test with the existing test.mp4 file
    input_video = "/Users/keval/Documents/VSCode/DobotControl/test.mp4"
    output_video = "/Users/keval/Documents/VSCode/DobotControl/processed_test.mp4"
    tracking_data = "/Users/keval/Documents/VSCode/DobotControl/hand_tracking_data.json"
    
    print("Starting video hand processing...")
    
    if processor.process_video(input_video, output_video, tracking_data):
        print("Video processing completed successfully!")
        
        # Extract robot positions for right hand
        robot_positions = processor.extract_robot_positions('right')
        print(f"Extracted {len(robot_positions)} position frames for robot control")
        
        # Save robot positions
        robot_data_path = "/Users/keval/Documents/VSCode/DobotControl/robot_positions.json"
        with open(robot_data_path, 'w') as f:
            json.dump(robot_positions, f, indent=2)
        print(f"Robot position data saved to: {robot_data_path}")
        
    else:
        print("Video processing failed!")

if __name__ == "__main__":
    main()