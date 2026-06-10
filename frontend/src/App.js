import { useState } from 'react';
import axios from 'axios';
import { FileText, Search, Loader2, CheckCircle, XCircle, Download, RefreshCw, BookOpen, Sparkles } from 'lucide-react';
import './App.css';

const API_BASE = 'http://localhost:8000/api';
const DEFAULT_SECTIONS = ['摘要', '引言', '方法', '结果', '讨论'];
const FIELDS = ['计算机科学', '人工智能', '生物学', '物理学', '化学', '医学', '经济学', '心理学'];

function App() {
  const [topic, setTopic] = useState('');
  const [field, setField] = useState('计算机科学');
  const [selectedSections, setSelectedSections] = useState(DEFAULT_SECTIONS);
  const [maxTokens, setMaxTokens] = useState(3000);
  const [taskId, setTaskId] = useState(null);
  const [taskStatus, setTaskStatus] = useState(null);
  const [paperResult, setPaperResult] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [searchHistory, setSearchHistory] = useState([]);

  const handleSectionToggle = (section) => {
    setSelectedSections(prev =>
      prev.includes(section)
        ? prev.filter(s => s !== section)
        : [...prev, section]
    );
  };

  const handleSubmit = async () => {
    if (!topic.trim()) {
      setError('请输入论文主题');
      return;
    }
    if (selectedSections.length === 0) {
      setError('请至少选择一个章节');
      return;
    }

    setError('');
    setIsLoading(true);
    setPaperResult(null);

    try {
      const response = await axios.post(`${API_BASE}/generate-paper`, {
        topic,
        field,
        sections: selectedSections,
        max_tokens: maxTokens
      });
      
      setTaskId(response.data.task_id);
      setTaskStatus('pending');
      pollTaskStatus(response.data.task_id);
      
      setSearchHistory(prev => [{ topic, field, timestamp: Date.now() }, ...prev].slice(0, 10));
    } catch (err) {
      setError('提交失败，请稍后重试');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  const pollTaskStatus = async (taskId) => {
    const interval = setInterval(async () => {
      try {
        const response = await axios.get(`${API_BASE}/task-status/${taskId}`);
        const { status, result, error: taskError } = response.data;
        
        setTaskStatus(status);
        
        if (status === 'completed') {
          setPaperResult(result);
          clearInterval(interval);
        } else if (status === 'failed') {
          setError(taskError || '生成失败');
          clearInterval(interval);
        }
      } catch (err) {
        console.error('轮询失败:', err);
      }
    }, 2000);
  };

  const handleDownload = () => {
    if (!paperResult) return;
    
    let content = `# ${paperResult.topic}\n\n`;
    content += `**领域**: ${paperResult.field}\n\n`;
    
    Object.entries(paperResult.content).forEach(([section, text]) => {
      content += `## ${section}\n\n${text}\n\n`;
    });
    
    const blob = new Blob([content], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${paperResult.topic}.md`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleReset = () => {
    setTopic('');
    setField('计算机科学');
    setSelectedSections(DEFAULT_SECTIONS);
    setMaxTokens(3000);
    setTaskId(null);
    setTaskStatus(null);
    setPaperResult(null);
    setError('');
  };

  return (
    <div className="app-container">
      <header className="header">
        <div className="logo">
          <BookOpen className="logo-icon" />
          <h1>论文生成Agent</h1>
        </div>
        <p className="subtitle">基于RAG技术的领域论文智能生成系统</p>
      </header>

      <div className="main-content">
        <div className="left-panel">
          <div className="form-card">
            <h2 className="form-title">
              <Sparkles className="title-icon" />
              生成论文
            </h2>
            
            <div className="form-group">
              <label>论文主题</label>
              <input
                type="text"
                value={topic}
                onChange={(e) => setTopic(e.target.value)}
                placeholder="请输入论文主题，例如：深度学习在图像识别中的应用"
                className="input-field"
              />
            </div>

            <div className="form-group">
              <label>研究领域</label>
              <select
                value={field}
                onChange={(e) => setField(e.target.value)}
                className="select-field"
              >
                {FIELDS.map(f => (
                  <option key={f} value={f}>{f}</option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label>选择章节</label>
              <div className="section-grid">
                {DEFAULT_SECTIONS.map(section => (
                  <button
                    key={section}
                    onClick={() => handleSectionToggle(section)}
                    className={`section-tag ${selectedSections.includes(section) ? 'selected' : ''}`}
                  >
                    {section}
                  </button>
                ))}
              </div>
            </div>

            <div className="form-group">
              <label>最大Token数: {maxTokens}</label>
              <input
                type="range"
                min="1000"
                max="8000"
                step="500"
                value={maxTokens}
                onChange={(e) => setMaxTokens(parseInt(e.target.value))}
                className="range-field"
              />
            </div>

            {error && <div className="error-message">{error}</div>}

            <div className="button-group">
              <button onClick={handleSubmit} disabled={isLoading || taskStatus === 'pending'} className="submit-btn">
                {isLoading ? (
                  <>
                    <Loader2 className="btn-icon spin" />
                    提交中...
                  </>
                ) : taskStatus === 'pending' ? (
                  <>
                    <Loader2 className="btn-icon spin" />
                    生成中...
                  </>
                ) : (
                  <>
                    <Search className="btn-icon" />
                    生成论文
                  </>
                )}
              </button>
              
              <button onClick={handleReset} className="reset-btn">
                重置
              </button>
            </div>
          </div>

          {searchHistory.length > 0 && (
            <div className="history-card">
              <h3>最近生成</h3>
              <div className="history-list">
                {searchHistory.map((item, idx) => (
                  <div key={idx} className="history-item">
                    <span className="history-topic">{item.topic}</span>
                    <span className="history-field">{item.field}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        <div className="right-panel">
          <div className="result-card">
            <div className="result-header">
              <h2 className="result-title">
                <FileText className="title-icon" />
                生成结果
              </h2>
              {paperResult && (
                <button onClick={handleDownload} className="download-btn">
                  <Download className="btn-icon" />
                  下载
                </button>
              )}
            </div>

            {!taskId && !paperResult && (
              <div className="empty-state">
                <BookOpen className="empty-icon" />
                <p>输入主题并点击生成按钮开始</p>
                <p className="empty-hint">系统将基于RAG检索相关文献并生成论文</p>
              </div>
            )}

            {taskStatus && !paperResult && (
              <div className="status-container">
                <div className={`status-card ${taskStatus}`}>
                  <div className="status-icon">
                    {taskStatus === 'pending' && <Loader2 className="spin" />}
                    {taskStatus === 'PROGRESS' && <RefreshCw className="spin" />}
                    {taskStatus === 'failed' && <XCircle />}
                  </div>
                  <div className="status-info">
                    <p className="status-text">
                      {taskStatus === 'pending' && '等待处理...'}
                      {taskStatus === 'PROGRESS' && '正在生成论文...'}
                      {taskStatus === 'failed' && '生成失败'}
                    </p>
                    {taskStatus === 'PROGRESS' && (
                      <div className="progress-bar">
                        <div className="progress-fill" style={{ width: '60%' }}></div>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}

            {paperResult && (
              <div className="paper-content">
                <h3 className="paper-title">{paperResult.topic}</h3>
                <p className="paper-field">领域：{paperResult.field}</p>
                
                {Object.entries(paperResult.content).map(([section, text]) => (
                  <div key={section} className="paper-section">
                    <h4 className="section-header">{section}</h4>
                    <div className="section-content">
                      {text.split('\n').map((paragraph, idx) => (
                        paragraph.trim() && <p key={idx}>{paragraph}</p>
                      ))}
                    </div>
                  </div>
                ))}

                {paperResult.context_used && (
                  <div className="context-badge">
                    <CheckCircle className="badge-icon" />
                    已基于知识库内容生成
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;