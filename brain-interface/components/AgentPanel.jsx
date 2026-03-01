'use client'

import { useEffect, useRef, useState } from 'react'

const THOUGHTS = [
  { t: 0,    text: 'Loaded sub-01_task-rest_eeg.edf — 64 channels, 256 Hz, 180s duration.' },
  { t: 1200, text: 'Impedance check passed. Mean electrode impedance: 4.2 kΩ. All channels within acceptable range.' },
  { t: 2800, text: 'Applying bandpass filter [1–40 Hz]. Butterworth order 4. Notch at 50 Hz (power line).' },
  { t: 4200, text: 'Filter applied. SNR improved from 14.2 dB to 22.7 dB. Proceeding to ICA decomposition.' },
  { t: 6000, text: 'Running FastICA on 64 components. Convergence in 47 iterations (tol=1e-4).' },
  { t: 8500, text: 'ICA complete. Identified 3 artifact components via MARA classifier:' },
  { t: 9000, text: '  · IC001 — ocular artifact (blink pattern, Fp1/Fp2 loading: 0.91)' },
  { t: 9400, text: '  · IC002 — ocular artifact (lateral eye movement, Fp1-Fp2 asymmetry)' },
  { t: 9800, text: '  · IC023 — cardiac artifact (QRS morphology, correlation r=0.87)' },
  { t: 11000, text: 'Removing 3 components. Reconstructing clean signal in sensor space.' },
  { t: 13000, text: 'Artifact removal complete. Residual muscle artifact in channels T7, T8 — below threshold, kept.' },
  { t: 15000, text: 'Epoching: −200ms to 800ms around stimulus onset. 312 epochs extracted.' },
  { t: 17000, text: 'Baseline correction applied [−200ms to 0ms]. Epoch rejection: 4 epochs dropped (amplitude > 120μV).' },
  { t: 19000, text: 'Extracting features for vision pipeline: ERN, P300 latency, alpha power topography.' },
  { t: 21000, text: 'Export ready. Feature tensor shape: [308, 64, 256]. Saving to /outputs/sub-01_features.npy' },
]

const JOURNAL = [
  {
    id: 'RUN-004',
    status: 'running',
    file: 'sub-01_task-rest_eeg.edf',
    started: '14:32:07',
    conclusion: null,
  },
  {
    id: 'RUN-003',
    status: 'done',
    file: 'sub-01_task-motor_eeg.edf',
    started: '13:58:22',
    conclusion: 'Clean signal. 2 ICA components removed (ocular). 289/291 epochs retained. Feature quality: high.',
  },
  {
    id: 'RUN-002',
    status: 'done',
    file: 'sub-02_task-rest_eeg.edf',
    started: '13:21:44',
    conclusion: 'High muscle artifact in temporal channels. 5 ICA components removed. 201/310 epochs retained. Quality: moderate — flagged for review.',
  },
  {
    id: 'RUN-001',
    status: 'error',
    file: 'sub-03_task-rest_eeg.edf',
    started: '12:47:03',
    conclusion: 'ICA failed to converge after 500 iterations. Suspected channel disconnection. File skipped.',
  },
]

function Cursor() {
  const [v, setV] = useState(true)
  useEffect(() => {
    const t = setInterval(() => setV(x => !x), 530)
    return () => clearInterval(t)
  }, [])
  return <span style={{ opacity: v ? 1 : 0, color: 'var(--text-0)' }}>█</span>
}

function StatusDot({ status }) {
  const colors = {
    running: 'var(--text-0)',
    done:    'var(--text-3)',
    error:   'var(--error)',
  }
  return (
    <div style={{
      width: 5, height: 5,
      borderRadius: '50%',
      background: colors[status],
      flexShrink: 0,
      boxShadow: status === 'running' ? '0 0 6px var(--text-0)' : 'none',
    }} />
  )
}

