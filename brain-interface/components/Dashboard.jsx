'use client'

import PipelineBar from '@/components/PipelineBar'
import EEGViewer   from '@/components/EEGViewer'
import AgentPanel  from '@/components/AgentPanel'
import { useState, useEffect } from 'react'

export default function Dashboard() {
  const [activeStep, setActiveStep] = useState(0)

  // Simulate pipeline progression
  useEffect(() => {
    const delays = [1200, 3500, 7000, 12000, 19000]
    const timers = delays.map((d, i) =>
      setTimeout(() => setActiveStep(i + 1), d)
    )
    return () => timers.forEach(clearTimeout)
  }, [])

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      height: '100vh',
      overflow: 'hidden',
      background: 'var(--bg-0)',
    }}>

      {/* TOP — Pipeline */}
      <div style={{ flexShrink: 0 }}>
        <PipelineBar activeStep={activeStep} runId="RUN-004" />
      </div>

      {/* MIDDLE — EEG Signal Viewer */}
      <div style={{
        flex: 1,
        minHeight: 0,
        borderBottom: '1px solid var(--border-1)',
      }}>
        <EEGViewer isProcessing={activeStep > 0 && activeStep < 6} />
      </div>

      {/* BOTTOM — Agent reasoning + journal */}
      <div style={{ height: 240, flexShrink: 0 }}>
        <AgentPanel />
      </div>
    </div>
  )
}