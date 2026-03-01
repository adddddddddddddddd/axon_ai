import { useEffect, useState } from 'react'

export function useAgentSocket(url = 'ws://localhost:8000/ws/agent') {
  const [logs,        setLogs]        = useState([])
  const [pipelineStep, setPipelineStep] = useState(0)
  const [connected,   setConnected]   = useState(false)
  const [done,        setDone]        = useState(false)

  useEffect(() => {
    const ws = new WebSocket(url)

    ws.onopen  = () => setConnected(true)
    ws.onclose = () => setConnected(false)

    ws.onmessage = (e) => {
      const msg = JSON.parse(e.data)

      if (msg.type === 'log') {
        setLogs(v => [...v, msg.text])
      }
      if (msg.type === 'pipeline') {
        setPipelineStep(msg.step)
      }
      if (msg.type === 'done') {
        setLogs(v => [...v, msg.text])
        setDone(true)
      }
    }

    return () => ws.close()
  }, [url])

  return { logs, pipelineStep, connected, done }
}