import React from 'react';

const MessageComponent = ({ message, formatTimestamp }) => {
  const renderContent = () => {
    switch (message.type) {
      case 'loading':
        return (
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <div className="loading-dots">
              <div className="loading-dot"></div>
              <div className="loading-dot"></div>
              <div className="loading-dot"></div>
            </div>
            <span>Processing your query...</span>
          </div>
        );
      
      case 'error':
        return (
          <div>
            <strong>❌ Error:</strong> {message.content}
          </div>
        );
      
      case 'user':
        return (
          <div>
            <div>{message.content}</div>
            <div style={{ fontSize: '12px', opacity: 0.8, marginTop: '4px' }}>
              {formatTimestamp(message.timestamp)}
            </div>
          </div>
        );
      
      case 'assistant':
        return (
          <div>
            <div style={{ whiteSpace: 'pre-wrap' }}>{message.content}</div>
            <div style={{ fontSize: '12px', opacity: 0.7, marginTop: '4px' }}>
              {formatTimestamp(message.timestamp)}
            </div>
          </div>
        );
      
      case 'system':
        return (
          <div>
            <div style={{ whiteSpace: 'pre-wrap' }}>{message.content}</div>
            <div style={{ fontSize: '12px', opacity: 0.7, marginTop: '4px' }}>
              {formatTimestamp(message.timestamp)}
            </div>
          </div>
        );
      
      case 'step':
        return (
          <div style={{ 
            backgroundColor: 'rgba(59, 130, 246, 0.1)', 
            border: '1px solid rgba(59, 130, 246, 0.3)',
            borderRadius: '8px',
            padding: '12px'
          }}>
            <div style={{ whiteSpace: 'pre-wrap', fontFamily: 'monospace', fontSize: '13px' }}>
              {message.content}
            </div>
            <div style={{ fontSize: '11px', opacity: 0.6, marginTop: '6px' }}>
              {formatTimestamp(message.timestamp)}
            </div>
          </div>
        );
      
      default:
        return <div>{message.content}</div>;
    }
  };

  return (
    <div className={`message ${message.type}`}>
      {renderContent()}
    </div>
  );
};

export default MessageComponent;
