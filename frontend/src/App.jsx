import { useState, useRef, useEffect, useCallback } from 'react'
import { Send, CheckCircle, XCircle, Mic, Square, ListTodo, Bell, X, Trash2 } from 'lucide-react'

const TASKS_API_BASE = window.electron?.isElectron ? 'http://127.0.0.1:8000' : 'http://localhost:8000'

function TasksPanel({ sessionId, onClose, refreshKey }) {
  const [tab, setTab] = useState('todos')
  const [todos, setTodos] = useState([])
  const [reminders, setReminders] = useState([])
  const [loading, setLoading] = useState(false)

  const fetchAll = useCallback(async () => {
    setLoading(true)
    try {
      const [t, r] = await Promise.all([
        fetch(`${TASKS_API_BASE}/todos?session_id=${sessionId}`).then(r => r.json()),
        fetch(`${TASKS_API_BASE}/reminders?session_id=${sessionId}`).then(r => r.json()),
      ])
      setTodos(t.todos || [])
      setReminders(r.reminders || [])
    } catch { /* network error — silently ignore */ }
    setLoading(false)
  }, [sessionId])

  useEffect(() => {
    let cancelled = false
    fetchAll().then(() => { if (cancelled) return }).catch(() => {})
    return () => { cancelled = true }
  }, [fetchAll, refreshKey])

  const completeTodo = async (id) => {
    await fetch(`${TASKS_API_BASE}/todos/${id}/complete`, { method: 'PATCH' })
    fetchAll()
  }
  const deleteTodo = async (id) => {
    await fetch(`${TASKS_API_BASE}/todos/${id}?session_id=${sessionId}`, { method: 'DELETE' })
    fetchAll()
  }
  const completeReminder = async (id) => {
    await fetch(`${TASKS_API_BASE}/reminders/${id}/complete`, { method: 'PATCH' })
    fetchAll()
  }

  const fmtTime = (iso) => {
    if (!iso) return null
    try {
      return new Date(iso).toLocaleString('en-IN', { dateStyle: 'medium', timeStyle: 'short' })
    } catch { return iso }
  }

  return (
    <div
      className="fixed right-0 top-0 h-screen w-80 z-50 flex flex-col"
      style={{
        background: 'linear-gradient(180deg,#040d1e 0%,#020917 100%)',
        borderLeft: '1px solid rgba(34,211,238,0.15)',
        backdropFilter: 'blur(20px)',
      }}
    >
      {/* Header */}
      <div className="flex items-center justify-between px-5 py-4 border-b border-cyan-900/20">
        <p className="text-cyan-300 text-sm font-medium tracking-wide">Tasks & Reminders</p>
        <button onClick={onClose} className="text-slate-500 hover:text-white transition-colors cursor-pointer">
          <X size={16} />
        </button>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-cyan-900/20">
        {[['todos', 'To-Do', <ListTodo size={13} />], ['reminders', 'Reminders', <Bell size={13} />]].map(([id, label, icon]) => (
          <button
            key={id}
            onClick={() => setTab(id)}
            className="flex-1 flex items-center justify-center gap-1.5 py-3 text-xs tracking-widest uppercase transition-all cursor-pointer"
            style={{
              color: tab === id ? '#22d3ee' : 'rgba(100,116,139,0.8)',
              borderBottom: tab === id ? '2px solid #22d3ee' : '2px solid transparent',
            }}
          >
            {icon}{label}
          </button>
        ))}
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto px-4 py-4 flex flex-col gap-2">
        {loading && <p className="text-slate-600 text-xs text-center mt-4">Loading…</p>}

        {tab === 'todos' && !loading && (
          todos.length === 0
            ? <div className="text-center mt-8">
                <ListTodo size={28} className="text-cyan-900/50 mx-auto mb-2" />
                <p className="text-slate-600 text-xs">No pending tasks</p>
                <p className="text-slate-700 text-xs mt-1">Say "Add todo: buy groceries"</p>
              </div>
            : todos.map(t => (
                <div
                  key={t.id}
                  className="flex items-start gap-3 px-3 py-2.5 rounded-xl group"
                  style={{ background: 'rgba(34,211,238,0.04)', border: '1px solid rgba(34,211,238,0.08)' }}
                >
                  <button
                    onClick={() => completeTodo(t.id)}
                    className="mt-0.5 w-4 h-4 rounded-full border border-cyan-700/50 shrink-0 hover:border-cyan-400 hover:bg-cyan-400/20 transition-all cursor-pointer"
                  />
                  <span className="flex-1 text-cyan-100/80 text-xs leading-relaxed">{t.title}</span>
                  <button
                    onClick={() => deleteTodo(t.id)}
                    className="opacity-0 group-hover:opacity-100 text-slate-600 hover:text-red-400 transition-all cursor-pointer shrink-0"
                  >
                    <Trash2 size={12} />
                  </button>
                </div>
              ))
        )}

        {tab === 'reminders' && !loading && (
          reminders.length === 0
            ? <div className="text-center mt-8">
                <Bell size={28} className="text-cyan-900/50 mx-auto mb-2" />
                <p className="text-slate-600 text-xs">No active reminders</p>
                <p className="text-slate-700 text-xs mt-1">Say "Remind me to call John at 9am"</p>
              </div>
            : reminders.map(r => (
                <div
                  key={r.id}
                  className="flex items-start gap-3 px-3 py-2.5 rounded-xl group"
                  style={{ background: 'rgba(167,139,250,0.05)', border: '1px solid rgba(167,139,250,0.12)' }}
                >
                  <button
                    onClick={() => completeReminder(r.id)}
                    className="mt-0.5 w-4 h-4 rounded-full border border-violet-700/50 shrink-0 hover:border-violet-400 hover:bg-violet-400/20 transition-all cursor-pointer"
                  />
                  <div className="flex-1 min-w-0">
                    <p className="text-violet-100/80 text-xs leading-relaxed">{r.title}</p>
                    {r.remind_at && (
                      <p className="text-violet-400/50 text-xs mt-0.5">{fmtTime(r.remind_at)}</p>
                    )}
                  </div>
                </div>
              ))
        )}
      </div>

      {/* Footer hint */}
      <div className="px-4 py-3 border-t border-cyan-900/20">
        <p className="text-slate-700 text-xs text-center">Use voice or chat to add tasks</p>
      </div>
    </div>
  )
}

