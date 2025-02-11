import { useState, useRef, useEffect } from 'react';
import { Message } from '../types';

const ChatWindow = () => {
  // 初始化欢迎消息
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 'welcome',
      content: '您好！我是智能助手，请问有什么可以帮您？',
      role: 'assistant',
      timestamp: Date.now()
    }
  ]);

  const [inputText, setInputText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // 自动滚动到底部
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // 发送消息
  const handleSend = async () => {
    if (!inputText.trim() || isLoading) return;

    const newMessage: Message = {
      id: Date.now().toString(),
      content: inputText,
      role: 'user',
      timestamp: Date.now()
    };

    setMessages(prev => [...prev, newMessage]);
    setInputText('');

    try {
      setIsLoading(true);
      const response = await fetch('http://localhost:8000/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          messages: [{ role: 'user', content: inputText }]
        })
      });

      const data = await response.json();

      const assistantMessage: Message = {
        id: Date.now().toString(),
 content: data.content,
        role: 'assistant',
        timestamp: Date.now()
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      console.error('请求失败:', error);
    } finally {
      setIsLoading(false);
    }
  };

  // 处理文件上传
  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    try {
      setIsLoading(true);
      const response = await fetch('http://localhost:8000/api/analyze', {
        method: 'POST',
        body: formData
      });

      const result = await response.json();

      const fileMessage: Message = {
        id: Date.now().toString(),
        content: result.summary || '文件分析失败',
        role: 'assistant',
        timestamp: Date.now(),
        file: {
          name: file.name,
          summary: result.summary
        }
      };

      setMessages(prev => [...prev, fileMessage]);
    } catch (error) {
      console.error('上传失败:', error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="chat-container">
      <div className="messages">
        {messages.map((msg) => (
          <div key={msg.id} className={`message ${msg.role}`}>
            {msg.file && (
              <div className="file-meta">
                <span className="file-icon">📄</span>
                <span className="file-name">{msg.file.name}</span>
                {msg.file.summary && (
                  <div className="file-summary">{msg.file.summary}</div>
                )}
              </div>
            )}
            <div className="content">{msg.content}</div>
          </div>
        ))}

        {isLoading && (
          <div className="message assistant loading">
            <div className="typing-indicator">
              <div className="dot"></div>
              <div className="dot"></div>
              <div className="dot"></div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="input-area">
        <input
          type="file"
          ref={fileInputRef}
          onChange={handleFileUpload}
          accept=".pdf,.txt,.docx"
          hidden
        />
        <button
          className="icon-button"
          onClick={() => fileInputRef.current?.click()}
          disabled={isLoading}
        >
          📎
        </button>

        <input
          type="text"
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && handleSend()}
          placeholder="输入消息..."
          disabled={isLoading}
        />

        <button
          className="send-button"
          onClick={handleSend}
          disabled={isLoading || !inputText.trim()}
        >
          {isLoading ? '发送中...' : '发送'}
        </button>
      </div>
    </div>
  );
};

export default ChatWindow;