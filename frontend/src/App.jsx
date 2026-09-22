import { useState, useRef, useEffect } from 'react';
import { 
  Send, User, Bot, Briefcase, FileText, Users, BookOpen, 
  Sparkles, RotateCcw, Copy, Check, ChevronRight, Zap
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
    gradient: 'from-emerald-500 to-teal-700',
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
    gradient: 'from-amber-500 to-orange-600',
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
    gradient: 'from-pink-500 to-rose-600',
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
    gradient: 'from-blue-500 to-indigo-600',
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

function App() {
  const [messages, setMessages] = useState([
    {
      id: 'welcome',
      role: 'assistant',
      content: "👋 **Hello! I'm your Enterprise Multi-Agent Assistant.**\n\nI can coordinate across **Finance, Sales, HR, and Knowledge Base** agents to answer questions or automate business workflows in real-time. Pick an example below or ask anything!",
      time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    }
  ]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [selectedAgent, setSelectedAgent] = useState(null);
  const [copiedId, setCopiedId] = useState(null);
  const [sessionId, setSessionId] = useState(() => 'session-' + Math.random().toString(36).substr(2, 9));
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

    const userMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: query.trim(),
      time: currentTime
    };
    
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsTyping(true);

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          session_id: sessionId,
          message: userMessage.content
        })
      });

      const data = await response.json();
      
      const assistantMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: data.response || "No response received.",
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };
      
      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
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
    setSessionId('session-' + Math.random().toString(36).substr(2, 9));
    setMessages([
      {
        id: Date.now().toString(),
        role: 'assistant',
        content: "🔄 **Session reset.** How can the specialist agents help you now?",
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      }
    ]);
  };

  const handleCopy = (id, text) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const createMarkup = (text) => {
    return { __html: marked.parse(text || '') };
  };

  return (
    <div className="app-container">
      {/* Dynamic Background Glow Elements */}
      <div className="ambient-glow glow-1"></div>
      <div className="ambient-glow glow-2"></div>

      {/* Sidebar */}
      <aside className="sidebar">
        <div className="sidebar-header">
          <div className="logo-badge">
            <Sparkles size={20} className="sparkle-icon" />
            <span>Multi-Agent AI</span>
          </div>
          <h2>Business Hub</h2>
          <p>Orchestrated Multi-Agent System</p>
        </div>
        
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
                onClick={() => {
                  setSelectedAgent(isSelected ? null : agent);
                }}
              >
                <div className={`agent-icon ${agent.colorClass}`}>
                  <Icon size={20} />
                </div>
                <div className="agent-info">
                  <div className="agent-title-row">
                    <h4>{agent.name}</h4>
                    <span className="status-dot"></span>
                  </div>
                  <p>{agent.desc}</p>
                </div>
                <ChevronRight size={16} className="agent-chevron" />
              </div>
            );
          })}
        </div>

        {/* Dynamic Details Panel when an Agent is clicked */}
        {selectedAgent && (
          <div className="agent-details-drawer">
            <div className="drawer-header">
              <span className="drawer-badge">{selectedAgent.dept}</span>
              <button className="drawer-close" onClick={() => setSelectedAgent(null)}>×</button>
            </div>
            <h5>Try asking {selectedAgent.name}:</h5>
            <div className="drawer-examples">
              {selectedAgent.examples.map((ex, idx) => (
                <button 
                  key={idx} 
                  className="example-pill"
                  onClick={() => {
                    setInput(ex);
                    inputRef.current?.focus();
                  }}
                >
                  <Zap size={12} />
                  <span>{ex}</span>
                </button>
              ))}
            </div>
          </div>
        )}
        
        <div className="sidebar-footer">
          <div className="platform-tag">
            <span className="pulse-circle"></span>
            <span>Azure AI Foundry + FastAPI</span>
          </div>
        </div>
      </aside>

      {/* Main Chat Area */}
      <main className="chat-container">
        <header className="chat-header">
          <div className="header-info">
            <div className="header-avatar">
              <Sparkles size={20} />
            </div>
            <div>
              <div className="title-row">
                <h1>Orchestrator Agent</h1>
                <span className="badge-orchestrator">Active Router</span>
              </div>
              <p className="subtitle">Routes queries dynamically to Finance, Sales, HR & Knowledge RAG</p>
            </div>
          </div>

          <div className="header-actions">
            <button 
              className="action-btn" 
              title="Reset conversation session"
              onClick={handleResetSession}
            >
              <RotateCcw size={16} />
              <span>Reset Session</span>
            </button>
          </div>
        </header>

        {/* Message Stream */}
        <div className="chat-messages">
          {messages.map((msg) => {
            const isAssistant = msg.role === 'assistant';
            return (
              <div key={msg.id} className={`message ${msg.role}`}>
                <div className="message-avatar">
                  {isAssistant ? <Bot size={18} /> : <User size={18} />}
                </div>
                <div className="message-wrapper">
                  <div className="message-header-meta">
                    <span className="sender-name">{isAssistant ? 'Enterprise Assistant' : 'You'}</span>
                    <span className="message-time">{msg.time}</span>
                  </div>
                  <div 
                    className="message-content" 
                    dangerouslySetInnerHTML={
                      isAssistant 
                        ? createMarkup(msg.content) 
                        : undefined
                    }
                  >
                    {!isAssistant ? msg.content : null}
                  </div>
                  {isAssistant && (
                    <div className="message-actions">
                      <button 
                        className="copy-btn"
                        onClick={() => handleCopy(msg.id, msg.content)}
                        title="Copy text"
                      >
                        {copiedId === msg.id ? (
                          <>
                            <Check size={13} className="text-success" />
                            <span>Copied!</span>
                          </>
                        ) : (
                          <>
                            <Copy size={13} />
                            <span>Copy</span>
                          </>
                        )}
                      </button>
                    </div>
                  )}
                </div>
              </div>
            );
          })}
          
          {isTyping && (
            <div className="message assistant typing-container">
              <div className="message-avatar">
                <Bot size={18} />
              </div>
              <div className="message-wrapper">
                <div className="message-header-meta">
                  <span className="sender-name">Enterprise Assistant</span>
                  <span className="thinking-text">Orchestrating agents...</span>
                </div>
                <div className="message-content typing-box">
                  <div className="typing-indicator">
                    <div className="dot"></div>
                    <div className="dot"></div>
                    <div className="dot"></div>
                  </div>
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Interactive Quick Starters */}
        <div className="quick-suggestions-bar">
          <span className="quick-label">Suggestions:</span>
          <div className="suggestions-scroll">
            {SUGGESTIONS.map((item, index) => (
              <button
                key={index}
                className="suggestion-chip"
                onClick={() => sendMessage(item.text)}
                disabled={isTyping}
              >
                <span className="chip-agent">{item.agent}</span>
                <span className="chip-text">{item.text}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Input Dock */}
        <div className="chat-input-area">
          <form className="chat-form" onSubmit={handleSubmit}>
            <input 
              ref={inputRef}
              type="text" 
              className="chat-input"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask anything about invoices, deals, PTO policies, or company docs..." 
              autoComplete="off" 
            />
            {input && (
              <button 
                type="button" 
                className="clear-input-btn"
                onClick={() => setInput('')}
              >
                ×
              </button>
            )}
            <button 
              type="submit" 
              className="send-button" 
              disabled={!input.trim() || isTyping}
              title="Send message"
            >
              <Send size={18} strokeWidth={2.2} />
            </button>
          </form>
          <div className="input-hint">
            <span>Tip: Multi-agent orchestrator automatically delegates to the appropriate specialist</span>
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;
