import { useState, useRef, useEffect } from 'react';
import { FaRobot, FaUser, FaPaperPlane, FaTools, FaFileDownload } from 'react-icons/fa';

const ChatTab = ({ showLoading, hideLoading }) => {
    const [messages, setMessages] = useState([
        {
            role: 'assistant',
            content: 'Hello! I am your AI assistant. I can help you download YouTube videos, transcribe audio, generate PDF summaries, and even create quizzes. What can I do for you today?'
        }
    ]);
    const [input, setInput] = useState('');
    const [isTyping, setIsTyping] = useState(false);
    const messagesEndRef = useRef(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const handleSend = async (e) => {
        e.preventDefault();
        if (!input.trim()) return;

        const userMessage = { role: 'user', content: input };
        const updatedMessages = [...messages, userMessage];
        setMessages(updatedMessages);
        setInput('');
        setIsTyping(true);

        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    messages: updatedMessages,
                    model_name: 'qwen3:30b-instruct',
                    provider: 'Ollama'
                })
            });

            const data = await response.json();

            if (data.success) {
                setMessages(prev => [...prev, {
                    role: 'assistant',
                    content: data.message,
                    tool_results: data.tool_results
                }]);
            } else {
                setMessages(prev => [...prev, {
                    role: 'assistant',
                    content: `Error: ${data.error || 'Something went wrong'}`
                }]);
            }
        } catch (error) {
            setMessages(prev => [...prev, {
                role: 'assistant',
                content: `Error: Failed to connect to server.`
            }]);
        } finally {
            setIsTyping(false);
        }
    };

    return (
        <div className="chat-container">
            <div className="chat-messages">
                {messages.map((msg, index) => (
                    <div key={index} className={`message-wrapper ${msg.role}`}>
                        <div className="message-icon">
                            {msg.role === 'assistant' ? <FaRobot /> : <FaUser />}
                        </div>
                        <div className="message-content">
                            <div className="message-bubble">
                                {msg.content}
                            </div>
                            {msg.tool_results && msg.tool_results.length > 0 && (
                                <div className="tool-execution-info">
                                    <div className="tool-header">
                                        <FaTools /> Actions Performed:
                                    </div>
                                    <ul className="tool-list">
                                        {msg.tool_results.map((tr, i) => (
                                            <li key={i} className="tool-item">
                                                <span className="tool-name">{tr.tool}</span>: {tr.result.status === 'success' ? '✅ Completed' : '❌ Failed'}
                                                {tr.result.path && (
                                                    <div className="file-info">
                                                        <span>{tr.result.filename || 'File generated'}</span>
                                                    </div>
                                                )}
                                            </li>
                                        ))}
                                    </ul>
                                </div>
                            )}
                        </div>
                    </div>
                ))}
                {isTyping && (
                    <div className="message-wrapper assistant">
                        <div className="message-icon"><FaRobot /></div>
                        <div className="message-bubble typing">
                            <span className="dot"></span>
                            <span className="dot"></span>
                            <span className="dot"></span>
                        </div>
                    </div>
                )}
                <div ref={messagesEndRef} />
            </div>

            <form className="chat-input-area" onSubmit={handleSend}>
                <input
                    type="text"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    placeholder="Ask me anything..."
                    disabled={isTyping}
                />
                <button type="submit" disabled={isTyping || !input.trim()}>
                    <FaPaperPlane />
                </button>
            </form>
        </div>
    );
};

export default ChatTab;
