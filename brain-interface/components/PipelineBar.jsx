'use client'

import { useEffect, useState } from 'react'

const STEPS = [
  { id: 'ingest',    label: 'FILE INGEST',       detail: 'parsing .edf header' },
  { id: 'quality',   label: 'QUALITY CHECK',      detail: 'impedance + SNR scan' },
  { id: 'filter',    label: 'BANDPASS FILTER',    detail: '1–40 Hz, notch 50 Hz' },
  { id: 'ica',       label: 'ICA DECOMPOSITION',  detail: '64 components' },
  { id: 'artifact',  label: 'ARTIFACT REMOVAL',   detail: 'ocular + cardiac' },
  { id: 'export',    label: 'FEATURE EXPORT',     detail: 'vision pipeline ready' },
]

export default function PipelineBar({ activeStep = 2, runId = 'RUN-004' }) {
  const [tick, setTick] = useState(true)

  useEffect(() => {
    const t = setInterval(() => setTick(v => !v), 800)
    return () => clearInterval(t)
  }, [])

  return (
    <div style={{
      borderBottom: '1px solid var(--border-1)',
      background: 'var(--bg-1)',
      padding: '0 32px',
    }}>
      {/* Top bar */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '10px 0 8px',
        borderBottom: '1px solid var(--border-0)',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          <span style={{ fontSize: 10, letterSpacing: 3, color: 'var(--text-3)', fontWeight: 600 }}>
            EEG//VISION
          </span>
          <span style={{ color: 'var(--border-2)', fontSize: 10 }}>|</span>
          <span style={{ fontSize: 10, color: 'var(--text-3)', letterSpacing: 1 }}>{runId}</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <div style={{
            width: 5, height: 5, borderRadius: '50%',
            background: 'var(--running)',
            opacity: tick ? 1 : 0.2,
            transition: 'opacity 0.3s',
          }} />
          <span style={{ fontSize: 10, letterSpacing: 2, color: 'var(--text-2)' }}>PROCESSING</span>
        </div>
      </div>

      {/* Steps */}
      <div style={{
        display: 'flex',
        alignItems: 'stretch',
        gap: 0,
        padding: '16px 0',
        overflowX: 'auto',
      }}>
        {STEPS.map((step, i) => {
          const isDone    = i < activeStep
          const isRunning = i === activeStep
          const isPending = i > activeStep

          return (
            <div key={step.id} style={{ display: 'flex', alignItems: 'center', flex: 1, minWidth: 0 }}>
              {/* Step card */}
              <div style={{
                flex: 1,
                minWidth: 0,
                padding: '8px 12px',
                borderRadius: 'var(--r-md)',
                border: `1px solid ${isRunning ? 'var(--border-3)' : 'var(--border-0)'}`,
                background: isRunning ? 'var(--bg-3)' : 'transparent',
                transition: 'all 0.4s ease',
                animation: isRunning ? 'fade-up 0.4s ease' : 'none',
              }}>
                {/* Index + label */}
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                  <span style={{
                    fontSize: 9,
                    letterSpacing: 1,
                    color: isDone ? 'var(--text-3)' : isRunning ? 'var(--text-0)' : 'var(--text-4)',
                    fontWeight: 600,
                  }}>
                    {String(i + 1).padStart(2, '0')}
                  </span>
                  <span style={{
                    fontSize: 9,
                    letterSpacing: 2,
                    color: isDone ? 'var(--text-3)' : isRunning ? 'var(--text-0)' : 'var(--text-4)',
                    fontWeight: isDone ? 400 : 600,
                    whiteSpace: 'nowrap',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                  }}>
                    {step.label}
                  </span>
                </div>

                {/* Detail */}
                <div style={{
                  fontSize: 9,
                  color: isRunning ? 'var(--text-2)' : 'var(--text-4)',
                  letterSpacing: 0.5,
                  whiteSpace: 'nowrap',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                }}>
                  {isDone ? '✓ done' : isRunning ? `> ${step.detail}` : step.detail}
                </div>

                {/* Running progress bar */}
                {isRunning && (
                  <div style={{
                    marginTop: 8,
                    height: 1,
                    background: 'var(--border-1)',
                    borderRadius: 99,
                    overflow: 'hidden',
                  }}>
                    <div style={{
                      height: '100%',
                      width: '40%',
                      background: 'var(--text-0)',
                      borderRadius: 99,
                      animation: 'scan-line 2s linear infinite',
                    }} />
                  </div>
                )}
              </div>

              {/* Connector */}
              {i < STEPS.length - 1 && (
                <div style={{
                  width: 24,
                  height: 1,
                  flexShrink: 0,
                  background: isDone ? 'var(--border-2)' : 'var(--border-0)',
                  transition: 'background 0.4s',
                }} />
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}