const SUGGESTIONS = [
  'Show my latest emails',
  "What's on my calendar today?",
  'Send an email to team@example.com',
]

const API_BASE = window.electron?.isElectron ? 'http://127.0.0.1:8000' : ''

function VoiceOrb({ active, thinking, listening, onClick }) {
  return (
    <div
      className="relative flex items-center justify-center w-56 h-56 cursor-pointer select-none"
      onClick={onClick}
      title={listening ? 'Stop listening' : 'Click to speak'}
    >
      {/* Outer slow pulse rings */}
      {[1, 2, 3].map(i => (
        <span
          key={i}
          className="absolute rounded-full border"
          style={{
            width: `${100 + i * 44}px`,
            height: `${100 + i * 44}px`,
            borderColor: listening ? 'rgba(239,68,68,0.35)' : 'rgba(34,211,238,0.2)',
            animation: listening
              ? `ping ${0.8 + i * 0.3}s cubic-bezier(0,0,0.2,1) infinite`
              : active
              ? `ping ${1 + i * 0.4}s cubic-bezier(0,0,0.2,1) infinite`
              : thinking
              ? `spin ${3 + i}s linear infinite`
              : 'none',
            opacity: listening ? 0.7 - i * 0.15 : active ? 0.5 - i * 0.1 : 0.15,
          }}
        />
      ))}

      {/* Mid glow ring */}
      <span
        className="absolute rounded-full"
        style={{
          width: '130px',
          height: '130px',
          background: listening
            ? 'radial-gradient(circle, rgba(239,68,68,0.3) 0%, transparent 70%)'
            : active
            ? 'radial-gradient(circle, rgba(34,211,238,0.25) 0%, transparent 70%)'
            : thinking
            ? 'radial-gradient(circle, rgba(139,92,246,0.25) 0%, transparent 70%)'
            : 'radial-gradient(circle, rgba(34,211,238,0.08) 0%, transparent 70%)',
          transition: 'all 0.5s ease',
        }}
      />

      {/* Core orb */}
      <div
        className="relative z-10 w-24 h-24 rounded-full flex items-center justify-center"
        style={{
          background: listening
            ? 'radial-gradient(circle at 35% 35%, #fca5a5, #dc2626)'
            : active
            ? 'radial-gradient(circle at 35% 35%, #67e8f9, #0891b2)'
            : thinking
            ? 'radial-gradient(circle at 35% 35%, #a78bfa, #5b21b6)'
            : 'radial-gradient(circle at 35% 35%, #334155, #0f172a)',
          boxShadow: listening
            ? '0 0 40px rgba(239,68,68,0.7), 0 0 80px rgba(239,68,68,0.3)'
            : active
            ? '0 0 40px rgba(34,211,238,0.6), 0 0 80px rgba(34,211,238,0.2)'
            : thinking
            ? '0 0 40px rgba(139,92,246,0.6), 0 0 80px rgba(139,92,246,0.2)'
            : '0 0 20px rgba(34,211,238,0.1)',
          transition: 'all 0.4s ease',
        }}
      >
        {thinking ? (
          <div className="flex gap-1 items-center">
            {[0, 1, 2].map(i => (
              <span
                key={i}
                className="w-1.5 h-1.5 rounded-full bg-white/80"
                style={{ animation: `bounce 0.8s ease-in-out ${i * 0.15}s infinite` }}
              />
            ))}
          </div>
        ) : listening ? (
          <Square size={24} className="text-white drop-shadow" fill="white" />
        ) : (
          <Mic size={28} className={active ? 'text-white drop-shadow' : 'text-cyan-300/80'} />
        )}
      </div>

      {/* Waveform bars — shown when active or listening */}
      {(active || listening) && (
        <div className="absolute flex items-center gap-1" style={{ bottom: '10px' }}>
          {[3, 5, 8, 12, 8, 5, 3].map((h, i) => (
            <span
              key={i}
              className="w-1 rounded-full"
              style={{
                height: `${h}px`,
                background: listening ? 'rgb(239,68,68)' : 'rgb(34,211,238)',
                animation: `waveBar 0.6s ease-in-out ${i * 0.08}s infinite alternate`,
              }}
            />
          ))}
        </div>
      )}
    </div>
  )
}

