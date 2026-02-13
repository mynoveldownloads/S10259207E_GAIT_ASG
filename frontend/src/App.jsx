import { useState } from 'react';
import './index.css';
import UploadTab from './components/UploadTab';
import TranscriptsTab from './components/TranscriptsTab';
import FeaturesTab from './components/FeaturesTab';
import QuizTab from './components/QuizTab';
import ChatTab from './components/ChatTab';
import LoadingOverlay from './components/LoadingOverlay';
import { FaVideo, FaFileAlt, FaMagic, FaQuestionCircle, FaRobot } from 'react-icons/fa';

function App() {
    const [activeTab, setActiveTab] = useState('upload');
    const [loading, setLoading] = useState(false);
    const [loadingMessage, setLoadingMessage] = useState('');

    const tabs = [
        { id: 'upload', label: 'Upload & Transcribe', icon: <FaVideo /> },
        { id: 'transcripts', label: 'Transcripts', icon: <FaFileAlt /> },
        { id: 'features', label: 'Generate Features', icon: <FaMagic /> },
        { id: 'quiz', label: 'Interactive Quiz', icon: <FaQuestionCircle /> },
        { id: 'chat', label: 'AI Chatbot', icon: <FaRobot /> }
    ];

    const showLoading = (message) => {
        setLoading(true);
        setLoadingMessage(message);
    };

    const hideLoading = () => {
        setLoading(false);
        setLoadingMessage('');
    };

    return (
        <div className="app-container">
            {loading && <LoadingOverlay message={loadingMessage} />}

            <header className="app-header">
                <div className="header-content">
                    <div>
                        <h1 className="app-title">
                            <FaVideo />
                            Video Transcription Studio
                        </h1>
                        <p className="app-subtitle">
                            AI-powered transcription, summaries, and quiz generation
                        </p>
                    </div>
                </div>
            </header>

            <main className="main-content">
                <nav className="nav-tabs">
                    {tabs.map(tab => (
                        <button
                            key={tab.id}
                            className={`nav-tab ${activeTab === tab.id ? 'active' : ''}`}
                            onClick={() => setActiveTab(tab.id)}
                        >
                            {tab.icon}
                            {tab.label}
                        </button>
                    ))}
                </nav>

                <div className="tab-content fade-in">
                    {activeTab === 'upload' && (
                        <UploadTab showLoading={showLoading} hideLoading={hideLoading} />
                    )}
                    {activeTab === 'transcripts' && (
                        <TranscriptsTab showLoading={showLoading} hideLoading={hideLoading} />
                    )}
                    {activeTab === 'features' && (
                        <FeaturesTab showLoading={showLoading} hideLoading={hideLoading} />
                    )}
                    {activeTab === 'quiz' && (
                        <QuizTab showLoading={showLoading} hideLoading={hideLoading} />
                    )}
                    {activeTab === 'chat' && (
                        <ChatTab showLoading={showLoading} hideLoading={hideLoading} />
                    )}
                </div>
            </main>
        </div>
    );
}

export default App;