export default function AgentPanel() {
  const logRef = useRef(null)
  const [visibleThoughts, setVisibleThoughts] = useState([])

  useEffect(() => {
    const timers = THOUGHTS.map(({ t, text }) =>
      setTimeout(() => {
        setVisibleThoughts(v => [...v, text])
      }, t)
    )
    return () => timers.forEach(clearTimeout)
  }, [])

  useEffect(() => {
    if (logRef.current) {
      logRef.current.scrollTop = logRef.current.scrollHeight
    }
  }, [visibleThoughts])

  return (
    <div style={{
      display: 'flex',
      borderTop: '1px solid var(--border-1)',
      height: '100%',
      background: 'var(--bg-1)',
    }}>

      {/* LEFT — Agent Thoughts */}
      <div style={{
        flex: 1,
        display: 'flex',
        flexDirection: 'column',
        borderRight: '1px solid var(--border-1)',
        overflow: 'hidden',
      }}>
        <PanelHeader label="AGENT REASONING" live />
        <div
          ref={logRef}
          style={{
            flex: 1,
            overflowY: 'auto',
            padding: '12px 20px',
            display: 'flex',
            flexDirection: 'column',
            gap: 2,
          }}
        >
          {visibleThoughts.map((line, i) => (
            <div
              key={i}
              style={{
                fontSize: 10,
                lineHeight: 1.7,
                color: i === visibleThoughts.length - 1 ? 'var(--text-1)' : 'var(--text-2)',
                animation: 'fade-up 0.3s ease',
                fontFamily: 'var(--font)',
                letterSpacing: 0.3,
              }}
            >
              <span style={{ color: 'var(--text-4)', marginRight: 8 }}>&gt;</span>
              {line}
              {i === visibleThoughts.length - 1 && <Cursor />}
            </div>
          ))}
          {visibleThoughts.length === 0 && (
            <div style={{ fontSize: 10, color: 'var(--text-4)', fontStyle: 'italic' }}>
              Waiting for agent...
            </div>
          )}
        </div>
      </div>

      {/* RIGHT — Experiment Journal */}
      <div style={{
        width: 360,
        flexShrink: 0,
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden',
      }}>
        <PanelHeader label="EXPERIMENT LOG" />
        <div style={{
          flex: 1,
          overflowY: 'auto',
          padding: '10px 16px',
          display: 'flex',
          flexDirection: 'column',
          gap: 6,
        }}>
          {JOURNAL.map((run) => (
            <div
              key={run.id}
              style={{
                padding: '10px 12px',
                border: `1px solid ${run.status === 'running' ? 'var(--border-2)' : 'var(--border-0)'}`,
                borderRadius: 'var(--r-md)',
                background: run.status === 'running' ? 'var(--bg-3)' : 'transparent',
                animation: run.status === 'running' ? 'fade-up 0.4s ease' : 'none',
              }}
            >
              {/* Run header */}
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
                <StatusDot status={run.status} />
                <span style={{
                  fontSize: 9,
                  fontWeight: 600,
                  letterSpacing: 2,
                  color: run.status === 'running'
                    ? 'var(--text-0)'
                    : run.status === 'error'
                    ? 'var(--error)'
                    : 'var(--text-2)',
                }}>
                  {run.id}
                </span>
                <span style={{ fontSize: 9, color: 'var(--text-4)', marginLeft: 'auto' }}>
                  {run.started}
                </span>
              </div>

              {/* File */}
              <div style={{
                fontSize: 9,
                color: 'var(--text-3)',
                marginBottom: run.conclusion ? 6 : 0,
                letterSpacing: 0.3,
              }}>
                {run.file}
              </div>

              {/* Conclusion */}
              {run.conclusion && (
                <div style={{
                  fontSize: 9,
                  color: run.status === 'error' ? 'rgba(255,77,77,0.7)' : 'var(--text-2)',
                  lineHeight: 1.6,
                  borderTop: '1px solid var(--border-0)',
                  paddingTop: 6,
                  letterSpacing: 0.2,
                }}>
                  {run.conclusion}
                </div>
              )}

              {/* Running indicator */}
              {run.status === 'running' && (
                <div style={{
                  marginTop: 8,
                  height: 1,
                  background: 'var(--border-1)',
                  borderRadius: 99,
                  overflow: 'hidden',
                }}>
                  <div style={{
                    height: '100%',
                    width: '30%',
                    background: 'var(--text-0)',
                    borderRadius: 99,
                    animation: 'scan-line 1.8s linear infinite',
                  }} />
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

function PanelHeader({ label, live }) {
  const [tick, setTick] = useState(true)
  useEffect(() => {
    if (!live) return
    const t = setInterval(() => setTick(v => !v), 900)
    return () => clearInterval(t)
  }, [live])

  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      gap: 8,
      padding: '8px 16px',
      borderBottom: '1px solid var(--border-0)',
      flexShrink: 0,
    }}>
      {live && (
        <div style={{
          width: 5, height: 5, borderRadius: '50%',
          background: 'var(--text-0)',
          opacity: tick ? 1 : 0.2,
          transition: 'opacity 0.3s',
        }} />
      )}
      <span style={{ fontSize: 9, letterSpacing: 3, color: 'var(--text-3)', fontWeight: 600 }}>
        {label}
      </span>
    </div>
  )
}