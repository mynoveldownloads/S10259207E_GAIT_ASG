import { useState, useEffect } from 'react';
import { FaFileAlt, FaDownload, FaEye } from 'react-icons/fa';
import { listTranscripts, getTranscriptContent, downloadFile } from '../utils/api';

function TranscriptsTab({ showLoading, hideLoading }) {
    const [transcripts, setTranscripts] = useState([]);
    const [selectedTranscript, setSelectedTranscript] = useState(null);
    const [content, setContent] = useState('');
    const [error, setError] = useState('');

    useEffect(() => {
        loadTranscripts();
    }, []);

    const loadTranscripts = async () => {
        try {
            showLoading('Loading transcripts...');
            const data = await listTranscripts();
            hideLoading();

            if (data.success) {
                setTranscripts(data.transcripts);
            }
        } catch (err) {
            hideLoading();
            setError(err.response?.data?.error || err.message || 'Failed to load transcripts');
        }
    };

    const viewTranscript = async (transcript) => {
        try {
            showLoading('Loading transcript content...');
            const data = await getTranscriptContent(transcript.path);
            hideLoading();

            if (data.success) {
                setSelectedTranscript(transcript);
                setContent(data.content);
                setError('');
            }
        } catch (err) {
            hideLoading();
            setError(err.response?.data?.error || err.message || 'Failed to load content');
        }
    };

    const handleDownload = async (transcript) => {
        try {
            showLoading('Downloading...');
            const blob = await downloadFile(transcript.path);
            hideLoading();

            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = transcript.name;
            a.click();
            URL.revokeObjectURL(url);
        } catch (err) {
            hideLoading();
            setError(err.response?.data?.error || err.message || 'Download failed');
        }
    };

    return (
        <div>
            <div className="card">
                <div className="card-header">
                    <h2 className="card-title">
                        <FaFileAlt />
                        Saved Transcripts
                    </h2>
                    <button className="btn btn-secondary btn-sm" onClick={loadTranscripts}>
                        Refresh
                    </button>
                </div>
                <div className="card-body">
                    {error && (
                        <div className="alert alert-error">
                            {error}
                        </div>
                    )}

                    {transcripts.length === 0 ? (
                        <div className="alert alert-info">
                            No transcripts found. Upload and transcribe a file first!
                        </div>
                    ) : (
                        <div>
                            {transcripts.map((transcript) => (
                                <div key={transcript.path} className="list-item">
                                    <div className="list-item-content">
                                        <FaFileAlt style={{ color: 'var(--accent-primary)' }} />
                                        <div>
                                            <div className="list-item-title">{transcript.name}</div>
                                            <div className="list-item-meta">
                                                {(transcript.size / 1024).toFixed(2)} KB
                                            </div>
                                        </div>
                                    </div>
                                    <div className="list-item-actions">
                                        <button
                                            className="btn btn-secondary btn-sm"
                                            onClick={() => viewTranscript(transcript)}
                                        >
                                            <FaEye />
                                            View
                                        </button>
                                        <button
                                            className="btn btn-primary btn-sm"
                                            onClick={() => handleDownload(transcript)}
                                        >
                                            <FaDownload />
                                            Download
                                        </button>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            </div>

            {selectedTranscript && (
                <div className="card">
                    <div className="card-header">
                        <h3 className="card-title">
                            {selectedTranscript.name}
                        </h3>
                        <button
                            className="btn btn-secondary btn-sm"
                            onClick={() => setSelectedTranscript(null)}
                        >
                            Close
                        </button>
                    </div>
                    <div className="card-body">
                        <textarea
                            className="input-field"
                            value={content}
                            readOnly
                            style={{ minHeight: '400px', fontFamily: 'var(--font-mono)' }}
                        />
                    </div>
                </div>
            )}
        </div>
    );
}

export default TranscriptsTab;
