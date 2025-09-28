"""
AI Service
==========
Production-level service for AI video analysis operations.
"""

import asyncio
import json
import logging
import os
import re
from pathlib import Path
from typing import Optional, Dict, Any, List
from functools import lru_cache
from datetime import datetime

from google import genai
from dotenv import load_dotenv

from models.schemas import AIAnalysisResult, JobStatus
from .job_manager import JobManager

# Load environment variables
load_dotenv()

# Configure Google Generative AI
try:
    api_key = os.getenv("GEMINI_API_KEY")
    if api_key:
        GENAI_AVAILABLE = True
    else:
        GENAI_AVAILABLE = False
        logging.warning("GEMINI_API_KEY not found in environment variables")
except Exception as e:
    GENAI_AVAILABLE = False
    logging.error(f"Failed to import Google GenAI: {e}")

logger = logging.getLogger(__name__)


class AIService:
    """Service for managing AI video analysis operations."""
    
    def __init__(self):
        """Initialize AI service."""
        self.genai_available = GENAI_AVAILABLE
        self.model = None
        
        if self.genai_available:
            try:
                # Initialize the genai client
                self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
                logging.info("✅ Google GenAI client initialized successfully")
            except Exception as e:
                logging.error(f"Failed to initialize GenAI client: {e}")
                self.genai_available = False
        
        self.analysis_cache: Dict[str, AIAnalysisResult] = {}
        self.usage_stats = {
            "total_analyses": 0,
            "successful_analyses": 0,
            "failed_analyses": 0,
            "total_processing_time": 0.0
        }
    
    async def analyze_video_background(
        self,
        job_id: str,
        video_path: Path,
        include_task_analysis: bool = True,
        include_movement_analysis: bool = True,
        detail_level: str = "standard",
        job_manager: JobManager = None
    ):
        """Background task for AI video analysis."""
        start_time = datetime.now()
        
        try:
            if not self.genai_available or not hasattr(self, 'client'):
                raise Exception("Google GenAI not available")
            
            # Update job status
            if job_manager:
                job_manager.update_job(
                    job_id,
                    status=JobStatus.PROCESSING,
                    progress=70,
                    current_step="AI Analysis",
                    message="Starting AI analysis..."
                )
            
            # Upload and analyze video with GenAI
            analysis_text = await self._analyze_video_with_genai(video_path)
            
            if not analysis_text:
                raise Exception("AI analysis returned empty result")
            
            # Update progress
            if job_manager:
                job_manager.update_job(
                    job_id,
                    progress=90,
                    current_step="Processing Results",
                    message="Processing AI analysis results..."
                )
            
            # Parse and structure the analysis
            analysis_result = await self._parse_analysis_result(
                analysis_text, include_task_analysis, include_movement_analysis, detail_level
            )
            
            # Save analysis result
            analysis_file = Path(f"processed/{job_id}_ai_analysis.json")
            analysis_file.parent.mkdir(exist_ok=True)
            
            with open(analysis_file, 'w') as f:
                json.dump(analysis_result.dict(), f, indent=2, default=str)
            
            # Cache the result
            self.analysis_cache[job_id] = analysis_result
            
            # Update job completion
            if job_manager:
                processed_files = job_manager.get_job(job_id).processed_files
                processed_files['ai_analysis'] = f"{job_id}_ai_analysis.json"
                
                job_manager.update_job(
                    job_id,
                    status=JobStatus.COMPLETED,
                    progress=100,
                    current_step="Complete",
                    message="AI analysis completed successfully",
                    processed_files=processed_files
                )
            
            # Update usage stats
            processing_time = (datetime.now() - start_time).total_seconds()
            self.usage_stats["total_analyses"] += 1
            self.usage_stats["successful_analyses"] += 1
            self.usage_stats["total_processing_time"] += processing_time
            
            logger.info(f"AI analysis completed for job {job_id} in {processing_time:.2f}s")
            
        except Exception as e:
            error_msg = f"AI analysis failed: {str(e)}"
            logger.error(f"Job {job_id}: {error_msg}")
            
            if job_manager:
                job_manager.update_job(
                    job_id,
                    status=JobStatus.FAILED,
                    progress=0,
                    current_step="Error",
                    message=error_msg,
                    error=str(e)
                )
            
            # Update usage stats
            self.usage_stats["total_analyses"] += 1
            self.usage_stats["failed_analyses"] += 1
    
    async def _analyze_video_with_genai(self, video_path: Path) -> str:
        """Analyze video using Google GenAI."""
        try:
            # Clean up any existing files first
            files = list(self.client.files.list())
            if files:
                logging.info("Cleaning up existing files...")
                for f in files:
                    self.client.files.delete(name=f.name)
                    logging.debug(f"Deleted: {f.name}")
            
            # Upload the video file
            logging.info(f"Uploading video: {video_path}")
            uploaded_file = self.client.files.upload(file=str(video_path))
            
            # Wait for the file to be processed
            logging.info("Processing uploaded video...")
            while uploaded_file.state.name == "PROCESSING":
                logging.debug("File is still processing, waiting...")
                await asyncio.sleep(2)
                uploaded_file = self.client.files.get(name=uploaded_file.name)
            
            if uploaded_file.state.name != "ACTIVE":
                raise Exception(f"File upload failed with state: {uploaded_file.state.name}")
            
            logging.info("Video ready for analysis!")
            
            # Enhanced prompt for video analysis with JSON format
            analysis_prompt = """
            IMPORTANT: You must respond with ONLY valid JSON. Do not include any markdown code blocks, explanations, or other text.

            Analyze this video and provide a detailed breakdown of hand movements and actions. Return ONLY the JSON response in this exact format:

            {
              "task_description": "Brief description of the main task being performed",
              "timeline": [
                {
                  "action": "Detailed description of what the hands are doing",
                  "start_time": "0:00", 
                  "end_time": "0:02",
                  "actors": ["right hand"],
                  "objects": ["book"],
                  "notes": "Any additional movement details"
                },
                {
                  "action": "Next action description", 
                  "start_time": "0:02",
                  "end_time": "0:04",
                  "actors": ["both hands"],
                  "objects": ["book", "pen"],
                  "notes": "Movement details"
                }
              ],
              "robot_notes": "Observations about hand movements for robot replication, including dominant hand usage, precision requirements, and speed variations",
              "confidence": 0.95
            }

            Requirements:
            - Break down the video into 3-8 distinct actions
            - Use MM:SS format for all timestamps
            - Be specific about which hand(s) are active in each action
            - Include all objects being touched, grasped, or manipulated
            - Make action descriptions detailed enough for robot programming
            - Ensure timeline covers the entire video duration
            - Focus on hand movements and object interactions

            Example response:
            {
              "task_description": "Opening a book to reveal a bookmark, then picking up an AirPods case",
              "timeline": [
                {
                  "action": "Both hands position and grasp the book cover",
                  "start_time": "0:00",
                  "end_time": "0:01", 
                  "actors": ["both hands"],
                  "objects": ["book"],
                  "notes": "Symmetrical hand positioning for book opening"
                },
                {
                  "action": "Both hands open the book revealing a pen bookmark",
                  "start_time": "0:01",
                  "end_time": "0:03",
                  "actors": ["both hands"], 
                  "objects": ["book", "pen bookmark"],
                  "notes": "Coordinated opening motion, pen visible inside"
                },
                {
                  "action": "Both hands close the book back to original position",
                  "start_time": "0:03", 
                  "end_time": "0:05",
                  "actors": ["both hands"],
                  "objects": ["book"],
                  "notes": "Reverse of opening motion"
                },
                {
                  "action": "Right hand reaches for and grasps AirPods case",
                  "start_time": "0:05",
                  "end_time": "0:07", 
                  "actors": ["right hand"],
                  "objects": ["AirPods case"],
                  "notes": "Precise grip on small rectangular object"
                }
              ],
              "robot_notes": "Primary coordination between both hands for book manipulation, then transition to right-hand dominance for object pickup. Moderate precision required for all actions.",
              "confidence": 0.98
            }
            """

            # Generate content with the uploaded video
            response = self.client.models.generate_content(
                model="gemini-2.5-flash", 
                contents=[uploaded_file, analysis_prompt]
            )
            
            analysis_result = response.text
            
            # Clean up the uploaded file
            logging.info("Cleaning up uploaded file...")
            self.client.files.delete(name=uploaded_file.name)
            logging.info("✓ Analysis complete!")
            
            # Debug: Log the raw response
            logging.info(f"Raw AI response (first 1000 chars): {analysis_result[:1000]}")
            
            return analysis_result
            
        except Exception as e:
            logging.error(f"GenAI analysis failed: {e}")
            raise
    
    async def _parse_analysis_result(
        self,
        analysis_text: str,
        include_task_analysis: bool,
        include_movement_analysis: bool,
        detail_level: str
    ) -> AIAnalysisResult:
        """Parse raw AI analysis text into structured result."""
        try:
            # Try to extract JSON from the response
            json_data = self._extract_json_from_text(analysis_text)
            
            # Debug logging
            logging.info(f"JSON extraction result: {json_data is not None}")
            if json_data:
                logging.info(f"Timeline items found: {len(json_data.get('timeline', []))}")
            
            if json_data:
                # Invert hand labels in the timeline
                inverted_timeline = self._invert_hand_labels(json_data.get("timeline", []))
                
                # Invert hand labels in robot_notes
                robot_notes = json_data.get("robot_notes", "No robot control notes available")
                inverted_robot_notes = self._invert_hand_labels_in_text(robot_notes)
                
                # Parse JSON response
                return AIAnalysisResult(
                    task_description=json_data.get("task_description", "Task description not available"),
                    timeline=inverted_timeline,
                    robot_notes=inverted_robot_notes,
                    confidence=json_data.get("confidence", 0.8)
                )
            else:
                # Fallback to text-based parsing for non-JSON responses
                task_description = self._extract_task_description(analysis_text)
                timeline = self._extract_timeline(analysis_text) if include_task_analysis else []
                robot_notes = self._extract_robot_notes(analysis_text) if include_movement_analysis else ""
                confidence = self._calculate_confidence(analysis_text, detail_level)
                
                return AIAnalysisResult(
                    task_description=task_description,
                    timeline=timeline,
                    robot_notes=robot_notes,
                    confidence=confidence
                )
            
        except Exception as e:
            logger.error(f"Failed to parse analysis result: {e}")
            # Return a basic result with error information
            return AIAnalysisResult(
                task_description="Failed to parse analysis response",
                timeline=[],
                robot_notes=f"Analysis parsing failed: {str(e)}",
                confidence=0.0
            )
    
    def _extract_json_from_text(self, text: str) -> Optional[Dict]:
        """Extract JSON from text that might contain markdown code blocks."""
        try:
            # First, try to parse the text directly as JSON
            return json.loads(text.strip())
        except json.JSONDecodeError:
            pass
        
        try:
            # Look for JSON in markdown code blocks - improved patterns
            
            # Pattern 1: ```json { ... } ```
            json_pattern1 = r'```json\s*(\{.*?\})\s*```'
            matches1 = re.findall(json_pattern1, text, re.DOTALL | re.IGNORECASE)
            
            if matches1:
                try:
                    return json.loads(matches1[0])
                except json.JSONDecodeError:
                    pass
            
            # Pattern 2: ``` { ... } ``` (without json specifier)
            json_pattern2 = r'```\s*(\{.*?\})\s*```'
            matches2 = re.findall(json_pattern2, text, re.DOTALL | re.IGNORECASE)
            
            if matches2:
                try:
                    return json.loads(matches2[0])
                except json.JSONDecodeError:
                    pass
            
            # Pattern 3: Just find the JSON object (starts with { and try to balance braces)
            json_start = text.find('{')
            if json_start != -1:
                # Find the matching closing brace
                brace_count = 0
                json_end = json_start
                
                for i in range(json_start, len(text)):
                    if text[i] == '{':
                        brace_count += 1
                    elif text[i] == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            json_end = i + 1
                            break
                
                if brace_count == 0:  # Found complete JSON
                    json_text = text[json_start:json_end]
                    try:
                        return json.loads(json_text)
                    except json.JSONDecodeError:
                        pass
            
            return None
            
        except Exception as e:
            logging.error(f"JSON extraction failed: {e}")
            return None
    
    def _extract_task_description(self, text: str) -> str:
        """Extract task description from analysis text."""
        lines = text.split('\n')
        for i, line in enumerate(lines):
            if line.strip().lower().startswith('task'):
                if i + 1 < len(lines):
                    return lines[i + 1].strip()
        return "Task description not found"
    
    def _extract_timeline(self, text: str) -> List[Dict[str, Any]]:
        """Extract timeline from analysis text."""
        timeline = []
        lines = text.split('\n')
        
        current_action = None
        for line in lines:
            line = line.strip()
            
            # Look for timeline section
            if line.lower().startswith('timeline'):
                continue
            
            # Look for time patterns (MM:SS — MM:SS)
            if '—' in line and ':' in line:
                if current_action:
                    timeline.append(current_action)
                
                # Parse time range
                time_part = line
                current_action = {
                    "description": "",
                    "time_range": time_part,
                    "actors": [],
                    "objects": []
                }
            
            # Look for action description (line before time)
            elif current_action is None and line and not line.lower().startswith(('actors:', 'objects:')):
                current_action = {
                    "description": line,
                    "time_range": "",
                    "actors": [],
                    "objects": []
                }
            
            # Parse actors
            elif line.lower().startswith('actors:') and current_action:
                actors_text = line[7:].strip()
                current_action["actors"] = [actors_text] if actors_text else []
            
            # Parse objects
            elif line.lower().startswith('objects:') and current_action:
                objects_text = line[8:].strip()
                current_action["objects"] = [objects_text] if objects_text else []
        
        # Add the last action
        if current_action:
            timeline.append(current_action)
        
        return timeline
    
    def _extract_robot_notes(self, text: str) -> str:
        """Extract robot control notes from analysis text."""
        lines = text.split('\n')
        robot_notes = []
        in_robot_section = False
        
        for line in lines:
            if 'robot control notes' in line.lower():
                in_robot_section = True
                continue
            
            if in_robot_section:
                if line.strip():
                    robot_notes.append(line.strip())
                elif robot_notes:  # Empty line after notes
                    break
        
        return '\n'.join(robot_notes) if robot_notes else "No robot control notes found"
    
    def _calculate_confidence(self, text: str, detail_level: str) -> float:
        """Calculate confidence score based on analysis quality."""
        base_confidence = 0.7
        
        # Increase confidence if structured sections are found
        if 'task' in text.lower():
            base_confidence += 0.1
        if 'timeline' in text.lower():
            base_confidence += 0.1
        if 'robot' in text.lower():
            base_confidence += 0.1
        
        # Adjust based on detail level
        if detail_level == "detailed":
            base_confidence += 0.05
        elif detail_level == "basic":
            base_confidence -= 0.05
        
        return min(1.0, base_confidence)
    
    async def get_analysis_result(self, job_id: str) -> Optional[AIAnalysisResult]:
        """Get AI analysis result for a job."""
        # Check cache first
        if job_id in self.analysis_cache:
            return self.analysis_cache[job_id]
        
        # Load from file
        analysis_file = Path(f"processed/{job_id}_ai_analysis.json")
        if analysis_file.exists():
            try:
                with open(analysis_file, 'r') as f:
                    data = json.load(f)
                result = AIAnalysisResult(**data)
                self.analysis_cache[job_id] = result
                return result
            except Exception as e:
                logger.error(f"Failed to load analysis result for job {job_id}: {e}")
        
        return None
    
    async def get_movement_insights(self, job_id: str) -> Dict[str, Any]:
        """Get detailed movement insights for robot programming."""
        analysis = await self.get_analysis_result(job_id)
        if not analysis:
            return {"error": "Analysis not found"}
        
        insights = {
            "primary_hand": self._determine_primary_hand(analysis.timeline),
            "movement_patterns": self._analyze_movement_patterns(analysis.timeline),
            "precision_requirements": self._assess_precision_requirements(analysis.robot_notes),
            "speed_recommendations": self._suggest_speed_settings(analysis.timeline),
            "safety_considerations": self._identify_safety_considerations(analysis.robot_notes)
        }
        
        return insights
    
    def _determine_primary_hand(self, timeline: List[Dict[str, Any]]) -> str:
        """Determine which hand is used most frequently."""
        hand_usage = {"right": 0, "left": 0, "both": 0}
        
        for action in timeline:
            for actor in action.get("actors", []):
                actor_lower = actor.lower()
                if "right hand" in actor_lower:
                    hand_usage["right"] += 1
                elif "left hand" in actor_lower:
                    hand_usage["left"] += 1
                elif "both hands" in actor_lower:
                    hand_usage["both"] += 1
        
        return max(hand_usage, key=hand_usage.get)
    
    def _invert_hand_labels(self, timeline: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Invert hand labels in timeline data to match corrected hand labeling."""
        inverted_timeline = []
        
        for action in timeline:
            inverted_action = action.copy()
            
            # Keep actors unchanged (don't invert actor labels)
            if "actors" in action:
                inverted_action["actors"] = action["actors"]
            
            # Invert hand references in action description
            if "action" in action:
                action_text = action["action"]
                # Replace "right hand" with "left hand" and vice versa
                action_text = re.sub(r'\bright hand\b', 'LEFT_HAND_PLACEHOLDER', action_text, flags=re.IGNORECASE)
                action_text = re.sub(r'\bleft hand\b', 'right hand', action_text, flags=re.IGNORECASE)
                action_text = re.sub(r'LEFT_HAND_PLACEHOLDER', 'left hand', action_text, flags=re.IGNORECASE)
                inverted_action["action"] = action_text
            
            # Invert hand references in notes
            if "notes" in action:
                notes_text = action["notes"]
                # Replace "right hand" with "left hand" and vice versa
                notes_text = re.sub(r'\bright hand\b', 'LEFT_HAND_PLACEHOLDER', notes_text, flags=re.IGNORECASE)
                notes_text = re.sub(r'\bleft hand\b', 'right hand', notes_text, flags=re.IGNORECASE)
                notes_text = re.sub(r'LEFT_HAND_PLACEHOLDER', 'left hand', notes_text, flags=re.IGNORECASE)
                inverted_action["notes"] = notes_text
            
            inverted_timeline.append(inverted_action)
        
        return inverted_timeline
    
    def _invert_hand_labels_in_text(self, text: str) -> str:
        """Invert hand labels in text (for robot_notes, task_description, etc.)."""
        if not text:
            return text
            
        # Replace "right hand" with "left hand" and vice versa
        # Use placeholder to avoid double replacement
        text = re.sub(r'\bright hand\b', 'LEFT_HAND_PLACEHOLDER', text, flags=re.IGNORECASE)
        text = re.sub(r'\bleft hand\b', 'right hand', text, flags=re.IGNORECASE)
        text = re.sub(r'LEFT_HAND_PLACEHOLDER', 'left hand', text, flags=re.IGNORECASE)
        
        return text
    
    def _analyze_movement_patterns(self, timeline: List[Dict[str, Any]]) -> List[str]:
        """Analyze movement patterns from timeline."""
        patterns = []
        
        # Analyze common action types
        action_types = []
        for action in timeline:
            description = action.get("description", "").lower()
            if "grasp" in description or "grab" in description:
                action_types.append("grasping")
            elif "place" in description or "put" in description:
                action_types.append("placing")
            elif "move" in description:
                action_types.append("moving")
        
        if action_types:
            most_common = max(set(action_types), key=action_types.count)
            patterns.append(f"Primary movement type: {most_common}")
        
        # Analyze sequence length
        patterns.append(f"Total actions: {len(timeline)}")
        
        return patterns
    
    def _assess_precision_requirements(self, robot_notes: str) -> str:
        """Assess precision requirements from robot notes."""
        notes_lower = robot_notes.lower()
        
        if "precision" in notes_lower or "careful" in notes_lower:
            return "high"
        elif "deliberate" in notes_lower or "controlled" in notes_lower:
            return "medium"
        else:
            return "standard"
    
    def _suggest_speed_settings(self, timeline: List[Dict[str, Any]]) -> Dict[str, float]:
        """Suggest speed settings based on timeline analysis."""
        # Default speeds
        suggestions = {
            "recommended_speed": 1.0,
            "min_safe_speed": 0.3,
            "max_safe_speed": 2.0
        }
        
        # Adjust based on action count (more actions = slower for precision)
        if len(timeline) > 10:
            suggestions["recommended_speed"] = 0.7
        elif len(timeline) > 5:
            suggestions["recommended_speed"] = 0.8
        
        return suggestions
    
    def _identify_safety_considerations(self, robot_notes: str) -> List[str]:
        """Identify safety considerations from robot notes."""
        considerations = []
        notes_lower = robot_notes.lower()
        
        if "object" in notes_lower:
            considerations.append("Ensure workspace is clear of obstacles")
        if "precision" in notes_lower:
            considerations.append("Use slower speeds for precise movements")
        if "grip" in notes_lower or "grasp" in notes_lower:
            considerations.append("Monitor gripper force to avoid damage")
        
        # Default safety considerations
        considerations.extend([
            "Verify robot is properly homed before playback",
            "Keep emergency stop accessible",
            "Monitor robot throughout playback"
        ])
        
        return considerations
    
    async def get_available_models(self) -> List[Dict[str, Any]]:
        """Get list of available AI models."""
        return [
            {
                "name": "gemini-2.5-flash",
                "description": "Fast video analysis with excellent accuracy",
                "capabilities": ["task_analysis", "movement_analysis", "timeline_extraction", "robot_insights"],
                "max_video_length": "10 minutes",
                "processing_speed": "fast",
                "provider": "Google AI"
            }
        ]
    
    async def submit_feedback(self, job_id: str, feedback: Dict[str, Any]) -> bool:
        """Submit feedback on analysis quality."""
        try:
            feedback_file = Path(f"feedback/{job_id}_feedback.json")
            feedback_file.parent.mkdir(exist_ok=True)
            
            feedback_data = {
                "job_id": job_id,
                "feedback": feedback,
                "timestamp": datetime.now().isoformat()
            }
            
            with open(feedback_file, 'w') as f:
                json.dump(feedback_data, f, indent=2)
            
            logger.info(f"Feedback submitted for job {job_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to submit feedback for job {job_id}: {e}")
            return False
    
    async def get_usage_stats(self) -> Dict[str, Any]:
        """Get AI service usage statistics."""
        stats = self.usage_stats.copy()
        
        # Calculate additional metrics
        if stats["total_analyses"] > 0:
            stats["success_rate"] = stats["successful_analyses"] / stats["total_analyses"]
            stats["average_processing_time"] = stats["total_processing_time"] / stats["total_analyses"]
        else:
            stats["success_rate"] = 0.0
            stats["average_processing_time"] = 0.0
        
        stats["cache_size"] = len(self.analysis_cache)
        stats["last_updated"] = datetime.now().isoformat()
        
        return stats


# Dependency injection
_ai_service: Optional[AIService] = None


@lru_cache()
def get_ai_service() -> AIService:
    """Get AI service instance (singleton)."""
    global _ai_service
    if _ai_service is None:
        _ai_service = AIService()
    return _ai_service


# Job manager dependency
@lru_cache()
def get_job_manager() -> JobManager:
    """Get job manager instance (singleton)."""
    return JobManager()
