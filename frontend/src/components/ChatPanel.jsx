import { useState, useRef, useEffect } from 'react'
import { riskApi } from '../services/api'

const SUGGESTIONS = [
  "Is Mirpur safe during monsoon season?",
  "Which areas of Dhaka have highest flood risk?",
  "How does elevation affect flood risk in Bangladesh?",
  "What is the flood risk in Sylhet?",
  "When is the most dangerous flood period?",
]

function Message({ msg }) {
  const isUser = msg.role === 'user'
  return (
    <div style={{
      display:       'flex',
      justifyContent: isUser ? 'flex-end' : 'flex-start',
      marginBottom:  10,
    }}>
      <div style={{
        maxWidth:     '85%',
        padding:      '8px 12px',
        borderRadius: isUser ? '12px 12px 2px 12px' : '12px 12px 12px 2px',
        background:   isUser ? '#185FA5' : '#f4f4f4',
        color:        isUser ? 'white' : '#222',
        fontSize:     13,
        lineHeight:   1.55,
      }}>
        {msg.content}
        {msg.area && (
          <div style={{
            marginTop:  5,
            fontSize:   11,
            opacity:    0.7,
          }}>
            Area detected: {msg.area}
            {msg.context && ` — Risk: ${(msg.context.avg_risk * 100).toFixed(1)}%`}
          </div>
        )}
      </div>
    </div>
  )
}

export default function ChatPanel({ isOpen, onClose }) {
  const [messages,  setMessages]  = useState([{
    role:    'assistant',
    content: 'Hello! Ask me anything about flood risk in Bangladesh. I use real spatial data to answer your questions.',
  }])
  const [input,     setInput]     = useState('')
  const [loading,   setLoading]   = useState(false)
  const bottomRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const sendMessage = async (text) => {
    const question = text || input.trim()
    if (!question || loading) return

    setMessages(prev => [...prev, { role: 'user', content: question }])
    setInput('')
    setLoading(true)

    try {
      
      const res = await riskApi.askQuestion(question)
      const data = res.data
      
      setMessages(prev => [...prev, {
        role:    'assistant',
        content: data.answer,
        area:    data.area_detected,
        context: data.context,
      }])
    } catch {
      setMessages(prev => [...prev, {
        role:    'assistant',
        content: 'Sorry, I could not reach the analysis service. Make sure Django and Ollama are running.',
      }])
    } finally {
      setLoading(false)
    }
  }

  if (!isOpen) return null

  return (
    <div style={{
      position:     'absolute',
      bottom:       20,
      right:        12,
      width:        320,
      height:       460,
      background:   'white',
      borderRadius: 12,
      boxShadow:    '0 4px 20px rgba(0,0,0,0.18)',
      zIndex:       1001,
      display:      'flex',
      flexDirection:'column',
      overflow:     'hidden',
    }}>
      {/* Header */}
      <div style={{
        background:     '#0C447C',
        color:          'white',
        padding:        '10px 14px',
        display:        'flex',
        justifyContent: 'space-between',
        alignItems:     'center',
        flexShrink:     0,
      }}>
        <div>
          <div style={{ fontSize: 13, fontWeight: 500 }}>
            Flood Risk Assistant
          </div>
          <div style={{ fontSize: 11, opacity: 0.7 }}>
            Powered by Llama 3.2 (local)
          </div>
        </div>
        <button
          onClick={onClose}
          style={{
            background: 'rgba(255,255,255,0.2)',
            border:     'none',
            borderRadius: 6,
            color:      'white',
            cursor:     'pointer',
            padding:    '3px 8px',
            fontSize:   12,
          }}
        >
          Close
        </button>
      </div>

      {/* Messages */}
      <div style={{
        flex:       1,
        overflowY:  'auto',
        padding:    '12px 12px 4px',
      }}>
        {messages.map((msg, i) => (
          <Message key={i} msg={msg} />
        ))}
        {loading && (
          <div style={{
            fontSize: 12, color: '#888',
            padding: '4px 8px',
          }}>
            Analysing spatial data...
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Suggestions */}
      {messages.length === 1 && (
        <div style={{
          padding:  '0 10px 6px',
          display:  'flex',
          flexWrap: 'wrap',
          gap:      5,
        }}>
          {SUGGESTIONS.map((s, i) => (
            <button
              key={i}
              onClick={() => sendMessage(s)}
              style={{
                fontSize:     10,
                padding:      '3px 8px',
                borderRadius: 12,
                border:       '1px solid #B5D4F4',
                background:   '#E6F1FB',
                color:        '#0C447C',
                cursor:       'pointer',
              }}
            >
              {s}
            </button>
          ))}
        </div>
      )}

      {/* Input */}
      <div style={{
        padding:     '8px 10px',
        borderTop:   '1px solid #eee',
        display:     'flex',
        gap:         6,
        flexShrink:  0,
      }}>
        <input
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && sendMessage()}
          placeholder="Ask about flood risk..."
          style={{
            flex:         1,
            padding:      '7px 10px',
            borderRadius: 8,
            border:       '1px solid #ddd',
            fontSize:     12,
            outline:      'none',
          }}
        />
        <button
          onClick={() => sendMessage()}
          disabled={!input.trim() || loading}
          style={{
            padding:      '7px 12px',
            borderRadius: 8,
            border:       'none',
            background:   input.trim() ? '#185FA5' : '#ccc',
            color:        'white',
            cursor:       input.trim() ? 'pointer' : 'default',
            fontSize:     12,
            fontWeight:   500,
          }}
        >
          Ask
        </button>
      </div>
    </div>
  )
}