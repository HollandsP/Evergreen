"""
ElevenLabs API client for voice synthesis.
"""

import os
import requests
import logging
from typing import Dict, List, Any, Optional, BinaryIO
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)

class ElevenLabsClient:
    """Client for interacting with ElevenLabs Text-to-Speech API."""
    
    BASE_URL = "https://api.elevenlabs.io/v1"
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize ElevenLabs client.
        
        Args:
            api_key: ElevenLabs API key (can also be set via ELEVENLABS_API_KEY env var)
        """
        self.api_key = api_key or os.getenv('ELEVENLABS_API_KEY')
        if not self.api_key:
            raise ValueError("ElevenLabs API key is required. Set ELEVENLABS_API_KEY env var or pass api_key parameter.")
        
        # Configure session with retry strategy
        self.session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("https://", adapter)
        self.session.headers.update({
            'xi-api-key': self.api_key,
            'Content-Type': 'application/json'
        })
    
    def text_to_speech(self, text: str, voice_id: str,
                      voice_settings: Optional[Dict[str, Any]] = None,
                      output_format: str = 'mp3_44100_128') -> bytes:
        """
        Convert text to speech using specified voice.
        
        Args:
            text: Text to convert to speech
            voice_id: ID of the voice to use
            voice_settings: Optional voice settings (stability, similarity_boost, etc.)
            output_format: Output audio format
        
        Returns:
            Audio data as bytes
        """
        url = f"{self.BASE_URL}/text-to-speech/{voice_id}"
        
        # Default voice settings
        if voice_settings is None:
            voice_settings = {
                "stability": 0.5,
                "similarity_boost": 0.5,
                "style": 0.0,
                "use_speaker_boost": True
            }
        
        payload = {
            "text": text,
            "model_id": "eleven_monolingual_v1",
            "voice_settings": voice_settings
        }
        
        # Set output format in headers
        headers = {
            'Accept': f'audio/{output_format}',
            'xi-api-key': self.api_key
        }
        
        try:
            response = self.session.post(url, json=payload, headers=headers)
            response.raise_for_status()
            
            logger.info(f"Successfully generated speech for {len(text)} characters")
            return response.content
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error generating speech: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response content: {e.response.text}")
            raise
    
    def text_to_speech_stream(self, text: str, voice_id: str,
                             voice_settings: Optional[Dict[str, Any]] = None,
                             chunk_size: int = 1024) -> Any:
        """
        Stream text to speech for real-time playback.
        
        Args:
            text: Text to convert to speech
            voice_id: ID of the voice to use
            voice_settings: Optional voice settings
            chunk_size: Size of audio chunks to yield
        
        Yields:
            Audio data chunks
        """
        url = f"{self.BASE_URL}/text-to-speech/{voice_id}/stream"
        
        if voice_settings is None:
            voice_settings = {
                "stability": 0.5,
                "similarity_boost": 0.5
            }
        
        payload = {
            "text": text,
            "model_id": "eleven_monolingual_v1",
            "voice_settings": voice_settings
        }
        
        try:
            response = self.session.post(url, json=payload, stream=True)
            response.raise_for_status()
            
            for chunk in response.iter_content(chunk_size=chunk_size):
                if chunk:
                    yield chunk
                    
        except requests.exceptions.RequestException as e:
            logger.error(f"Error streaming speech: {str(e)}")
            raise
    
    def get_voices(self) -> List[Dict[str, Any]]:
        """
        Get list of available voices.
        
        Returns:
            List of voice dictionaries
        """
        url = f"{self.BASE_URL}/voices"
        
        try:
            response = self.session.get(url)
            response.raise_for_status()
            
            voices = response.json().get('voices', [])
            logger.info(f"Retrieved {len(voices)} voices")
            return voices
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting voices: {str(e)}")
            raise
    
    def get_voice(self, voice_id: str) -> Dict[str, Any]:
        """
        Get details for a specific voice.
        
        Args:
            voice_id: ID of the voice
        
        Returns:
            Voice details dictionary
        """
        url = f"{self.BASE_URL}/voices/{voice_id}"
        
        try:
            response = self.session.get(url)
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting voice {voice_id}: {str(e)}")
            raise
    
    def clone_voice(self, name: str, files: List[str],
                   description: str = "", labels: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Clone a voice from audio samples.
        
        Args:
            name: Name for the cloned voice
            files: List of audio file paths to use for cloning
            description: Optional description of the voice
            labels: Optional labels/tags for the voice
        
        Returns:
            Created voice information including voice_id
        """
        url = f"{self.BASE_URL}/voices/add"
        
        # Prepare multipart form data
        files_data = []
        for file_path in files:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Audio file not found: {file_path}")
            
            with open(file_path, 'rb') as f:
                files_data.append(('files', (os.path.basename(file_path), f, 'audio/mpeg')))
        
        data = {
            'name': name,
            'description': description
        }
        
        if labels:
            data['labels'] = labels
        
        # Remove Content-Type header for multipart upload
        headers = {'xi-api-key': self.api_key}
        
        try:
            response = requests.post(url, headers=headers, data=data, files=files_data)
            response.raise_for_status()
            
            voice_data = response.json()
            logger.info(f"Successfully cloned voice: {name} (ID: {voice_data.get('voice_id')})")
            return voice_data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error cloning voice: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response content: {e.response.text}")
            raise
    
    def delete_voice(self, voice_id: str) -> bool:
        """
        Delete a cloned voice.
        
        Args:
            voice_id: ID of the voice to delete
        
        Returns:
            True if successful
        """
        url = f"{self.BASE_URL}/voices/{voice_id}"
        
        try:
            response = self.session.delete(url)
            response.raise_for_status()
            
            logger.info(f"Successfully deleted voice: {voice_id}")
            return True
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error deleting voice {voice_id}: {str(e)}")
            raise
    
    def get_models(self) -> List[Dict[str, Any]]:
        """
        Get list of available models.
        
        Returns:
            List of model dictionaries
        """
        url = f"{self.BASE_URL}/models"
        
        try:
            response = self.session.get(url)
            response.raise_for_status()
            
            models = response.json()
            logger.info(f"Retrieved {len(models)} models")
            return models
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting models: {str(e)}")
            raise
    
    def get_user_info(self) -> Dict[str, Any]:
        """
        Get user account information including usage.
        
        Returns:
            User information dictionary
        """
        url = f"{self.BASE_URL}/user"
        
        try:
            response = self.session.get(url)
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting user info: {str(e)}")
            raise
    
    def get_history(self, page_size: int = 100, start_after_history_item_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get generation history.
        
        Args:
            page_size: Number of items per page
            start_after_history_item_id: ID to start after for pagination
        
        Returns:
            History data with items and pagination info
        """
        url = f"{self.BASE_URL}/history"
        
        params = {'page_size': page_size}
        if start_after_history_item_id:
            params['start_after_history_item_id'] = start_after_history_item_id
        
        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting history: {str(e)}")
            raise
    
    def get_history_item_audio(self, history_item_id: str) -> bytes:
        """
        Download audio for a history item.
        
        Args:
            history_item_id: ID of the history item
        
        Returns:
            Audio data as bytes
        """
        url = f"{self.BASE_URL}/history/{history_item_id}/audio"
        
        try:
            response = self.session.get(url)
            response.raise_for_status()
            
            return response.content
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error downloading history audio: {str(e)}")
            raise
    
    def validate_api_key(self) -> bool:
        """
        Validate that the API key is working.
        
        Returns:
            True if API key is valid
        """
        try:
            self.get_user_info()
            return True
        except:
            return False