import { useState, useRef, useEffect } from 'react';
import {
  Send, User, Bot, Briefcase, FileText, Users, BookOpen,
  Sparkles, RotateCcw, Copy, Check, ChevronRight, Zap,
  History, BarChart2, MessageSquare, Clock, TrendingUp,
  Search, Trash2, LayoutDashboard
} from 'lucide-react';
import { marked } from 'marked';
import './index.css';

const AGENTS = [
  {
    id: 'finance',
    name: 'Finance Agent',
    dept: 'Finance',
    desc: 'Invoices, budgets & expenses',
    icon: Briefcase,
    colorClass: 'finance-icon',
    examples: [
      'Check status of invoice #INV-2024-001',
      'What is our Q3 marketing budget?'
    ]
  },
  {
    id: 'sales',
    name: 'Sales Agent',
    dept: 'Sales & CRM',
    desc: 'Deals, quotes & pipelines',
    icon: FileText,
    colorClass: 'sales-icon',
    examples: [
      'Is the Acme deal still open?',
      'Draft a quote for Acme Corp'
    ]
  },
  {
    id: 'hr',
    name: 'HR Agent',
    dept: 'People & Culture',
    desc: 'Time-off balances & policies',
    icon: Users,
    colorClass: 'hr-icon',
    examples: [
      'What is my PTO balance for this year?',
      'How do I submit an expense reimbursement?'
    ]
  },
  {
    id: 'knowledge',
    name: 'Knowledge Agent',
    dept: 'Enterprise Wiki',
    desc: 'RAG over indexed company docs',
    icon: BookOpen,
    colorClass: 'knowledge-icon',
    examples: [
      'What is the company remote work policy?',
      'Where can I find the security guidelines?'
    ]
  }
];

const SUGGESTIONS = [
  { text: "Check status of invoice #INV-2024-001", agent: "Finance" },
  { text: "What is my current PTO balance?", agent: "HR" },
  { text: "Draft a quote for Acme Corp", agent: "Sales" },
  { text: "What is our company travel policy?", agent: "Knowledge" }
];

const AGENT_COLORS = { Finance: '#10b981', Sales: '#f59e0b', HR: '#ec4899', Knowledge: '#3b82f6' };
const AGENT_BAR_COLORS = { finance: '#10b981', sales: '#f59e0b', hr: '#ec4899', knowledge: '#3b82f6' };

function detectAgent(text) {
  const t = text.toLowerCase();
  if (t.includes('invoice') || t.includes('budget') || t.includes('finance') || t.includes('expense')) return 'Finance';
  if (t.includes('deal') || t.includes('quote') || t.includes('sales') || t.includes('acme') || t.includes('pipeline')) return 'Sales';
  if (t.includes('pto') || t.includes('time-off') || t.includes('hr') || t.includes('leave') || t.includes('reimbursement')) return 'HR';
  return 'Knowledge';
}