function renderInline(text) {
  const parts = text.split(/(\*\*[^*]+\*\*|`[^`]+`|\[([^\]]+)\]\(([^)]+)\))/g)
  const nodes = []
  let i = 0
  while (i < parts.length) {
    const part = parts[i]
    if (!part) { i++; continue }
    if (part.startsWith('**') && part.endsWith('**')) {
      nodes.push(<strong key={i} className="text-cyan-300 font-semibold">{part.slice(2, -2)}</strong>)
    } else if (part.startsWith('`') && part.endsWith('`')) {
      nodes.push(
        <code key={i} className="px-1.5 py-0.5 rounded text-xs font-mono"
          style={{ background: 'rgba(34,211,238,0.12)', color: '#67e8f9' }}>
          {part.slice(1, -1)}
        </code>
      )
    } else if (part.startsWith('[')) {
      const m = part.match(/^\[([^\]]+)\]\(([^)]+)\)$/)
      if (m) nodes.push(<a key={i} href={m[2]} target="_blank" rel="noreferrer"
        className="text-cyan-400 underline underline-offset-2 hover:text-cyan-300">{m[1]}</a>)
      else nodes.push(part)
    } else {
      nodes.push(part)
    }
    i++
  }
  return nodes
}

function MarkdownContent({ text, isUser }) {
  if (isUser) return <span>{text}</span>
  const lines = text.split('\n')
  const elements = []
  let listItems = []
  let listType = null

  const flushList = (key) => {
    if (!listItems.length) return
    if (listType === 'ul') {
      elements.push(
        <ul key={`ul-${key}`} className="mt-1.5 mb-1 space-y-1 pl-1">
          {listItems.map((item, j) => (
            <li key={j} className="flex gap-2 items-start">
              <span className="mt-1.5 w-1 h-1 rounded-full shrink-0" style={{ background: 'rgba(34,211,238,0.6)' }} />
              <span>{renderInline(item)}</span>
            </li>
          ))}
        </ul>
      )
    } else {
      elements.push(
        <ol key={`ol-${key}`} className="mt-1.5 mb-1 space-y-1 pl-1 list-none">
          {listItems.map((item, j) => (
            <li key={j} className="flex gap-2 items-start">
              <span className="shrink-0 text-cyan-400 font-mono text-xs mt-0.5">{j + 1}.</span>
              <span>{renderInline(item)}</span>
            </li>
          ))}
        </ol>
      )
    }
    listItems = []
    listType = null
  }

  lines.forEach((line, idx) => {
    const ulMatch = line.match(/^[-•*]\s+(.+)/)
    const olMatch = line.match(/^\d+\.\s+(.+)/)
    const h3Match = line.match(/^###\s+(.+)/)
    const h2Match = line.match(/^##\s+(.+)/)

    if (ulMatch) {
      if (listType === 'ol') flushList(idx)
      listType = 'ul'
      listItems.push(ulMatch[1])
    } else if (olMatch) {
      if (listType === 'ul') flushList(idx)
      listType = 'ol'
      listItems.push(olMatch[1])
    } else {
      flushList(idx)
      if (!line.trim()) {
        if (elements.length) elements.push(<div key={`sp-${idx}`} className="h-1" />)
      } else if (h2Match) {
        elements.push(
          <p key={idx} className="text-cyan-300 font-semibold text-sm mt-2 mb-0.5 tracking-wide">
            {renderInline(h2Match[1])}
          </p>
        )
      } else if (h3Match) {
        elements.push(
          <p key={idx} className="text-cyan-400/80 font-medium text-xs mt-2 mb-0.5 uppercase tracking-widest">
            {renderInline(h3Match[1])}
          </p>
        )
      } else {
        elements.push(<p key={idx} className="leading-relaxed">{renderInline(line)}</p>)
      }
    }
  })
  flushList('end')
  return <div className="flex flex-col gap-0.5 text-sm">{elements}</div>
}

function MessageRow({ msg }) {
  const isUser = msg.role === 'user'
  const isConfirm = msg.status === 'needs_confirmation'
  return (
    <div className={`flex gap-3 items-start ${isUser ? 'flex-row-reverse' : ''}`}>
      <div
        className="shrink-0 w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold mt-0.5"
        style={{
          background: isUser
            ? 'linear-gradient(135deg,#7c3aed,#4f46e5)'
            : 'linear-gradient(135deg,#0e7490,#0891b2)',
          boxShadow: isUser
            ? '0 0 8px rgba(124,58,237,0.5)'
            : '0 0 8px rgba(8,145,178,0.5)',
        }}
      >
        {isUser ? 'U' : 'J'}
      </div>
      <div
        className={`max-w-[80%] px-4 py-2.5 rounded-2xl
          ${isUser ? 'rounded-tr-sm' : 'rounded-tl-sm'}
          ${isConfirm
            ? 'border border-amber-400/40 text-amber-200'
            : isUser
            ? 'text-white'
            : 'text-cyan-50/90'}`}
        style={{
          background: isConfirm
            ? 'rgba(251,191,36,0.08)'
            : isUser
            ? 'rgba(109,40,217,0.35)'
            : 'rgba(8,145,178,0.12)',
          backdropFilter: 'blur(8px)',
          border: isConfirm ? undefined : `1px solid ${isUser ? 'rgba(139,92,246,0.3)' : 'rgba(34,211,238,0.12)'}`,
        }}
      >
        <MarkdownContent text={msg.content} isUser={isUser} />
      </div>
    </div>
  )
}

export default function App() {
  const [sessionId, setSessionId] = useState(null)
  const [messages, setMessages] = useState([
    {
      id: 'welcome',
      role: 'assistant',
      content: "JARVIS online. I can read your emails, check your calendar, or send messages on your behalf. How can I assist?",
    },
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [pendingConfirm, setPendingConfirm] = useState(false)
  const [active, setActive] = useState(false)
  const [showTasks, setShowTasks] = useState(false)
  const [tasksRefreshKey, setTasksRefreshKey] = useState(0)
  const [listening, setListening] = useState(false)
  const mediaRecorderRef = useRef(null)
  const audioChunksRef = useRef([])
  const bottomRef = useRef(null)
  const inputRef = useRef(null)

  // Load persistent session ID
  useEffect(() => {
    if (window.electron?.getSessionId) {
      window.electron.getSessionId().then(id => {
        setSessionId(id)
        console.log('[app] loaded session ID:', id)
      }).catch(() => {
        // Fallback to random ID if electron API fails
        setSessionId(crypto.randomUUID())
      })
    } else {
      // Non-electron environment
      setSessionId(crypto.randomUUID())
    }
  }, [])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  const apiPost = useCallback(async (path, body) => {
    const res = await fetch(API_BASE + path, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: sessionId, ...body }),
    })
    if (!res.ok) {
      const err = await res.json().catch(() => ({}))
      throw new Error(err.detail || `HTTP ${res.status}`)
    }
    return res.json()
  }, [sessionId])

  const addMessage = useCallback((msg) => {
    setMessages(prev => [...prev, { id: crypto.randomUUID(), ...msg }])
  }, [])

  const speak = useCallback((text) => {
    if (!window.speechSynthesis) return
    window.speechSynthesis.cancel()
    const utt = new SpeechSynthesisUtterance(text)
    utt.lang = 'en-US'
    utt.rate = 1.05
    utt.pitch = 1
    window.speechSynthesis.speak(utt)
  }, [])

  const sendCommand = useCallback(async (text) => {
    if (!text.trim() || loading) return
    setInput('')
    addMessage({ role: 'user', content: text })
    setLoading(true)
    setActive(true)

    try {
      const data = await apiPost('/command', { text })
      if (data.status === 'needs_confirmation') {
        setPendingConfirm(true)
        addMessage({ role: 'assistant', content: data.response || data.message, status: data.status })
        if (['add_todo','list_todos','complete_todo','set_reminder','list_reminders','complete_reminder'].includes(data.intent)) {
          setTasksRefreshKey(k => k + 1)
        }
        speak(data.message)
      } else {
        addMessage({ role: 'assistant', content: data.response })
        speak(data.response)
      }
    } catch (e) {
      addMessage({ role: 'assistant', content: `Error: ${e.message}` })
    } finally {
      setLoading(false)
      setActive(false)
      inputRef.current?.focus()
    }
  }, [loading, addMessage, speak, apiPost])

  const toggleListening = useCallback(async () => {
    if (listening) {
      mediaRecorderRef.current?.stop()
      return
    }
    let stream
    try {
      stream = await navigator.mediaDevices.getUserMedia({ audio: true })
    } catch {
      addMessage({ role: 'assistant', content: 'Microphone access denied. Please allow mic permission.' })
      return
    }
    audioChunksRef.current = []
    const mimeType = MediaRecorder.isTypeSupported('audio/webm') ? 'audio/webm' : 'audio/ogg'
    const recorder = new MediaRecorder(stream, { mimeType })
    mediaRecorderRef.current = recorder

    recorder.ondataavailable = (e) => {
      if (e.data.size > 0) audioChunksRef.current.push(e.data)
    }

    recorder.onstart = () => setListening(true)

    recorder.onstop = async () => {
      setListening(false)
      stream.getTracks().forEach(t => t.stop())
      const blob = new Blob(audioChunksRef.current, { type: mimeType })
      audioChunksRef.current = []
      if (blob.size < 1000) return
      setLoading(true)
      setActive(true)
      try {
        const ext = mimeType.includes('webm') ? 'webm' : 'ogg'
        const form = new FormData()
        form.append('file', blob, `audio.${ext}`)
        const base = window.electron?.isElectron ? 'http://127.0.0.1:8000' : ''
        const res = await fetch(`${base}/transcribe`, { method: 'POST', body: form })
        const { text } = await res.json()
        if (text?.trim()) {
          setInput('')
          await sendCommand(text.trim())
        }
      } catch (e) {
        addMessage({ role: 'assistant', content: `Transcription error: ${e.message}` })
        setLoading(false)
        setActive(false)
      }
    }

    recorder.start()
  }, [listening, sendCommand, addMessage])

  const handleConfirm = async () => {
    setPendingConfirm(false)
    setLoading(true)
    setActive(true)
    try {
      const data = await apiPost('/confirm', {})
      addMessage({ role: 'assistant', content: data.response || 'Done!' })
    } catch (e) {
      addMessage({ role: 'assistant', content: `Error: ${e.message}` })
    } finally {
      setLoading(false)
      setActive(false)
    }
  }

  const handleCancel = async () => {
    setPendingConfirm(false)
    try {
      await apiPost('/cancel', {})
      addMessage({ role: 'assistant', content: 'Action cancelled.' })
    } catch {
      addMessage({ role: 'assistant', content: 'Action cancelled.' })
    }
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    sendCommand(input)
  }

  return (
    <>
      <style>{`
        @keyframes waveBar {
          from { transform: scaleY(1); }
          to   { transform: scaleY(2.5); }
        }
        body { background: #020917; }
        ::-webkit-scrollbar { width: 4px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: rgba(34,211,238,0.2); border-radius: 4px; }
        .drag-region { -webkit-app-region: drag; }
        .no-drag { -webkit-app-region: no-drag; }
      `}</style>

      <div className="h-screen overflow-hidden flex" style={{ background: 'linear-gradient(135deg,#020917 0%,#0a1628 50%,#080d1f 100%)' }}>

        {/* Grid overlay */}
        <div className="fixed inset-0 pointer-events-none" style={{
          backgroundImage: 'linear-gradient(rgba(34,211,238,0.03) 1px,transparent 1px),linear-gradient(90deg,rgba(34,211,238,0.03) 1px,transparent 1px)',
          backgroundSize: '60px 60px',
        }} />

        {/* Left panel — Orb + status */}
        <div className="hidden lg:flex w-96 shrink-0 flex-col items-center justify-center gap-8 relative border-r border-cyan-900/30 px-8 h-screen overflow-hidden">
          {/* Top label — draggable title bar area */}
          <div className="drag-region absolute top-0 left-0 right-0 h-16" />
          <div className="absolute top-8 left-8 right-8">
            <p className="text-cyan-400/50 text-xs tracking-[0.3em] uppercase">J.A.R.V.I.S</p>
            <p className="text-slate-500 text-xs mt-1">Just A Rather Very Intelligent System</p>
          </div>

          <VoiceOrb active={active} thinking={loading} listening={listening} onClick={toggleListening} />

          {/* Status badge */}
          <div
            className="flex items-center gap-2 px-4 py-2 rounded-full text-xs"
            style={{ background: 'rgba(34,211,238,0.06)', border: '1px solid rgba(34,211,238,0.15)' }}
          >
            <span
              className="w-2 h-2 rounded-full"
              style={{
                background: listening ? '#ef4444' : loading ? '#a78bfa' : '#22d3ee',
                boxShadow: listening ? '0 0 6px #ef4444' : loading ? '0 0 6px #a78bfa' : '0 0 6px #22d3ee',
                animation: 'pulse 2s infinite',
              }}
            />
            <span className="text-cyan-300/70 tracking-widest uppercase">
              {listening ? 'Listening…' : loading ? 'Processing…' : pendingConfirm ? 'Awaiting confirmation' : 'Ready'}
            </span>
          </div>

          {/* Quick suggestions */}
          {messages.length <= 1 && !loading && (
            <div className="flex flex-col gap-2 w-full">
              <p className="text-slate-500 text-xs tracking-widest uppercase mb-1">Quick commands</p>
              {SUGGESTIONS.map(s => (
                <button
                  key={s}
                  onClick={() => sendCommand(s)}
                  className="text-left text-xs text-cyan-300/70 hover:text-cyan-200 px-4 py-2.5 rounded-xl transition-all cursor-pointer"
                  style={{ background: 'rgba(34,211,238,0.04)', border: '1px solid rgba(34,211,238,0.1)' }}
                  onMouseEnter={e => e.currentTarget.style.background = 'rgba(34,211,238,0.08)'}
                  onMouseLeave={e => e.currentTarget.style.background = 'rgba(34,211,238,0.04)'}
                >
                  {s}
                </button>
              ))}
            </div>
          )}

          {/* Bottom decoration */}
          <div className="absolute bottom-8 left-8 right-8 flex flex-col gap-1">
            {['NEURAL NET', 'VOICE ENGINE', 'MEMORY'].map((label, i) => (
              <div key={label} className="flex items-center justify-between">
                <span className="text-slate-600 text-xs tracking-widest">{label}</span>
                <div className="flex gap-0.5">
                  {Array.from({ length: 6 }).map((_, j) => (
                    <span
                      key={j}
                      className="w-4 h-1 rounded-sm"
                      style={{ background: j < 4 - i ? 'rgba(34,211,238,0.5)' : 'rgba(34,211,238,0.1)' }}
                    />
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Right panel — Chat */}
        <div className="flex-1 flex flex-col h-screen overflow-hidden">

          {/* Top bar — draggable */}
          <div className="drag-region flex items-center justify-between px-8 py-5 border-b border-cyan-900/20" style={{ paddingLeft: window.electron?.isElectron ? '5rem' : undefined }}>
            <div className="no-drag flex items-center gap-3 lg:hidden">
              <VoiceOrb active={active} thinking={loading} listening={listening} onClick={toggleListening} />
            </div>
            <div>
              <h1 className="text-white font-light text-xl tracking-wide">Voice Agent</h1>
              <p className="text-slate-500 text-xs tracking-widest uppercase mt-0.5">AI Assistant Interface</p>
            </div>
            <div className="no-drag flex items-center gap-3">
              <button
                onClick={() => setShowTasks(v => !v)}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs transition-all cursor-pointer"
                style={{
                  background: showTasks ? 'rgba(34,211,238,0.12)' : 'rgba(34,211,238,0.04)',
                  border: `1px solid ${showTasks ? 'rgba(34,211,238,0.4)' : 'rgba(34,211,238,0.15)'}`,
                  color: showTasks ? '#22d3ee' : 'rgba(100,116,139,0.8)',
                }}
                title="Tasks & Reminders"
              >
                <ListTodo size={13} />
                <span className="hidden sm:inline tracking-widest uppercase">Tasks</span>
              </button>
              <div className="flex items-center gap-2 text-xs text-cyan-400/50 tracking-widest uppercase">
                <span
                  className="w-1.5 h-1.5 rounded-full"
                  style={{ background: '#22d3ee', boxShadow: '0 0 6px #22d3ee', animation: 'pulse 2s infinite' }}
                />
                Online
              </div>
            </div>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto px-6 lg:px-10 py-6 flex flex-col gap-5">
            {messages.map(msg => <MessageRow key={msg.id} msg={msg} />)}

            {/* Thinking indicator */}
            {loading && (
              <div className="flex gap-3 items-start">
                <div
                  className="shrink-0 w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold"
                  style={{ background: 'linear-gradient(135deg,#0e7490,#0891b2)', boxShadow: '0 0 8px rgba(8,145,178,0.5)' }}
                >J</div>
                <div
                  className="px-4 py-3 rounded-2xl rounded-tl-sm flex gap-1.5 items-center"
                  style={{ background: 'rgba(8,145,178,0.1)', border: '1px solid rgba(34,211,238,0.12)' }}
                >
                  {[0, 1, 2, 3, 4].map(i => (
                    <span
                      key={i}
                      className="w-0.5 rounded-full bg-cyan-400/60"
                      style={{
                        height: '16px',
                        animation: `waveBar 0.5s ease-in-out ${i * 0.1}s infinite alternate`,
                      }}
                    />
                  ))}
                </div>
              </div>
            )}
            <div ref={bottomRef} />
          </div>

          {/* Confirmation overlay */}
          {pendingConfirm && (
            <div
              className="mx-6 lg:mx-10 mb-4 px-6 py-4 rounded-2xl flex items-center justify-between gap-4"
              style={{
                background: 'rgba(251,191,36,0.06)',
                border: '1px solid rgba(251,191,36,0.25)',
                backdropFilter: 'blur(8px)',
              }}
            >
              <div>
                <p className="text-amber-300 text-sm font-medium tracking-wide">Authorization Required</p>
                <p className="text-amber-400/60 text-xs mt-0.5">Confirm to execute this action</p>
              </div>
              <div className="flex gap-3">
                <button
                  onClick={handleCancel}
                  className="flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs text-slate-400 hover:text-white transition-all cursor-pointer"
                  style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)' }}
                >
                  <XCircle size={13} /> Abort
                </button>
                <button
                  onClick={handleConfirm}
                  className="flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs text-white transition-all cursor-pointer"
                  style={{ background: 'rgba(34,211,238,0.15)', border: '1px solid rgba(34,211,238,0.4)', boxShadow: '0 0 12px rgba(34,211,238,0.15)' }}
                  onMouseEnter={e => e.currentTarget.style.background = 'rgba(34,211,238,0.25)'}
                  onMouseLeave={e => e.currentTarget.style.background = 'rgba(34,211,238,0.15)'}
                >
                  <CheckCircle size={13} /> Authorize
                </button>
              </div>
            </div>
          )}

          {/* Input */}
          <form
            onSubmit={handleSubmit}
            className="px-6 lg:px-10 pb-8 pt-2 flex gap-3 items-center"
          >
            <div
              className="flex-1 flex items-center gap-3 px-5 py-3.5 rounded-2xl"
              style={{
                background: 'rgba(34,211,238,0.04)',
                border: `1px solid ${input ? 'rgba(34,211,238,0.3)' : 'rgba(34,211,238,0.1)'}`,
                boxShadow: input ? '0 0 20px rgba(34,211,238,0.06)' : 'none',
                transition: 'all 0.3s ease',
              }}
            >
              <input
                ref={inputRef}
                value={input}
                onChange={e => setInput(e.target.value)}
                placeholder={listening ? 'Listening…' : 'Type or click mic to speak…'}
                disabled={loading || pendingConfirm}
                className="flex-1 bg-transparent text-sm text-cyan-50 placeholder-slate-600 outline-none disabled:opacity-40"
              />
              <button
                type="button"
                onClick={toggleListening}
                disabled={loading || pendingConfirm}
                className="shrink-0 w-8 h-8 rounded-full flex items-center justify-center transition-all cursor-pointer disabled:opacity-30"
                style={{
                  background: listening ? 'rgba(239,68,68,0.2)' : 'rgba(34,211,238,0.08)',
                  border: `1px solid ${listening ? 'rgba(239,68,68,0.5)' : 'rgba(34,211,238,0.2)'}`,
                  boxShadow: listening ? '0 0 10px rgba(239,68,68,0.3)' : 'none',
                }}
                title={listening ? 'Stop' : 'Start voice input'}
              >
                {listening
                  ? <Square size={12} className="text-red-400" fill="currentColor" />
                  : <Mic size={14} className="text-cyan-400" />}
              </button>
            </div>
            <button
              type="submit"
              disabled={!input.trim() || loading || pendingConfirm}
              className="w-12 h-12 rounded-xl flex items-center justify-center text-white transition-all cursor-pointer disabled:opacity-30 disabled:cursor-not-allowed shrink-0"
              style={{
                background: 'linear-gradient(135deg,#0891b2,#0e7490)',
                boxShadow: input.trim() ? '0 0 20px rgba(34,211,238,0.3)' : 'none',
              }}
            >
              <Send size={16} />
            </button>
          </form>
        </div>
      </div>
      {showTasks && sessionId && (
        <TasksPanel
          sessionId={sessionId}
          onClose={() => setShowTasks(false)}
          refreshKey={tasksRefreshKey}
        />
      )}
    </>
  )
}
