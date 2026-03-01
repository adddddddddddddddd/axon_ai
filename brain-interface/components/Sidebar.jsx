'use client'

import { useState } from 'react'
import { EXPERIMENTS } from '@/lib/data'

export default function Sidebar({ onExport, onNewRun }) {
  const [collapsed, setCollapsed]     = useState(false)
  const [activeExp, setActiveExp]     = useState('RUN-004')

  return (
    <>
      <aside style={{
        width: collapsed ? 48 : 220,
        flexShrink: 0,
        background: 'var(--surface)',
        borderRight: '1px solid var(--border)',
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden',
        transition: 'width 0.25s ease',
      }}>

        {/* Header */}
        <div style={{
          height: 48,
          display: 'flex',
          alignItems: 'center',
          padding: '0 14px',
          borderBottom: '1px solid var(--border)',
          gap: 10,
          flexShrink: 0,
        }}>
          {!collapsed && (
            <span style={{ fontWeight: 600, fontSize: 13, color: 'var(--text-primary)', whiteSpace: 'nowrap' }}>
              Neural<span style={{ color: 'var(--accent)' }}>Prep</span>
            </span>
          )}
          <button
            onClick={() => setCollapsed(v => !v)}
            style={{
              marginLeft: collapsed ? 0 : 'auto',
              width: 24, height: 24,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              border: 'none', background: 'none',
              color: 'var(--text-tertiary)', cursor: 'pointer',
              borderRadius: 'var(--r-sm)',
            }}
          >
            {collapsed
              ? <ChevronRight size={13} />
              : <ChevronLeft  size={13} />}
          </button>
        </div>

        {/* Experiment list */}
        <div style={{ flex: 1, overflowY: 'auto', paddingBottom: 8 }}>
          {!collapsed && (
            <div style={{
              fontSize: 10, fontWeight: 500, color: 'var(--text-disabled)',
              letterSpacing: '0.5px', textTransform: 'uppercase',
              padding: '14px 14px 6px',
            }}>
              Expériences
            </div>
          )}

          {EXPERIMENTS.map(exp => (
            <div
              key={exp.id}
              onClick={() => setActiveExp(exp.id)}
              style={{
                padding: '7px 14px',
                display: 'flex',
                alignItems: 'center',
                gap: 9,
                cursor: 'pointer',
                background: activeExp === exp.id ? 'var(--accent-soft)' : 'transparent',
                borderLeft: activeExp === exp.id ? '2px solid var(--accent)' : '2px solid transparent',
                transition: 'background 0.12s',
                position: 'relative',
              }}
            >
              <StatusDot status={exp.status} />
              {!collapsed && (
                <>
                  <div style={{ overflow: 'hidden', minWidth: 0, flex: 1 }}>
                    <div style={{
                      fontFamily: 'var(--font-mono)', fontSize: 9, fontWeight: 500,
                      color: activeExp === exp.id ? 'var(--accent)' : 'var(--text-secondary)',
                    }}>
                      {exp.id}
                    </div>
                    <div style={{
                      fontSize: 10, color: 'var(--text-tertiary)',
                      whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis',
                      marginTop: 1,
                    }}>
                      {exp.file}
                    </div>
                  </div>
                  <span style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-disabled)', flexShrink: 0 }}>
                    {exp.time}
                  </span>
                </>
              )}
            </div>
          ))}
        </div>

        {/* Footer */}
        <div style={{ padding: '12px 14px', borderTop: '1px solid var(--border)', flexShrink: 0, display: 'flex', flexDirection: 'column', gap: 6 }}>
          {/* New run */}
          <button
            onClick={onNewRun}
            style={{
              width: '100%',
              display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 7,
              padding: collapsed ? '8px' : '8px 0',
              background: 'none',
              color: 'var(--accent)',
              border: '1px solid var(--accent-mid)',
              borderRadius: 'var(--r)',
              fontFamily: 'var(--font-sans)',
              fontSize: 12, fontWeight: 500,
              cursor: 'pointer',
              whiteSpace: 'nowrap', overflow: 'hidden',
              transition: 'background 0.15s',
            }}
          >
            <PlusIcon />
            {!collapsed && <span>New run</span>}
          </button>

          {/* Export */}
          <button
            onClick={onExport}
            style={{
              width: '100%',
              display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 7,
              padding: collapsed ? '8px' : '8px 0',
              background: 'var(--accent)',
              color: 'white',
              border: 'none',
              borderRadius: 'var(--r)',
              fontFamily: 'var(--font-sans)',
              fontSize: 12, fontWeight: 500,
              cursor: 'pointer',
              whiteSpace: 'nowrap', overflow: 'hidden',
            }}
          >
            <DownloadIcon size={13} />
            {!collapsed && <span>Export results</span>}
          </button>
        </div>
      </aside>
    </>
  )
}

// ── Small inline icons ────────────────────────────────────────
function ChevronLeft({ size = 14 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 14 14" fill="none">
      <path d="M9 2L4 7l5 5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  )
}
function ChevronRight({ size = 14 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 14 14" fill="none">
      <path d="M5 2l5 5-5 5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  )
}
function DownloadIcon({ size = 13 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 13 13" fill="none">
      <path d="M6.5 1v7M4 6l2.5 2.5L9 6M2 10.5h9" stroke="white" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  )
}

function PlusIcon() {
  return (
    <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
      <path d="M6 1v10M1 6h10" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round"/>
    </svg>
  )
}

function StatusDot({ status }) {
  const colors = { running: 'var(--accent)', done: 'var(--text-disabled)', error: 'var(--warn)' }
  return (
    <div style={{
      width: 6, height: 6, borderRadius: '50%',
      background: colors[status],
      flexShrink: 0,
      animation: status === 'running' ? 'blink 1.8s ease infinite' : 'none',
    }} />
  )
}