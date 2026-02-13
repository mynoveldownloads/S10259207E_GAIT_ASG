import { useState, useRef } from 'react';
import { FaUpload, FaYoutube, FaFile, FaPlay } from 'react-icons/fa';
import { uploadMedia, downloadYouTube, transcribeAudio, listMedia } from '../utils/api';

function UploadTab({ showLoading, hideLoading }) {
    const [uploadMethod, setUploadMethod] = useState('file');
    const [youtubeUrl, setYoutubeUrl] = useState('');
    const [selectedFile, setSelectedFile] = useState(null);
    const [uploadProgress, setUploadProgress] = useState(0);
    const [existingFiles, setExistingFiles] = useState([]);
    const [selectedExisting, setSelectedExisting] = useState('');
    const [result, setResult] = useState(null);
    const [error, setError] = useState('');
    const fileInputRef = useRef(null);

    const loadExistingFiles = async () => {
        try {
            const data = await listMedia();
            if (data.success) {
                setExistingFiles(data.files);
            }
        } catch (err) {
            console.error('Error loading files:', err);
        }
    };

    const handleFileSelect = (e) => {
        const file = e.target.files[0];
        if (file) {
            setSelectedFile(file);
            setError('');
        }
    };

    const handleDrop = (e) => {
        e.preventDefault();
        const file = e.dataTransfer.files[0];
        if (file) {
            setSelectedFile(file);
            setError('');
        }
    };

    const handleDragOver = (e) => {
        e.preventDefault();
    };

    const processFile = async (filePath) => {
        try {
            showLoading('Transcribing audio... This may take a while');
            const transcribeData = await transcribeAudio(filePath);
            hideLoading();

            if (transcribeData.success) {
                setResult({
                    type: transcribeData.type,
                    transcript: transcribeData.transcript,
                    timestamped: transcribeData.timestamped,
                    transcript_path: transcribeData.transcript_path,
                    timestamped_path: transcribeData.timestamped_path,
                });
                setError('');
            } else {
                setError(transcribeData.error || 'Transcription failed');
            }
        } catch (err) {
            hideLoading();
            setError(err.response?.data?.error || err.message || 'Transcription failed');
        }
    };

    const handleFileUpload = async () => {
        if (!selectedFile) {
            setError('Please select a file');
            return;
        }

        try {
            setError('');
            showLoading('Extracting Content...');

            const uploadData = await uploadMedia(selectedFile, (progress) => {
                setUploadProgress(progress);
            });

            hideLoading();

            if (uploadData.success) {
                await processFile(uploadData.path);
            } else {
                setError(uploadData.error || 'Upload failed');
            }
        } catch (err) {
            hideLoading();
            setError(err.response?.data?.error || err.message || 'Upload failed');
        }
    };

    const handleYouTubeDownload = async () => {
        if (!youtubeUrl) {
            setError('Please enter a YouTube URL');
            return;
        }

        try {
            setError('');
            showLoading('Downloading from YouTube...');

            const downloadData = await downloadYouTube(youtubeUrl);
            hideLoading();

            if (downloadData.success) {
                await processFile(downloadData.path);
            } else {
                setError(downloadData.error || 'Download failed');
            }
        } catch (err) {
            hideLoading();
            setError(err.response?.data?.error || err.message || 'Download failed');
        }
    };

    const handleExistingFile = async () => {
        if (!selectedExisting) {
            setError('Please select a file');
            return;
        }

        await processFile(selectedExisting);
    };

    const downloadTranscript = (content, filename) => {
        const blob = new Blob([content], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        a.click();
        URL.revokeObjectURL(url);
    };

    return (
        <div>
            <div className="card">
                <div className="card-header">
                    <h2 className="card-title">
                        <FaUpload />
                        Upload and Extract Content
                    </h2>
                </div>
                <div className="card-body">
                    <div className="nav-tabs" style={{ marginBottom: 'var(--spacing-lg)', borderBottom: 'none' }}>
                        <button
                            className={`nav-tab ${uploadMethod === 'file' ? 'active' : ''}`}
                            onClick={() => setUploadMethod('file')}
                        >
                            <FaFile />
                            File Upload
                        </button>
                        <button
                            className={`nav-tab ${uploadMethod === 'youtube' ? 'active' : ''}`}
                            onClick={() => setUploadMethod('youtube')}
                        >
                            <FaYoutube />
                            YouTube URL
                        </button>
                        <button
                            className={`nav-tab ${uploadMethod === 'existing' ? 'active' : ''}`}
                            onClick={() => {
                                setUploadMethod('existing');
                                loadExistingFiles();
                            }}
                        >
                            <FaFile />
                            Existing Files
                        </button>
                    </div>

                    {error && (
                        <div className="alert alert-error">
                            {error}
                        </div>
                    )}

                    {uploadMethod === 'file' && (
                        <div>
                            <div
                                className="file-upload-area"
                                onDrop={handleDrop}
                                onDragOver={handleDragOver}
                                onClick={() => fileInputRef.current?.click()}
                            >
                                <div className="file-upload-icon">
                                    <FaUpload />
                                </div>
                                <p className="file-upload-text">
                                    {selectedFile ? selectedFile.name : 'Click or drag file to upload'}
                                </p>
                                <p className="file-upload-hint">
                                    Supported: MP4, AVI, MOV, MP3, WAV, M4A, MKV, WebM, FLV, OGG, PDF, PPTX, DOCX, PNG, JPG, JPEG, WebP
                                </p>
                                <input
                                    ref={fileInputRef}
                                    type="file"
                                    accept=".mp4,.avi,.mov,.mp3,.wav,.m4a,.mkv,.webm,.flv,.ogg,.pdf,.pptx,.docx,.png,.jpg,.jpeg,.webp"
                                    onChange={handleFileSelect}
                                    style={{ display: 'none' }}
                                />
                            </div>

                            {uploadProgress > 0 && uploadProgress < 100 && (
                                <div className="progress-container">
                                    <div className="progress-bar">
                                        <div className="progress-fill" style={{ width: `${uploadProgress}%` }}></div>
                                    </div>
                                    <p className="progress-text">{uploadProgress}% uploaded</p>
                                </div>
                            )}

                            <button
                                className="btn btn-primary btn-lg"
                                onClick={handleFileUpload}
                                disabled={!selectedFile}
                                style={{ marginTop: 'var(--spacing-lg)', width: '100%' }}
                            >
                                <FaPlay />
                                Upload & Extract
                            </button>
                        </div>
                    )}

                    {uploadMethod === 'youtube' && (
                        <div>
                            <div className="input-group">
                                <label className="input-label">YouTube URL</label>
                                <input
                                    type="text"
                                    className="input-field"
                                    placeholder="https://www.youtube.com/watch?v=..."
                                    value={youtubeUrl}
                                    onChange={(e) => setYoutubeUrl(e.target.value)}
                                />
                            </div>

                            <button
                                className="btn btn-primary btn-lg"
                                onClick={handleYouTubeDownload}
                                disabled={!youtubeUrl}
                                style={{ width: '100%' }}
                            >
                                <FaYoutube />
                                Download & Extract
                            </button>
                        </div>
                    )}

                    {uploadMethod === 'existing' && (
                        <div>
                            <div className="input-group">
                                <label className="input-label">Select Existing File</label>
                                <select
                                    className="input-field"
                                    value={selectedExisting}
                                    onChange={(e) => setSelectedExisting(e.target.value)}
                                >
                                    <option value="">-- Select a file --</option>
                                    {existingFiles.map((file) => (
                                        <option key={file.path} value={file.path}>
                                            {file.name} ({(file.size / 1024 / 1024).toFixed(2)} MB)
                                        </option>
                                    ))}
                                </select>
                            </div>

                            <button
                                className="btn btn-primary btn-lg"
                                onClick={handleExistingFile}
                                disabled={!selectedExisting}
                                style={{ width: '100%' }}
                            >
                                <FaPlay />
                                Transcribe Selected File
                            </button>
                        </div>
                    )}
                </div>
            </div>

            {result && (
                <div className={result.type === 'media' ? "grid grid-2" : ""}>
                    <div className="card">
                        <div className="card-header">
                            <h3 className="card-title">
                                {result.type === 'media' ? 'Plain Transcript' : 'Extracted Text / OCR Result'}
                            </h3>
                        </div>
                        <div className="card-body">
                            <textarea
                                className="input-field"
                                value={result.transcript}
                                readOnly
                                style={{ minHeight: '400px' }}
                            />
                            <button
                                className="btn btn-secondary"
                                onClick={() => downloadTranscript(result.transcript, result.type === 'media' ? 'transcript.txt' : 'ocr_result.txt')}
                                style={{ marginTop: 'var(--spacing-md)', width: '100%' }}
                            >
                                Download {result.type === 'media' ? 'Transcript' : 'OCR Result'}
                            </button>
                        </div>
                    </div>

                    {result.type === 'media' && (
                        <div className="card">
                            <div className="card-header">
                                <h3 className="card-title">Timestamped Transcript</h3>
                            </div>
                            <div className="card-body">
                                <textarea
                                    className="input-field"
                                    value={result.timestamped}
                                    readOnly
                                    style={{ minHeight: '400px' }}
                                />
                                <button
                                    className="btn btn-secondary"
                                    onClick={() => downloadTranscript(result.timestamped, 'transcript_timestamped.txt')}
                                    style={{ marginTop: 'var(--spacing-md)', width: '100%' }}
                                >
                                    Download Timestamped
                                </button>
                            </div>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}

export default UploadTab;
