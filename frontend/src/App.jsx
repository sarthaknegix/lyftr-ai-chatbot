
import { useState, useRef, useEffect } from "react";
import {
  Bot,
  Plus,
  Send,
  Sparkles,
  User,
  Zap,
  Clock3,
  Coins,
  Database,
  Menu,
  X,
  Settings2,
  MessageSquare,
  RotateCcw,
} from "lucide-react";

import "./App.css";

const API_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

function App() {
  const [sessionId, setSessionId] = useState(() =>
    crypto.randomUUID()
  );

  const [messages, setMessages] = useState([]);
  const [sessions, setSessions] = useState([]);
  const [input, setInput] = useState("");
  const [systemPrompt, setSystemPrompt] = useState("");
  const [showSettings, setShowSettings] = useState(false);

  const [responseStyle, setResponseStyle] = useState("normal");
  const [showMetadata, setShowMetadata] = useState(true);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const messagesEndRef = useRef(null);

  // Scroll to the latest message
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({
      behavior: "smooth",
    });
  }, [messages, loading]);

  // Load saved conversations when the application opens
  const loadSessions = async () => {
    try {
      const response = await fetch(`${API_URL}/sessions`);

      if (!response.ok) return;

      const data = await response.json();
      setSessions(data.sessions || []);
    } catch (error) {
      console.error("Could not load conversations:", error);
    }
  };

  useEffect(() => {
    loadSessions();
  }, []);

  // Start a new conversation
  const startNewChat = () => {
    setSessionId(crypto.randomUUID());
    setMessages([]);
    setInput("");
    setError("");
    setSidebarOpen(false);
  };

  // Open an existing conversation from history
  const openSavedChat = async (id) => {
    setLoading(true);
    setError("");

    try {
      const response = await fetch(
        `${API_URL}/sessions/${encodeURIComponent(id)}/messages`
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail || "Could not open conversation"
        );
      }

      const restoredMessages = (data.messages || []).map(
        (message, index) => ({
          id: `${id}-${index}`,
          role: message.role,
          content: message.content,
          metadata: message.metadata,
        })
      );

      setSessionId(id);
      setMessages(restoredMessages);
      setSidebarOpen(false);
    } catch (error) {
      setError(error.message);
    } finally {
      setLoading(false);
    }
  };

  // Send a message to the backend
  const sendMessage = async (event) => {
    event?.preventDefault();

    const trimmedInput = input.trim();

    if (!trimmedInput || loading) return;

    const userMessage = {
      id: crypto.randomUUID(),
      role: "user",
      content: trimmedInput,
    };

    setMessages((previous) => [...previous, userMessage]);
    setInput("");
    setError("");
    setLoading(true);

    try {
      const requestBody = {
        session_id: sessionId,
        message: trimmedInput,
      };

      const styleInstructions = {
  normal: "Respond naturally and helpfully.",
  professional: "Respond in a professional and formal tone.",
  friendly: "Respond in a friendly, warm and conversational tone.",
  concise: "Give short, direct and clear answers.",
  detailed: "Give detailed explanations with examples when useful.",
};

const combinedPrompt = [
  systemPrompt.trim(),
  styleInstructions[responseStyle],
]
  .filter(Boolean)
  .join("\n\n");

requestBody.system_prompt = combinedPrompt;

      const response = await fetch(`${API_URL}/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(requestBody),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail || "Something went wrong"
        );
      }

      const assistantMessage = {
        id: crypto.randomUUID(),
        role: "assistant",
        content: data.reply,
        metadata: data.metadata,
      };

      setMessages((previous) => [
        ...previous,
        assistantMessage,
      ]);

      // Refresh sidebar history after a successful response
      await loadSessions();
    } catch (error) {
      setError(error.message);
    } finally {
      setLoading(false);
    }
  };

  // Handle Enter key
  const handleKeyDown = (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="app-container">

      {/* Mobile sidebar overlay */}
      {sidebarOpen && (
        <div
          className="mobile-overlay"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={`sidebar ${
          sidebarOpen ? "sidebar-open" : ""
        }`}
      >
        <div className="sidebar-header">
          <div className="brand">
            <div className="brand-icon">
              <Sparkles size={20} />
            </div>

            <div className="brand-text">
              <h2>Lyftr AI</h2>
              <span>Intelligent Assistant</span>
            </div>
          </div>

          <button
            className="icon-button mobile-close"
            onClick={() => setSidebarOpen(false)}
            aria-label="Close sidebar"
          >
            <X size={19} />
          </button>
        </div>

        <button
          className="new-chat-button"
          onClick={startNewChat}
        >
          <Plus size={18} />
          <span>New Chat</span>
        </button>

        {/* Chat History */}
        <div className="sidebar-section recent-section">
          <div className="sidebar-label">
            CHAT HISTORY
          </div>

          {sessions.length > 0 ? (
            <div className="history-list">
              {sessions.map((session) => (
                <button
                  key={session.session_id}
                  className={`history-item ${
                    session.session_id === sessionId
                      ? "selected"
                      : ""
                  }`}
                  onClick={() =>
                    openSavedChat(session.session_id)
                  }
                >
                  <MessageSquare size={15} />

                  <span>
                    {session.title || "New conversation"}
                  </span>
                </button>
              ))}
            </div>
          ) : (
            <div className="empty-history">
              Your conversations will appear here.
            </div>
          )}
        </div>

        <div className="sidebar-bottom">
          <div className="sidebar-status">
            <span className="status-dot"></span>
            <span>AI Service Connected</span>
          </div>

          <div className="sidebar-footer">
            <Sparkles size={14} />
            <span>Powered by Lyftr AI</span>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="main-content">

        {/* Top Navigation */}
        <header className="topbar">
          <div className="topbar-left">
            <button
              className="icon-button menu-button"
              onClick={() => setSidebarOpen(true)}
              aria-label="Open sidebar"
            >
              <Menu size={21} />
            </button>

            <div className="topbar-title">
              <span className="online-indicator"></span>
              <span>AI Assistant</span>
            </div>
          </div>

          <div className="topbar-right">
            <button
              className={`settings-button ${
                showSettings ? "active" : ""
              }`}
              onClick={() =>
                setShowSettings(!showSettings)
              }
            >
              <Settings2 size={17} />
              <span>Settings</span>
            </button>
          </div>
        </header>

        
{/* Advanced Settings Panel */}
{showSettings && (
  <div className="settings-panel">

    <div className="settings-heading">
      <Settings2 size={19} />
      <span>Chat Settings</span>
    </div>

    <div className="settings-group">
      <label htmlFor="response-style">
        Response Style
      </label>

      <select
        id="response-style"
        value={responseStyle}
        onChange={(event) =>
          setResponseStyle(event.target.value)
        }
      >
        <option value="normal">Normal</option>
        <option value="professional">Professional</option>
        <option value="friendly">Friendly</option>
        <option value="concise">Concise</option>
        <option value="detailed">Detailed</option>
      </select>

      <p>Choose how Lyftr AI should respond.</p>
    </div>

    <div className="settings-group">
      <label htmlFor="system-prompt-input">
        Custom System Prompt
      </label>

      <textarea
        id="system-prompt-input"
        value={systemPrompt}
        onChange={(event) =>
          setSystemPrompt(event.target.value)
        }
        placeholder="Example: You are an expert Python tutor..."
        rows={4}
      />

      <p>Customize the assistant's behaviour.</p>
    </div>

    <div className="settings-toggle">
      <div>
        <strong>Show Response Metadata</strong>
        <p>Display model, latency and token usage.</p>
      </div>

      <input
        type="checkbox"
        checked={showMetadata}
        onChange={(event) =>
          setShowMetadata(event.target.checked)
        }
      />
    </div>

    <div className="settings-actions">
      <button
        type="button"
        className="reset-settings-button"
        onClick={() => {
          setSystemPrompt("");
          setResponseStyle("normal");
          setShowMetadata(true);
        }}
      >
        <RotateCcw size={14} />
        Reset Defaults
      </button>

      <button
        type="button"
        className="save-settings-button"
        onClick={() => setShowSettings(false)}
      >
        Done
      </button>
    </div>

  </div>
)}


        {/* Chat Area */}
        <section className="chat-area">

          {messages.length === 0 ? (
            <div className="welcome-screen">
              <div className="welcome-icon">
                <Bot size={34} />
                <div className="welcome-sparkle">
                  <Sparkles size={17} />
                </div>
              </div>

              <h1>
                How can I help you <span>today?</span>
              </h1>

              <p className="welcome-description">
                Your intelligent AI assistant is ready.
                Ask questions, explore ideas, or get help
                with your work.
              </p>

              <div className="suggestion-grid">
                <button
                  className="suggestion-card"
                  onClick={() =>
                    setInput(
                      "Explain artificial intelligence in simple words."
                    )
                  }
                >
                  <div className="suggestion-icon purple">
                    <Sparkles size={19} />
                  </div>

                  <div>
                    <strong>Learn something</strong>
                    <span>
                      Explain a complex topic simply
                    </span>
                  </div>
                </button>

                <button
                  className="suggestion-card"
                  onClick={() =>
                    setInput(
                      "Help me write clean and understandable Python code."
                    )
                  }
                >
                  <div className="suggestion-icon blue">
                    <Zap size={19} />
                  </div>

                  <div>
                    <strong>Write code</strong>
                    <span>
                      Get help with programming
                    </span>
                  </div>
                </button>

                <button
                  className="suggestion-card"
                  onClick={() =>
                    setInput(
                      "Give me some creative project ideas."
                    )
                  }
                >
                  <div className="suggestion-icon orange">
                    <Coins size={19} />
                  </div>

                  <div>
                    <strong>Explore ideas</strong>
                    <span>
                      Discover new possibilities
                    </span>
                  </div>
                </button>

                <button
                  className="suggestion-card"
                  onClick={() =>
                    setInput(
                      "Help me prepare for a technical interview."
                    )
                  }
                >
                  <div className="suggestion-icon green">
                    <MessageSquare size={19} />
                  </div>

                  <div>
                    <strong>Prepare for interviews</strong>
                    <span>
                      Practice technical concepts
                    </span>
                  </div>
                </button>
              </div>
            </div>
          ) : (
            <div className="messages-container">
              {messages.map((message) => (
                <div
                  key={message.id}
                  className={`message-row ${
                    message.role === "user"
                      ? "user-row"
                      : "assistant-row"
                  }`}
                >
                  <div className="message-avatar">
                    {message.role === "user" ? (
                      <User size={18} />
                    ) : (
                      <Bot size={19} />
                    )}
                  </div>

                  <div className="message-content">
                    <div className="message-author">
                      {message.role === "user"
                        ? "You"
                        : "Lyftr AI"}
                    </div>

                    <div
                      className={`message-bubble ${
                        message.role === "user"
                          ? "user-bubble"
                          : "assistant-bubble"
                      }`}
                      data-testid={
                        message.role === "assistant"
                          ? "assistant-message"
                          : undefined
                      }
                    >
                      {message.content}
                    </div>

                    {/* Assistant response metadata */}
                    {message.role === "assistant" &&
                       message.metadata &&
                       showMetadata &&  (
                        <div className="metadata-panel">
                          <div className="metadata-header">
                            <Database size={14} />
                            <span>Response Details</span>

                            <span
                              className={`source-badge ${
                                message.metadata
                                  .resolution_source ===
                                "LLM_CACHE"
                                  ? "cache-badge"
                                  : "live-badge"
                              }`}
                              data-testid="meta-source"
                            >
                              {message.metadata.resolution_source}
                            </span>
                          </div>

                          <div className="metadata-grid">
                            <div className="metadata-item">
                              <span className="metadata-label">
                                Model
                              </span>

                              <strong data-testid="meta-model">
                                {message.metadata.model}
                              </strong>
                            </div>

                            <div className="metadata-item">
                              <span className="metadata-label">
                                Latency
                              </span>

                              <strong data-testid="meta-latency">
                                {message.metadata.latency_ms} ms
                              </strong>
                            </div>

                            <div className="metadata-item">
                              <span className="metadata-label">
                                Input Tokens
                              </span>

                              <strong data-testid="meta-input-tokens">
                                {message.metadata.input_tokens}
                              </strong>
                            </div>

                            <div className="metadata-item">
                              <span className="metadata-label">
                                Output Tokens
                              </span>

                              <strong data-testid="meta-output-tokens">
                                {message.metadata.output_tokens}
                              </strong>
                            </div>
                          </div>

                          {message.metadata.fallback_attempts > 0 && (
                            <div className="fallback-info">
                              <Zap size={13} />
                              Provider fallback attempts:{" "}
                              {message.metadata.fallback_attempts}
                            </div>
                          )}
                        </div>
                      )}
                  </div>
                </div>
              ))}

              {/* Loading indicator */}
              {loading && (
                <div className="message-row assistant-row">
                  <div className="message-avatar">
                    <Bot size={19} />
                  </div>

                  <div className="message-content">
                    <div className="message-author">
                      Lyftr AI
                    </div>

                    <div className="typing-indicator">
                      <span></span>
                      <span></span>
                      <span></span>
                    </div>
                  </div>
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>
          )}

          {/* Error Message */}
          {error && (
            <div className="error-message">
              {error}
            </div>
          )}
        </section>

        {/* Message Input */}
        
{/* Modern Message Composer */}
<footer className="input-area">
  <form
    className="input-container"
    onSubmit={sendMessage}
  >
    <div className="composer-box">
      <textarea
        id="chat-input"
        value={input}
        onChange={(event) => {
          setInput(event.target.value);
          event.target.style.height = "auto";
          event.target.style.height =
            Math.min(event.target.scrollHeight, 180) + "px";
        }}
        onKeyDown={handleKeyDown}
        placeholder="Ask Lyftr AI anything..."
        rows={1}
        disabled={loading}
      />

      <div className="composer-bottom">
        <div className="composer-hint">
          <Sparkles size={15} />
          <span>AI-powered assistance</span>
        </div>

        <div className="composer-actions">
          <span className="enter-hint">
            Enter to send
          </span>

          <button
            id="send-button"
            type="submit"
            className="send-button"
            disabled={!input.trim() || loading}
            aria-label="Send message"
          >
            <Send size={18} />
          </button>
        </div>
      </div>
    </div>
  </form>

  <div className="input-disclaimer">
    Lyftr AI can make mistakes. Verify important information.
  </div>
</footer>
      </main>
    </div>
  );
}

export default App;
