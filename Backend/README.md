# R.A.M.A Backend - Model Configuration

This backend now uses Google Gemini by default, with Ollama as an offline fallback.

Environment variables (set in a local .env file, which is already gitignored):

- GEMINI_API_KEY=your_key_here
- GEMINI_MODEL=gemini-1.5-flash (optional; defaults to gemini-1.5-flash)
- GEMINI_EMBEDDING_MODEL=models/text-embedding-004 (optional; defaults to text-embedding-004)
- OLLAMA_ENDPOINT=http://localhost:11434 (defaults include /api path as needed)
- OLLAMA_MODEL=mistral (optional)
- OLLAMA_EMBEDDING_MODEL=nomic-embed-text (optional)

To run locally offline, install and start Ollama, and pull the models you want:

- ollama serve
- ollama pull mistral
- ollama pull nomic-embed-text

The FastAPI service will call Gemini when GEMINI_API_KEY is set, otherwise it will use Ollama.