function App() {
  const [view, setView] = useState('chat');
  const [messages, setMessages] = useState([
    {
      id: 'welcome',
      role: 'assistant',
      content: "👋 **Hello! I'm your Enterprise Multi-Agent Assistant.**\n\nI can coordinate across **Finance, Sales, HR, and Knowledge Base** agents to answer questions or automate business workflows in real-time. Pick an example below or ask anything!",
      time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    }
  ]);
  const [searchHistory, setSearchHistory] = useState([]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [selectedAgent, setSelectedAgent] = useState(null);
  const [copiedId, setCopiedId] = useState(null);
  const [sessionId] = useState(() => 'session-' + Math.random().toString(36).substr(2, 9));
  const [historyFilter, setHistoryFilter] = useState('');
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping]);

  const sendMessage = async (textToSend) => {
    const query = textToSend || input;
    if (!query.trim()) return;

    const currentTime = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    const detectedAgent = detectAgent(query);

    const userMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: query.trim(),
      time: currentTime
    };

    setSearchHistory(prev => [{
      id: Date.now().toString(),
      query: query.trim(),
      agent: detectedAgent,
      time: currentTime,
      date: new Date().toLocaleDateString([], { month: 'short', day: 'numeric' })
    }, ...prev].slice(0, 50));

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsTyping(true);

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sessionId, message: userMessage.content })
      });
      const data = await response.json();
      setMessages(prev => [...prev, {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: data.response || 'No response received.',
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      }]);
    } catch {
      setMessages(prev => [...prev, {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: '⚠️ **Connection Error**: Unable to reach backend server. Please make sure the backend is running.',
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      }]);
    } finally {
      setIsTyping(false);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    sendMessage(input);
  };

  const handleResetSession = () => {
    setMessages([{
      id: Date.now().toString(),
      role: 'assistant',
      content: "🔄 **Session reset.** How can the specialist agents help you now?",
      time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    }]);
  };

  const handleCopy = (id, text) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const createMarkup = (text) => ({ __html: marked.parse(text || '') });

  const totalQueries = searchHistory.length;
  const filteredHistory = searchHistory.filter(h =>
    h.query.toLowerCase().includes(historyFilter.toLowerCase())
  );

  return (
    <div className="app-container">
      {/* Sidebar */}
      <aside className="sidebar">
        <div className="sidebar-header">
          <div className="logo-badge">
            <Sparkles size={14} className="sparkle-icon" />
            <span>Multi-Agent AI</span>
          </div>
          <h2>Business Hub</h2>
          <p>Orchestrated Multi-Agent System</p>
        </div>

        {/* Nav Tabs */}
        <div className="sidebar-nav">
          <button className={`nav-tab ${view === 'chat' ? 'active' : ''}`} onClick={() => setView('chat')}>
            <MessageSquare size={14} /><span>Chat</span>
          </button>
          <button className={`nav-tab ${view === 'dashboard' ? 'active' : ''}`} onClick={() => setView('dashboard')}>
            <LayoutDashboard size={14} /><span>Dashboard</span>
          </button>
        </div>

        {/* Agents */}
        <div className="agent-list">
          <div className="section-label">
            <span>Specialist Agents</span>
            <span className="count-badge">4 Online</span>
          </div>
          {AGENTS.map((agent) => {
            const Icon = agent.icon;
            const isSelected = selectedAgent?.id === agent.id;
            return (
              <div
                key={agent.id}
                className={`agent-item ${isSelected ? 'active-agent' : ''}`}
                onClick={() => setSelectedAgent(isSelected ? null : agent)}
              >
                <div className={`agent-icon ${agent.colorClass}`}><Icon size={17} /></div>
                <div className="agent-info">
                  <div className="agent-title-row">
                    <h4>{agent.name}</h4>
                    <span className="status-dot"></span>
                  </div>
                  <p>{agent.desc}</p>
                </div>
                <ChevronRight size={13} className="agent-chevron" />
              </div>
            );
          })}
        </div>

        {selectedAgent && (
          <div className="agent-details-drawer">
            <div className="drawer-header">
              <span className="drawer-badge">{selectedAgent.dept}</span>
              <button className="drawer-close" onClick={() => setSelectedAgent(null)}>×</button>
            </div>
            <h5>Try asking {selectedAgent.name}:</h5>
            <div className="drawer-examples">
              {selectedAgent.examples.map((ex, idx) => (
                <button key={idx} className="example-pill" onClick={() => {
                  setInput(ex); setView('chat');
                  setTimeout(() => inputRef.current?.focus(), 100);
                }}>
                  <Zap size={11} /><span>{ex}</span>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* History Panel */}
        <div className="history-section">
          <div className="section-label">
            <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
              <History size={11} />History
            </span>
            {searchHistory.length > 0 && (
              <button className="clear-history-btn" onClick={() => setSearchHistory([])} title="Clear all">
                <Trash2 size={11} />
              </button>
            )}
          </div>
          <div className="history-search">
            <Search size={11} />
            <input
              className="history-search-input"
              placeholder="Filter..."
              value={historyFilter}
              onChange={(e) => setHistoryFilter(e.target.value)}
            />
          </div>
          <div className="history-list">
            {filteredHistory.length === 0 ? (
              <div className="history-empty">No searches yet</div>
            ) : (
              filteredHistory.map(h => (
                <div key={h.id} className="history-item" onClick={() => {
                  setInput(h.query); setView('chat');
                  setTimeout(() => inputRef.current?.focus(), 100);
                }}>
                  <div className="history-item-agent" style={{ background: AGENT_COLORS[h.agent] + '22', color: AGENT_COLORS[h.agent] }}>
                    {h.agent.charAt(0)}
                  </div>
                  <div className="history-item-content">
                    <span className="history-query">{h.query}</span>
                    <span className="history-time"><Clock size={9} /> {h.time}</span>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        <div className="sidebar-footer">
          <div className="platform-tag">
            <span className="pulse-circle"></span>
            <span>Azure AI Foundry + FastAPI</span>
          </div>
        </div>
      </aside>

      {/* Main Area */}
      <main className="main-area">
        {view === 'chat' ? (
          <div className="chat-container">
            <header className="chat-header">
              <div className="header-info">
                <div className="header-avatar"><Sparkles size={18} /></div>
                <div>
                  <div className="title-row">
                    <h1>Orchestrator Agent</h1>
                    <span className="badge-orchestrator">Active Router</span>
                  </div>
                  <p className="subtitle">Routes queries to Finance, Sales, HR & Knowledge RAG</p>
                </div>
              </div>
              <div className="header-actions">
                <span className="session-info">{totalQueries} queries</span>
                <button className="action-btn" title="Reset session" onClick={handleResetSession}>
                  <RotateCcw size={13} /><span>Reset</span>
                </button>
              </div>
            </header>

            <div className="chat-messages">
              {messages.map((msg) => {
                const isAssistant = msg.role === 'assistant';
                return (
                  <div key={msg.id} className={`message ${msg.role}`}>
                    <div className="message-avatar">
                      {isAssistant ? <Bot size={15} /> : <User size={15} />}
                    </div>
                    <div className="message-wrapper">
                      <div className="message-header-meta">
                        <span className="sender-name">{isAssistant ? 'Enterprise Assistant' : 'You'}</span>
                        <span className="message-time">{msg.time}</span>
                      </div>
                      <div
                        className="message-content"
                        dangerouslySetInnerHTML={isAssistant ? createMarkup(msg.content) : undefined}
                      >
                        {!isAssistant ? msg.content : null}
                      </div>
                      {isAssistant && (
                        <div className="message-actions">
                          <button className="copy-btn" onClick={() => handleCopy(msg.id, msg.content)}>
                            {copiedId === msg.id
                              ? <><Check size={11} className="text-success" /><span>Copied!</span></>
                              : <><Copy size={11} /><span>Copy</span></>}
                          </button>
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
              {isTyping && (
                <div className="message assistant typing-container">
                  <div className="message-avatar"><Bot size={15} /></div>
                  <div className="message-wrapper">
                    <div className="message-header-meta">
                      <span className="sender-name">Enterprise Assistant</span>
                      <span className="thinking-text">Orchestrating agents...</span>
                    </div>
                    <div className="message-content typing-box">
                      <div className="typing-indicator">
                        <div className="dot"></div><div className="dot"></div><div className="dot"></div>
                      </div>
                    </div>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>

            <div className="quick-suggestions-bar">
              <span className="quick-label">Suggestions:</span>
              <div className="suggestions-scroll">
                {SUGGESTIONS.map((item, index) => (
                  <button key={index} className="suggestion-chip" onClick={() => sendMessage(item.text)} disabled={isTyping}>
                    <span className="chip-agent">{item.agent}</span>
                    <span className="chip-text">{item.text}</span>
                  </button>
                ))}
              </div>
            </div>

            <div className="chat-input-area">
              <form className="chat-form" onSubmit={handleSubmit}>
                <input
                  ref={inputRef}
                  type="text"
                  className="chat-input"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  placeholder="Ask about invoices, deals, PTO policies, or company docs..."
                  autoComplete="off"
                />
                {input && (
                  <button type="button" className="clear-input-btn" onClick={() => setInput('')}>×</button>
                )}
                <button type="submit" className="send-button" disabled={!input.trim() || isTyping}>
                  <Send size={16} strokeWidth={2.2} />
                </button>
              </form>
              <div className="input-hint">
                <span>Multi-agent orchestrator automatically delegates to the appropriate specialist</span>
              </div>
            </div>
          </div>
        ) : (
          /* Dashboard View */
          <div className="chat-container">
            <header className="chat-header">
              <div className="header-info">
                <div className="header-avatar"><BarChart2 size={18} /></div>
                <div>
                  <div className="title-row">
                    <h1>Analytics Dashboard</h1>
                    <span className="badge-orchestrator">Live</span>
                  </div>
                  <p className="subtitle">Session activity and agent usage breakdown</p>
                </div>
              </div>
            </header>

            <div className="dashboard-scroll">
              {/* KPI Cards */}
              <div className="kpi-grid">
                <div className="kpi-card">
                  <div className="kpi-icon kpi-blue"><MessageSquare size={20} /></div>
                  <div className="kpi-info">
                    <div className="kpi-value">{totalQueries}</div>
                    <div className="kpi-label">Total Queries</div>
                  </div>
                </div>
                <div className="kpi-card">
                  <div className="kpi-icon kpi-purple"><TrendingUp size={20} /></div>
                  <div className="kpi-info">
                    <div className="kpi-value">{messages.filter(m => m.role === 'assistant').length}</div>
                    <div className="kpi-label">Responses</div>
                  </div>
                </div>
                <div className="kpi-card">
                  <div className="kpi-icon kpi-green"><Sparkles size={20} /></div>
                  <div className="kpi-info">
                    <div className="kpi-value">4</div>
                    <div className="kpi-label">Active Agents</div>
                  </div>
                </div>
                <div className="kpi-card">
                  <div className="kpi-icon kpi-orange"><Clock size={20} /></div>
                  <div className="kpi-info">
                    <div className="kpi-value">{searchHistory[0]?.time || '—'}</div>
                    <div className="kpi-label">Last Activity</div>
                  </div>
                </div>
              </div>

              {/* Agent Usage Bars */}
              <div className="dashboard-section">
                <div className="dash-section-title"><BarChart2 size={15} /><span>Agent Usage</span></div>
                <div className="agent-bars">
                  {AGENTS.map(agent => {
                    const count = searchHistory.filter(h => h.agent === agent.id.charAt(0).toUpperCase() + agent.id.slice(1)).length;
                    const pct = totalQueries > 0 ? (count / totalQueries) * 100 : 0;
                    const Icon = agent.icon;
                    return (
                      <div key={agent.id} className="agent-bar-row">
                        <div className="agent-bar-label">
                          <div className={`agent-icon-sm ${agent.colorClass}`}><Icon size={13} /></div>
                          <span>{agent.name}</span>
                        </div>
                        <div className="agent-bar-track">
                          <div className="agent-bar-fill" style={{ width: `${pct}%`, background: AGENT_BAR_COLORS[agent.id] }}></div>
                        </div>
                        <span className="agent-bar-count">{count}</span>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Full History Table */}
              <div className="dashboard-section">
                <div className="dash-section-title">
                  <History size={15} /><span>Search History</span>
                  {searchHistory.length > 0 && (
                    <button className="clear-all-btn" onClick={() => setSearchHistory([])}>
                      <Trash2 size={12} /> Clear All
                    </button>
                  )}
                </div>
                <div className="history-search dash-search">
                  <Search size={13} />
                  <input
                    className="history-search-input"
                    placeholder="Filter history..."
                    value={historyFilter}
                    onChange={(e) => setHistoryFilter(e.target.value)}
                  />
                </div>
                {filteredHistory.length === 0 ? (
                  <div className="dash-empty">
                    <MessageSquare size={30} />
                    <p>No search history yet. Start chatting!</p>
                    <button className="go-chat-btn" onClick={() => setView('chat')}>Go to Chat</button>
                  </div>
                ) : (
                  <div className="dash-history-list">
                    {filteredHistory.map((h, i) => (
                      <div key={h.id} className="dash-history-row">
                        <span className="dash-row-num">#{i + 1}</span>
                        <div className="dash-history-agent" style={{ background: AGENT_COLORS[h.agent] + '22', color: AGENT_COLORS[h.agent] }}>
                          {h.agent}
                        </div>
                        <span className="dash-query">{h.query}</span>
                        <span className="dash-time"><Clock size={10} /> {h.date} {h.time}</span>
                        <button className="dash-replay-btn" title="Re-send" onClick={() => {
                          setInput(h.query); setView('chat');
                          setTimeout(() => inputRef.current?.focus(), 100);
                        }}>
                          <Send size={11} />
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
