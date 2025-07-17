"""
Voice Manager Module

Manages multi-speaker voices, character voice assignment, and voice consistency
across audiobook chapters. Provides intelligent voice selection and character detection.
"""

import logging
import re
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from .csm_generator import AudioSegment

logger = logging.getLogger(__name__)


@dataclass
class VoiceProfile:
    """Voice profile for a character or speaker"""
    name: str
    speaker_id: int
    description: str
    usage_patterns: List[str]
    voice_type: str  # 'narrator', 'character', 'dialogue'
    gender: Optional[str] = None
    age_group: Optional[str] = None  # 'child', 'teen', 'adult', 'elderly'


@dataclass
class DialogueSegment:
    """Represents a dialogue segment with speaker assignment"""
    text: str
    speaker_name: str
    speaker_id: int
    segment_type: str  # 'dialogue', 'narration', 'thought'
    confidence: float = 1.0


class VoiceManager:
    """
    Voice management system for audiobook generation
    
    Handles character voice assignment, speaker consistency, and intelligent
    voice selection based on text content analysis.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Voice Manager
        
        Args:
            config: Configuration dictionary with voice settings
        """
        self.config = config
        self.audio_config = config.get('audio', {})
        self.voice_config = self.audio_config.get('voices', {})
        self.text_config = config.get('text_processing', {})
        
        # Initialize voice profiles
        self.voice_profiles = self._create_voice_profiles()
        self.character_patterns = self._load_character_patterns()
        
        # Default voice assignments
        self.default_narrator = self.voice_config.get('narrator', 0)
        self.current_context = []
        
        logger.info(f"Initialized Voice Manager with {len(self.voice_profiles)} voice profiles")
    
    def _create_voice_profiles(self) -> Dict[str, VoiceProfile]:
        """Create voice profiles for different characters"""
        profiles = {}
        
        # Define default Wimpy Kid character voices
        voice_definitions = [
            {
                'name': 'narrator',
                'speaker_id': self.voice_config.get('narrator', 0),
                'description': 'Main narrator voice - clear and engaging',
                'patterns': ['narrator', 'description', 'scene'],
                'voice_type': 'narrator',
                'gender': 'neutral',
                'age_group': 'adult'
            },
            {
                'name': 'greg',
                'speaker_id': self.voice_config.get('greg', 1),
                'description': 'Greg Heffley - main character, middle school boy',
                'patterns': ['I said', 'I thought', 'I was', 'I did', 'I went', 'I knew'],
                'voice_type': 'character',
                'gender': 'male',
                'age_group': 'child'
            },
            {
                'name': 'rodrick',
                'speaker_id': self.voice_config.get('rodrick', 2),
                'description': 'Rodrick Heffley - older brother, teenager',
                'patterns': ['Rodrick said', 'Rodrick yelled', 'Rodrick told', 'Rodrick'],
                'voice_type': 'character',
                'gender': 'male',
                'age_group': 'teen'
            },
            {
                'name': 'mom',
                'speaker_id': self.voice_config.get('mom', 3),
                'description': 'Mom - caring but firm mother figure',
                'patterns': ['Mom said', 'Mom told', 'Mom asked', 'Mom', 'Mother'],
                'voice_type': 'character',
                'gender': 'female',
                'age_group': 'adult'
            },
            {
                'name': 'dad',
                'speaker_id': self.voice_config.get('dad', 4),
                'description': 'Dad - well-meaning father figure',
                'patterns': ['Dad said', 'Dad told', 'Dad asked', 'Dad', 'Father'],
                'voice_type': 'character',
                'gender': 'male',
                'age_group': 'adult'
            },
            {
                'name': 'friend',
                'speaker_id': self.voice_config.get('friend', 5),
                'description': 'Friend characters - peers and classmates',
                'patterns': ['Rowley', 'friend', 'classmate', 'buddy'],
                'voice_type': 'character',
                'gender': 'neutral',
                'age_group': 'child'
            },
            {
                'name': 'teacher',
                'speaker_id': self.voice_config.get('teacher', 6),
                'description': 'Teacher/adult authority figures',
                'patterns': ['teacher', 'principal', 'coach', 'Mr.', 'Mrs.', 'Ms.'],
                'voice_type': 'character',
                'gender': 'neutral',
                'age_group': 'adult'
            }
        ]
        
        for voice_def in voice_definitions:
            profile = VoiceProfile(
                name=voice_def['name'],
                speaker_id=voice_def['speaker_id'],
                description=voice_def['description'],
                usage_patterns=voice_def['patterns'],
                voice_type=voice_def['voice_type'],
                gender=voice_def.get('gender'),
                age_group=voice_def.get('age_group')
            )
            profiles[voice_def['name']] = profile
        
        return profiles
    
    def _load_character_patterns(self) -> Dict[str, List[str]]:
        """Load character detection patterns from config"""
        patterns = {}
        
        # Load from config if available
        char_config = self.text_config.get('character_detection', {}).get('patterns', {})
        for char_name, char_patterns in char_config.items():
            patterns[char_name] = char_patterns
        
        # Add default patterns if not in config
        default_patterns = {
            'greg': [r'\bI\s+(said|thought|was|did|went|knew|felt)', r'^I\s+'],
            'rodrick': [r'\bRodrick\s+(said|yelled|told|asked)', r'\bRodrick\b'],
            'mom': [r'\b(Mom|Mother)\s+(said|told|asked|called)', r'\bMom\b'],
            'dad': [r'\b(Dad|Father)\s+(said|told|asked|called)', r'\bDad\b'],
            'dialogue': [r'"[^"]*"', r'"[^"]*"', r'"[^"]*"'],  # Various quote styles
        }
        
        for char_name, default_pats in default_patterns.items():
            if char_name not in patterns:
                patterns[char_name] = default_pats
        
        return patterns
    
    def analyze_text_for_speakers(self, text: str) -> List[DialogueSegment]:
        """
        Analyze text to identify speakers and assign voices
        
        Args:
            text: Input text to analyze
            
        Returns:
            List of dialogue segments with speaker assignments
        """
        segments = []
        
        try:
            # Split text into sentences/paragraphs
            text_parts = self._split_text_into_parts(text)
            
            for part in text_parts:
                if not part.strip():
                    continue
                
                # Detect speaker for this part
                speaker_info = self._detect_speaker(part)
                
                segment = DialogueSegment(
                    text=part.strip(),
                    speaker_name=speaker_info['name'],
                    speaker_id=speaker_info['id'],
                    segment_type=speaker_info['type'],
                    confidence=speaker_info['confidence']
                )
                
                segments.append(segment)
            
            # Post-process to improve consistency
            segments = self._improve_speaker_consistency(segments)
            
            logger.debug(f"Analyzed text into {len(segments)} speaker segments")
            return segments
            
        except Exception as e:
            logger.error(f"Speaker analysis failed: {str(e)}")
            # Fallback: assign everything to narrator
            return [DialogueSegment(
                text=text,
                speaker_name='narrator',
                speaker_id=self.default_narrator,
                segment_type='narration',
                confidence=0.5
            )]
    
    def _split_text_into_parts(self, text: str) -> List[str]:
        """Split text into logical parts for speaker analysis"""
        # Split by dialogue markers and paragraph breaks
        parts = []
        
        # First, split by dialogue quotes
        quote_pattern = r'("[^"]*")'
        split_parts = re.split(quote_pattern, text)
        
        for part in split_parts:
            if not part.strip():
                continue
                
            # If it's a quoted dialogue, keep as is
            if part.startswith('"') and part.endswith('"'):
                parts.append(part)
            else:
                # Split narration by sentences or paragraphs
                sentences = re.split(r'[.!?]+(?=\s+[A-Z])', part)
                for sentence in sentences:
                    if sentence.strip():
                        parts.append(sentence.strip())
        
        return parts
    
    def _detect_speaker(self, text: str) -> Dict[str, Any]:
        """Detect the most likely speaker for a text segment"""
        text_lower = text.lower().strip()
        
        # Check for direct dialogue
        if text.startswith('"') and text.endswith('"'):
            # This is dialogue - determine who's speaking
            return self._detect_dialogue_speaker(text)
        
        # Check character-specific patterns
        for char_name, patterns in self.character_patterns.items():
            if char_name == 'dialogue':
                continue
                
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    profile = self.voice_profiles.get(char_name)
                    if profile:
                        return {
                            'name': char_name,
                            'id': profile.speaker_id,
                            'type': 'character',
                            'confidence': 0.8
                        }
        
        # Check for first-person perspective (likely Greg)
        if re.search(r'\bI\s+(was|am|did|went|said|thought)', text_lower):
            greg_profile = self.voice_profiles.get('greg')
            if greg_profile:
                return {
                    'name': 'greg',
                    'id': greg_profile.speaker_id,
                    'type': 'character',
                    'confidence': 0.7
                }
        
        # Default to narrator
        return {
            'name': 'narrator',
            'id': self.default_narrator,
            'type': 'narration',
            'confidence': 0.6
        }
    
    def _detect_dialogue_speaker(self, dialogue_text: str) -> Dict[str, Any]:
        """Detect speaker for quoted dialogue"""
        # Look for speaker attribution before or after the quote
        # This is a simplified approach - could be enhanced with context
        
        # Default to Greg for most dialogue (as he's the main character)
        greg_profile = self.voice_profiles.get('greg')
        if greg_profile:
            return {
                'name': 'greg',
                'id': greg_profile.speaker_id,
                'type': 'dialogue',
                'confidence': 0.6
            }
        
        # Fallback to narrator
        return {
            'name': 'narrator',
            'id': self.default_narrator,
            'type': 'dialogue',
            'confidence': 0.5
        }
    
    def _improve_speaker_consistency(self, segments: List[DialogueSegment]) -> List[DialogueSegment]:
        """Improve speaker consistency across segments"""
        if len(segments) <= 1:
            return segments
        
        # Simple consistency improvement
        for i in range(1, len(segments)):
            prev_segment = segments[i-1]
            curr_segment = segments[i]
            
            # If current segment has low confidence and previous was high confidence
            # and they're similar types, consider using previous speaker
            if (curr_segment.confidence < 0.7 and 
                prev_segment.confidence > 0.7 and
                curr_segment.segment_type == prev_segment.segment_type):
                
                # Check if text is continuation (starts with lowercase, no quotes)
                if (not curr_segment.text.startswith('"') and 
                    curr_segment.text[0].islower()):
                    curr_segment.speaker_name = prev_segment.speaker_name
                    curr_segment.speaker_id = prev_segment.speaker_id
                    curr_segment.confidence = 0.8
        
        return segments
    
    def assign_voices_to_text(
        self, 
        text: str, 
        context: Optional[List[AudioSegment]] = None
    ) -> List[Tuple[str, int, str]]:
        """
        Assign voices to text segments for audio generation
        
        Args:
            text: Input text to process
            context: Previous audio context for consistency
            
        Returns:
            List of (text_segment, speaker_id, speaker_name) tuples
        """
        # Analyze text for speakers
        segments = self.analyze_text_for_speakers(text)
        
        # Convert to format expected by audio generation
        voice_assignments = []
        for segment in segments:
            voice_assignments.append((
                segment.text,
                segment.speaker_id,
                segment.speaker_name
            ))
        
        logger.info(f"Assigned voices to {len(voice_assignments)} text segments")
        return voice_assignments
    
    def get_voice_for_character(self, character_name: str) -> Optional[VoiceProfile]:
        """Get voice profile for a specific character"""
        return self.voice_profiles.get(character_name.lower())
    
    def get_speaker_context(
        self, 
        segments: List[DialogueSegment], 
        max_context: int = 5
    ) -> List[AudioSegment]:
        """
        Create speaker context for CSM generation
        
        Args:
            segments: Recent dialogue segments
            max_context: Maximum number of context segments
            
        Returns:
            List of AudioSegment objects for context
        """
        context = []
        
        # Take the most recent segments as context
        recent_segments = segments[-max_context:] if len(segments) > max_context else segments
        
        for segment in recent_segments:
            audio_segment = AudioSegment(
                text=segment.text,
                speaker=segment.speaker_id,
                speaker_name=segment.speaker_name
            )
            context.append(audio_segment)
        
        return context
    
    def get_voice_statistics(self) -> Dict[str, Any]:
        """Get statistics about voice usage and profiles"""
        stats = {
            'total_voices': len(self.voice_profiles),
            'voice_types': {},
            'characters': list(self.voice_profiles.keys()),
            'speaker_ids': [p.speaker_id for p in self.voice_profiles.values()]
        }
        
        # Count voice types
        for profile in self.voice_profiles.values():
            voice_type = profile.voice_type
            if voice_type not in stats['voice_types']:
                stats['voice_types'][voice_type] = 0
            stats['voice_types'][voice_type] += 1
        
        return stats
    
    def update_voice_mapping(self, character_name: str, speaker_id: int) -> bool:
        """
        Update voice mapping for a character
        
        Args:
            character_name: Name of the character
            speaker_id: New speaker ID to assign
            
        Returns:
            bool: True if update was successful
        """
        try:
            if character_name.lower() in self.voice_profiles:
                self.voice_profiles[character_name.lower()].speaker_id = speaker_id
                logger.info(f"Updated voice mapping: {character_name} -> speaker {speaker_id}")
                return True
            else:
                logger.warning(f"Character not found: {character_name}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to update voice mapping: {str(e)}")
            return False
    
    def export_voice_mapping(self) -> Dict[str, Any]:
        """Export current voice mapping configuration"""
        mapping = {}
        
        for name, profile in self.voice_profiles.items():
            mapping[name] = {
                'speaker_id': profile.speaker_id,
                'description': profile.description,
                'voice_type': profile.voice_type,
                'patterns': profile.usage_patterns
            }
        
        return mapping
    
    def validate_voice_assignments(self, assignments: List[Tuple[str, int, str]]) -> bool:
        """Validate that voice assignments are consistent and valid"""
        try:
            valid_speaker_ids = [p.speaker_id for p in self.voice_profiles.values()]
            
            for text, speaker_id, speaker_name in assignments:
                if speaker_id not in valid_speaker_ids:
                    logger.warning(f"Invalid speaker ID: {speaker_id}")
                    return False
                
                if not text.strip():
                    logger.warning("Empty text segment found")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Voice assignment validation failed: {str(e)}")
            return False