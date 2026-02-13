import { useState, useEffect } from 'react';
import { FaQuestionCircle, FaCheckCircle, FaTimesCircle, FaRedo } from 'react-icons/fa';
import { listLatexFiles, generateQuiz } from '../utils/api';

function QuizTab({ showLoading, hideLoading }) {
    const [latexFiles, setLatexFiles] = useState([]);
    const [selectedLatex, setSelectedLatex] = useState('');
    const [modelName, setModelName] = useState('gpt-oss:latest');
    const [numQuestions, setNumQuestions] = useState(10);
    const [quizData, setQuizData] = useState(null);
    const [userAnswers, setUserAnswers] = useState({});
    const [submitted, setSubmitted] = useState(false);
    const [error, setError] = useState('');

    useEffect(() => {
        loadLatexFiles();
    }, []);

    const loadLatexFiles = async () => {
        try {
            const data = await listLatexFiles();
            if (data.success) {
                setLatexFiles(data.files);
            }
        } catch (err) {
            console.error('Error loading LaTeX files:', err);
        }
    };

    const handleGenerateQuiz = async () => {
        if (!selectedLatex) {
            setError('Please select a LaTeX summary');
            return;
        }

        try {
            setError('');
            showLoading(`Generating ${numQuestions} quiz questions...`);

            const data = await generateQuiz(selectedLatex, modelName, numQuestions);
            hideLoading();

            if (data.success) {
                setQuizData(data.quiz_data);
                setUserAnswers({});
                setSubmitted(false);
            } else {
                setError(data.error || 'Quiz generation failed');
            }
        } catch (err) {
            hideLoading();
            setError(err.response?.data?.error || err.message || 'Quiz generation failed');
        }
    };

    const handleAnswerSelect = (questionId, answer) => {
        if (!submitted) {
            setUserAnswers({
                ...userAnswers,
                [questionId]: answer
            });
        }
    };

    const handleSubmit = () => {
        setSubmitted(true);
    };

    const handleReset = () => {
        setUserAnswers({});
        setSubmitted(false);
    };

    const calculateScore = () => {
        if (!quizData) return { correct: 0, total: 0, percentage: 0 };

        const correct = quizData.questions.filter(
            q => userAnswers[q.id] === q.correct_answer
        ).length;
        const total = quizData.questions.length;
        const percentage = (correct / total) * 100;

        return { correct, total, percentage };
    };

    const getDifficultyClass = (difficulty) => {
        const diff = difficulty?.toLowerCase();
        if (diff === 'easy') return 'easy';
        if (diff === 'medium') return 'medium';
        if (diff === 'hard') return 'hard';
        return 'medium';
    };

    const score = calculateScore();

    return (
        <div>
            {!quizData ? (
                <div className="card">
                    <div className="card-header">
                        <h2 className="card-title">
                            <FaQuestionCircle />
                            Generate Quiz
                        </h2>
                    </div>
                    <div className="card-body">
                        {error && (
                            <div className="alert alert-error">
                                {error}
                            </div>
                        )}

                        {latexFiles.length === 0 ? (
                            <div className="alert alert-info">
                                No LaTeX summaries available. Generate a PDF summary first!
                            </div>
                        ) : (
                            <>
                                <div className="input-group">
                                    <label className="input-label">Select LaTeX Summary</label>
                                    <select
                                        className="input-field"
                                        value={selectedLatex}
                                        onChange={(e) => setSelectedLatex(e.target.value)}
                                    >
                                        <option value="">-- Select a summary --</option>
                                        {latexFiles.map((file) => (
                                            <option key={file.path} value={file.path}>
                                                {file.name}
                                            </option>
                                        ))}
                                    </select>
                                </div>

                                <div className="input-group">
                                    <label className="input-label">Ollama Model for Quiz</label>
                                    <input
                                        type="text"
                                        className="input-field"
                                        value={modelName}
                                        onChange={(e) => setModelName(e.target.value)}
                                        placeholder="gpt-oss:latest"
                                    />
                                </div>

                                <div className="input-group">
                                    <label className="input-label">Number of Questions</label>
                                    <input
                                        type="range"
                                        min="5"
                                        max="30"
                                        step="5"
                                        value={numQuestions}
                                        onChange={(e) => setNumQuestions(parseInt(e.target.value))}
                                        style={{ width: '100%' }}
                                    />
                                    <div className="text-center text-mono" style={{ marginTop: 'var(--spacing-sm)' }}>
                                        {numQuestions} questions
                                    </div>
                                </div>

                                <button
                                    className="btn btn-primary btn-lg"
                                    onClick={handleGenerateQuiz}
                                    disabled={!selectedLatex}
                                    style={{ width: '100%', marginTop: 'var(--spacing-lg)' }}
                                >
                                    <FaQuestionCircle />
                                    Generate Quiz
                                </button>
                            </>
                        )}
                    </div>
                </div>
            ) : (
                <div>
                    <div className="card">
                        <div className="card-header">
                            <div>
                                <h2 className="card-title">
                                    {quizData.quiz_title || 'Interactive Quiz'}
                                </h2>
                                <p className="text-secondary text-mono" style={{ marginTop: 'var(--spacing-xs)' }}>
                                    Total Questions: {quizData.total_questions || quizData.questions.length}
                                </p>
                            </div>
                            <button
                                className="btn btn-secondary"
                                onClick={() => {
                                    setQuizData(null);
                                    setUserAnswers({});
                                    setSubmitted(false);
                                }}
                            >
                                New Quiz
                            </button>
                        </div>
                    </div>

                    {quizData.questions.map((question) => {
                        const userAnswer = userAnswers[question.id];
                        const isCorrect = userAnswer === question.correct_answer;

                        return (
                            <div key={question.id} className="quiz-question fade-in">
                                <div className="quiz-question-header">
                                    <span className="quiz-question-number">
                                        Question {question.id}
                                    </span>
                                    <span className={`quiz-difficulty ${getDifficultyClass(question.difficulty)}`}>
                                        {question.difficulty || 'Medium'}
                                    </span>
                                </div>

                                <p className="quiz-question-text">{question.question}</p>

                                <div className="quiz-options">
                                    {Object.entries(question.options).map(([key, value]) => {
                                        const isSelected = userAnswer === key;
                                        const isCorrectAnswer = key === question.correct_answer;

                                        let optionClass = 'quiz-option';
                                        if (submitted) {
                                            if (isCorrectAnswer) {
                                                optionClass += ' correct';
                                            } else if (isSelected && !isCorrect) {
                                                optionClass += ' incorrect';
                                            }
                                        } else if (isSelected) {
                                            optionClass += ' selected';
                                        }

                                        return (
                                            <div
                                                key={key}
                                                className={optionClass}
                                                onClick={() => handleAnswerSelect(question.id, key)}
                                            >
                                                <span className="quiz-option-letter">{key}</span>
                                                <span>{value}</span>
                                            </div>
                                        );
                                    })}
                                </div>

                                {submitted && (
                                    <div className="quiz-explanation">
                                        {isCorrect ? (
                                            <div style={{ color: 'var(--accent-success)', marginBottom: 'var(--spacing-sm)' }}>
                                                <FaCheckCircle style={{ marginRight: 'var(--spacing-xs)' }} />
                                                Correct!
                                            </div>
                                        ) : userAnswer ? (
                                            <div style={{ color: 'var(--accent-error)', marginBottom: 'var(--spacing-sm)' }}>
                                                <FaTimesCircle style={{ marginRight: 'var(--spacing-xs)' }} />
                                                Incorrect. Correct answer: {question.correct_answer}
                                            </div>
                                        ) : (
                                            <div style={{ color: 'var(--accent-warning)', marginBottom: 'var(--spacing-sm)' }}>
                                                Not answered. Correct answer: {question.correct_answer}
                                            </div>
                                        )}
                                        <strong>Explanation:</strong> {question.explanation}
                                    </div>
                                )}
                            </div>
                        );
                    })}

                    <div className="card">
                        <div className="card-body">
                            <div className="flex gap-md" style={{ flexWrap: 'wrap' }}>
                                {!submitted ? (
                                    <button
                                        className="btn btn-primary btn-lg"
                                        onClick={handleSubmit}
                                        style={{ flex: 1 }}
                                    >
                                        Submit Quiz
                                    </button>
                                ) : (
                                    <>
                                        <button
                                            className="btn btn-secondary btn-lg"
                                            onClick={handleReset}
                                            style={{ flex: 1 }}
                                        >
                                            <FaRedo />
                                            Reset Quiz
                                        </button>
                                        <div style={{ flex: 1, textAlign: 'center' }}>
                                            <div className="card" style={{ padding: 'var(--spacing-lg)', margin: 0 }}>
                                                <h3 className="text-mono" style={{ marginBottom: 'var(--spacing-sm)' }}>
                                                    Your Score
                                                </h3>
                                                <div style={{ fontSize: '2rem', fontWeight: 'bold', fontFamily: 'var(--font-mono)' }}>
                                                    {score.correct}/{score.total}
                                                </div>
                                                <div
                                                    className="text-mono"
                                                    style={{
                                                        color: score.percentage >= 80 ? 'var(--accent-success)' :
                                                            score.percentage >= 60 ? 'var(--accent-warning)' :
                                                                'var(--accent-error)',
                                                        fontSize: '1.25rem',
                                                        marginTop: 'var(--spacing-sm)'
                                                    }}
                                                >
                                                    {score.percentage.toFixed(1)}%
                                                </div>
                                                <div className="text-secondary" style={{ marginTop: 'var(--spacing-sm)' }}>
                                                    {score.percentage >= 80 ? '🎉 Excellent!' :
                                                        score.percentage >= 60 ? '👍 Good job!' :
                                                            '📚 Keep studying!'}
                                                </div>
                                            </div>
                                        </div>
                                    </>
                                )}
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}

export default QuizTab;
