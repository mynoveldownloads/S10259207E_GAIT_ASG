import { useState, useEffect } from 'react';
import { FaVolumeUp, FaFilePdf, FaMagic } from 'react-icons/fa';
import { listTranscripts, generateTTS, generatePDF, downloadFile } from '../utils/api';

function FeaturesTab({ showLoading, hideLoading }) {
    const [transcripts, setTranscripts] = useState([]);
    const [selectedTranscript, setSelectedTranscript] = useState('');
    const [modelName, setModelName] = useState('gpt-oss:latest');
    const [summaryMode, setSummaryMode] = useState('concise');
    const [error, setError] = useState('');
    const [success, setSuccess] = useState('');
    const [ttsResult, setTtsResult] = useState(null);
    const [pdfResult, setPdfResult] = useState(null);
    const [ttsMode, setTtsMode] = useState('transcript');
    const [pdfProvider, setPdfProvider] = useState('OpenRouter');
    const [streamingLatex, setStreamingLatex] = useState('');
    const [isStreaming, setIsStreaming] = useState(false);

    useEffect(() => {
        loadTranscripts();
    }, []);

    useEffect(() => {
        if (pdfProvider === 'OpenRouter') {
            setModelName('openai/gpt-oss-120b');
        } else {
            setModelName('gpt-oss:latest');
        }
    }, [pdfProvider]);

    const loadTranscripts = async () => {
        try {
            const data = await listTranscripts();
            if (data.success) {
                setTranscripts(data.transcripts);
            }
        } catch (err) {
            console.error('Error loading transcripts:', err);
        }
    };

    const handleGenerateTTS = async () => {
        if (!selectedTranscript) {
            setError('Please select a transcript');
            return;
        }

        try {
            setError('');
            setSuccess('');
            showLoading(ttsMode === 'summary' ? 'Generating conversational summary and speech...' : 'Generating speech audio...');

            const data = await generateTTS(selectedTranscript, ttsMode);
            hideLoading();

            if (data.success) {
                setTtsResult(data);
                setSuccess('Audio generated successfully!');
            } else {
                setError(data.error || 'TTS generation failed');
            }
        } catch (err) {
            hideLoading();
            setError(err.response?.data?.error || err.message || 'TTS generation failed');
        }
    };

    const handleGeneratePDF = async () => {
        if (!selectedTranscript) {
            setError('Please select a transcript');
            return;
        }

        try {
            setError('');
            setSuccess('');
            setStreamingLatex('');
            setIsStreaming(true);
            setPdfResult(null);

            // Step 1: Stream LaTeX code
            const response = await fetch('/api/pdf/stream_latex', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    transcript_path: selectedTranscript,
                    model_name: modelName,
                    summary_mode: summaryMode,
                    provider: pdfProvider
                })
            });

            if (!response.ok) throw new Error('Failed to start LaTeX streaming');

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let accumulatedLatex = '';

            while (true) {
                const { value, done } = await reader.read();
                if (done) break;
                const chunk = decoder.decode(value, { stream: true });
                accumulatedLatex += chunk;
                setStreamingLatex(accumulatedLatex);

                // Auto-scroll the streaming box
                const box = document.getElementById('latex-stream-box');
                if (box) box.scrollTop = box.scrollHeight;
            }

            setIsStreaming(false);
            showLoading('Compiling PDF summary... This may take a moment');

            // Step 2: Compile PDF using the streamed LaTeX
            const data = await generatePDF(selectedTranscript, modelName, summaryMode, pdfProvider, accumulatedLatex);
            hideLoading();

            if (data.success) {
                setPdfResult(data);
                setSuccess('PDF generated successfully!');
            } else {
                setError(data.error || 'PDF generation failed');
                if (data.tex_path) {
                    setPdfResult({ tex_path: data.tex_path, tex_filename: data.tex_filename });
                }
            }
        } catch (err) {
            hideLoading();
            setError(err.response?.data?.error || err.message || 'PDF generation failed');
        }
    };

    const handleDownload = async (path, filename) => {
        try {
            showLoading('Downloading...');
            const blob = await downloadFile(path);
            hideLoading();

            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
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
                        <FaMagic />
                        Generate Features from Transcripts
                    </h2>
                </div>
                <div className="card-body">
                    {error && (
                        <div className="alert alert-error">
                            {error}
                        </div>
                    )}

                    {success && (
                        <div className="alert alert-success">
                            {success}
                        </div>
                    )}

                    {transcripts.length === 0 ? (
                        <div className="alert alert-info">
                            No transcripts available. Generate a transcript first!
                        </div>
                    ) : (
                        <div className="input-group">
                            <label className="input-label">Select Transcript</label>
                            <select
                                className="input-field"
                                value={selectedTranscript}
                                onChange={(e) => setSelectedTranscript(e.target.value)}
                            >
                                <option value="">-- Select a transcript --</option>
                                {transcripts.map((transcript) => (
                                    <option key={transcript.path} value={transcript.path}>
                                        {transcript.name}
                                    </option>
                                ))}
                            </select>
                        </div>
                    )}
                </div>
            </div>

            <div className="grid grid-2">
                {/* TTS Section */}
                <div className="card">
                    <div className="card-header">
                        <h3 className="card-title">
                            <FaVolumeUp />
                            Text-to-Speech (TTS)
                        </h3>
                    </div>
                    <div className="card-body">
                        <p className="text-secondary" style={{ marginBottom: 'var(--spacing-lg)' }}>
                            Generate audio from your transcript using Kokoro TTS.
                        </p>

                        <div className="input-group">
                            <label className="input-label">TTS Mode</label>
                            <select
                                className="input-field"
                                value={ttsMode}
                                onChange={(e) => setTtsMode(e.target.value)}
                            >
                                <option value="transcript">Audio Transcript (Direct)</option>
                                <option value="summary">Audio Summary (AI Conversational)</option>
                            </select>
                        </div>

                        <button
                            className="btn btn-primary btn-lg"
                            onClick={handleGenerateTTS}
                            disabled={!selectedTranscript}
                            style={{ width: '100%' }}
                        >
                            <FaVolumeUp />
                            Generate Audio
                        </button>

                        {ttsResult && (
                            <div style={{ marginTop: 'var(--spacing-lg)' }}>
                                <div className="alert alert-success">
                                    Audio generated: {ttsResult.filename}
                                </div>
                                <div style={{ marginTop: 'var(--spacing-md)' }}>
                                    <audio controls src={ttsResult.audio_url} style={{ width: '100%', borderRadius: 'var(--radius-md)' }}>
                                        Your browser does not support the audio element.
                                    </audio>
                                </div>
                                <button
                                    className="btn btn-secondary btn-sm"
                                    onClick={() => handleDownload(ttsResult.audio_path, ttsResult.filename)}
                                    style={{ width: '100%', marginTop: 'var(--spacing-sm)' }}
                                >
                                    Download Audio File
                                </button>
                            </div>
                        )}
                    </div>
                </div>

                {/* PDF Section */}
                <div className="card">
                    <div className="card-header">
                        <h3 className="card-title">
                            <FaFilePdf />
                            PDF Summary
                        </h3>
                    </div>
                    <div className="card-body">
                        <p className="text-secondary" style={{ marginBottom: 'var(--spacing-lg)' }}>
                            Generate a condensed PDF summary using AI (requires Ollama).
                        </p>

                        <div className="input-group">
                            <label className="input-label">AI Provider</label>
                            <select
                                className="input-field"
                                value={pdfProvider}
                                onChange={(e) => {
                                    setPdfProvider(e.target.value);
                                    if (e.target.value === 'OpenRouter') {
                                        setModelName('google/gemini-2.5-flash-lite');
                                    } else {
                                        setModelName('gpt-oss:latest');
                                    }
                                }}
                            >
                                <option value="OpenRouter">OpenRouter (Cloud)</option>
                                <option value="Ollama">Ollama (Local)</option>
                            </select>
                        </div>

                        <div className="input-group">
                            <label className="input-label">Model Name</label>
                            <input
                                type="text"
                                className="input-field"
                                value={modelName}
                                onChange={(e) => setModelName(e.target.value)}
                                placeholder={pdfProvider === 'OpenRouter' ? "openai/gpt-oss-120b" : "gpt-oss:latest"}
                            />
                        </div>

                        {(streamingLatex || isStreaming) && (
                            <div style={{ marginTop: 'var(--spacing-lg)' }}>
                                <label className="input-label">LaTeX Stream (Live Debug)</label>
                                <div
                                    id="latex-stream-box"
                                    className="input-field"
                                    style={{
                                        height: '400px',
                                        overflowY: 'auto',
                                        backgroundColor: '#1e1e1e',
                                        color: '#d4d4d4',
                                        fontFamily: 'monospace',
                                        padding: 'var(--spacing-md)',
                                        fontSize: '12px',
                                        whiteSpace: 'pre-wrap',
                                        borderRadius: 'var(--radius-md)',
                                        border: '1px solid var(--border-color)'
                                    }}
                                >
                                    {streamingLatex || 'Waiting for stream...'}
                                    {isStreaming && <span className="cursor-blink">|</span>}
                                </div>
                            </div>
                        )}

                        <div className="input-group">
                            <label className="input-label">Summary Mode</label>
                            <select
                                className="input-field"
                                value={summaryMode}
                                onChange={(e) => setSummaryMode(e.target.value)}
                            >
                                <option value="concise">Concise Summary</option>
                                <option value="detailed">Detailed Coverage</option>
                            </select>
                        </div>

                        <button
                            className="btn btn-primary btn-lg"
                            onClick={handleGeneratePDF}
                            disabled={!selectedTranscript}
                            style={{ width: '100%' }}
                        >
                            <FaFilePdf />
                            Generate PDF
                        </button>

                        {pdfResult && (
                            <div style={{ marginTop: 'var(--spacing-lg)' }}>
                                {pdfResult.pdf_path ? (
                                    <>
                                        <div className="alert alert-success">
                                            PDF generated successfully!
                                        </div>
                                        <div className="flex gap-sm" style={{ flexDirection: 'column' }}>
                                            <button
                                                className="btn btn-secondary"
                                                onClick={() => handleDownload(pdfResult.pdf_path, pdfResult.pdf_filename)}
                                            >
                                                Download PDF
                                            </button>
                                            <button
                                                className="btn btn-secondary"
                                                onClick={() => handleDownload(pdfResult.tex_path, pdfResult.tex_filename)}
                                            >
                                                Download LaTeX Source
                                            </button>
                                        </div>
                                    </>
                                ) : (
                                    <>
                                        <div className="alert alert-warning">
                                            PDF compilation failed, but LaTeX source is available.
                                        </div>
                                        <button
                                            className="btn btn-secondary"
                                            onClick={() => handleDownload(pdfResult.tex_path, pdfResult.tex_filename)}
                                            style={{ width: '100%' }}
                                        >
                                            Download LaTeX Source
                                        </button>
                                    </>
                                )}
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}

export default FeaturesTab;
