import axios from 'axios';

const API_BASE_URL = '/api';

const api = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

// Health check
export const checkHealth = async () => {
    const response = await api.get('/health');
    return response.data;
};

// Media endpoints
export const listMedia = async () => {
    const response = await api.get('/media/list');
    return response.data;
};

export const uploadMedia = async (file, onProgress) => {
    const formData = new FormData();
    formData.append('file', file);

    const response = await api.post('/media/upload', formData, {
        headers: {
            'Content-Type': 'multipart/form-data',
        },
        onUploadProgress: (progressEvent) => {
            if (onProgress) {
                const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
                onProgress(percentCompleted);
            }
        },
    });

    return response.data;
};

export const downloadYouTube = async (url) => {
    const response = await api.post('/media/youtube', { url });
    return response.data;
};

// Transcription endpoints
export const transcribeAudio = async (path) => {
    const response = await api.post('/transcribe', { path });
    return response.data;
};

export const listTranscripts = async () => {
    const response = await api.get('/transcripts/list');
    return response.data;
};

export const getTranscriptContent = async (path) => {
    const response = await api.post('/transcripts/content', { path });
    return response.data;
};

// TTS endpoints
export const generateTTS = async (transcriptPath, ttsMode) => {
    const response = await api.post('/tts/generate', {
        transcript_path: transcriptPath,
        tts_mode: ttsMode
    });
    return response.data;
};

// PDF endpoints
export const generatePDF = async (transcriptPath, modelName, summaryMode, provider, latexCode = null) => {
    const response = await api.post('/pdf/generate', {
        transcript_path: transcriptPath,
        model_name: modelName,
        summary_mode: summaryMode,
        provider: provider,
        latex_code: latexCode
    });
    return response.data;
};

export const listLatexFiles = async () => {
    const response = await api.get('/latex/list');
    return response.data;
};

// Quiz endpoints
export const generateQuiz = async (latexPath, modelName, numQuestions) => {
    const response = await api.post('/quiz/generate', {
        latex_path: latexPath,
        model_name: modelName,
        num_questions: numQuestions,
    });
    return response.data;
};

// Download endpoint
export const downloadFile = async (path) => {
    const response = await api.post('/download', { path }, {
        responseType: 'blob',
    });
    return response.data;
};

export default api;
