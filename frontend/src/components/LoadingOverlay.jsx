function LoadingOverlay({ message }) {
    return (
        <div className="loading-overlay">
            <div className="loading-content">
                <div className="loading-spinner"></div>
                <p className="loading-text">{message || 'Processing...'}</p>
            </div>
        </div>
    );
}

export default LoadingOverlay;
