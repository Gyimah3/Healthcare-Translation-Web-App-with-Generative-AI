# Medical Voice Translator

A real-time medical translation system that enables multilingual communication in healthcare settings using AI technologies.

## Features

- Real-time speech transcription using AssemblyAI
- Medical-focused translation using OpenAI GPT-4
- Text-to-speech output using ElevenLabs
- Support for 20+ languages
- Real-time transcript and translation display
- Instant audio playback of translations

## Technology Stack

- **Frontend**: HTML, CSS, JavaScript with WebSocket
- **Backend**: FastAPI (Python)
- **AI Services**:
  - AssemblyAI - Real-time speech transcription
  - OpenAI GPT-4 - Medical translation
  - ElevenLabs - Text-to-speech synthesis

## Prerequisites

- Python 3.8+
- API keys for:
  - AssemblyAI
  - OpenAI 
  - ElevenLabs

## Installation

1. Clone the repository
2. Install dependencies
3. Create a `.env` file in the root directory with your API keys

## Usage

1. Start the FastAPI server `uvicorn main:app --relod`
2. Open `index.html` in your browser or start a simple HTTP server
3. Select source and target languages from the dropdown menus
4. Click the "Start Recording" button to begin speaking
5. View real-time transcription and translation on screen
6. Click "Stop Recording" when finished, and play translation

`Backend server is live on ->` https://healthcare-translation-web-app-with-ibvg.onrender.com/

## HTML Demo

The included HTML file provides a simple interface for testing the system before designing the frontend. **Note: This is intended for demonstration and testing purposes only and is not recommended for production use.**

## Future Work

### AI Recommendation System
- Implement an intelligent system that analyzes conversation transcripts to provide contextual medical recommendations
- Develop machine learning models trained on medical dialogue datasets to identify patient needs
- Create a knowledge base of standard medical protocols and procedures
- Build a recommendation engine that suggests appropriate responses to healthcare providers based on:
  - Patient symptoms described in conversation
  - Medical history (if integrated with EHR systems)
  - Best practices for specific conditions
  - Cultural considerations based on patient background
- Implement confidence scoring for recommendations to indicate reliability
- Add explanation capabilities to justify why certain recommendations are made

### Voice-to-Voice Agent
- Develop an autonomous conversational agent that can facilitate medical discussions without manual intervention
- Implement conversation state tracking to understand context and conversation flow
- Create natural language understanding components specifically trained on medical terminology
- Build speaker recognition to differentiate between healthcare provider and patient voices
- Develop automatic language detection to eliminate the need for manual language selection
- Implement continuous streaming translation that operates in real-time during conversation
- Add emotional intelligence capabilities to detect stress, pain, or confusion in patient's voice
- Create automatic summarization of conversations for medical documentation

### Enhanced Medical Translation
- Expand specialized medical terminology coverage across all supported languages
- Incorporate medical ontologies and standardized terminology (SNOMED CT, ICD-10, etc.)
- Develop domain-specific translation models for specialized fields (cardiology, neurology, pediatrics, etc.)
- Implement medical abbreviation and acronym handling
- Add support for regional medical dialects and expressions
- Create custom prompting techniques for OpenAI model to improve medical translation accuracy

### Technical Improvements
- Optimize real-time processing to reduce latency below 500ms
- Implement edge deployment for offline capabilities in areas with poor connectivity
- Create adaptive noise filtering for hospital environments
- Develop battery optimization for mobile deployment
- Implement distributed processing architecture for handling multiple simultaneous sessions
- Design fallback mechanisms for service disruptions
- Build comprehensive logging and analytics for system performance monitoring

### Integration & Expansion
- Develop plugins for popular telehealth platforms
- Build mobile applications for iOS and Android
- Design specialized hardware devices optimized for hospital environments
- Create administrative dashboard for managing multiple devices and users
- Implement team translation capabilities for complex medical consultations with multiple specialists

### Security & Compliance
- Implement end-to-end encryption for all communications
- Develop HIPAA-compliant data storage and processing
- Create comprehensive audit trails for regulatory compliance
- Design user authentication and authorization systems
- Implement automated PHI (Protected Health Information) detection and handling
- Develop data retention and deletion policies following medical records regulations
- Create privacy-preserving machine learning techniques to improve models without exposing patient data

## Security Considerations



## License

[MIT License](LICENSE)

## Disclaimer

The HTML demo is provided in this repo for testing purposes only and should not be used in production environments without proper security implementations and code review.
