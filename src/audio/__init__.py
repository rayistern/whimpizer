"""
Audio Generation Module for Whimperizer CSM Voice Integration

This module provides text-to-speech capabilities using Sesame's CSM (Conversational Speech Model)
to generate audiobooks from Wimpy Kid-style content.

Components:
- CSMGenerator: Core CSM model wrapper and text-to-speech conversion
- AudioProcessor: Audio file manipulation, conversion, and optimization
- VoiceManager: Multi-speaker voice management and character assignment
- AudiobookGenerator: High-level audiobook creation and assembly
"""

from .csm_generator import CSMGenerator
from .audio_processor import AudioProcessor
from .voice_manager import VoiceManager
from .audiobook_generator import AudiobookGenerator

__version__ = "1.0.0"
__author__ = "Whimperizer Audio Team"

__all__ = [
    "CSMGenerator",
    "AudioProcessor", 
    "VoiceManager",
    "AudiobookGenerator"
]