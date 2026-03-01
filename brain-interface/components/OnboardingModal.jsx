'use client'

import { useState, useEffect } from 'react'

// ── Mock BIDS data ────────────────────────────────────────────
const BIDS_DATASETS = [
  { id: 'ds001', name: 'Motor Imagery', subjects: 12, tasks: ['rest', 'motor_left', 'motor_right'] },
  { id: 'ds002', name: 'Visual Oddball', subjects: 8,  tasks: ['rest', 'visual_p300'] },
  { id: 'ds003', name: 'Resting State', subjects: 24, tasks: ['rest'] },
  { id: 'ds004', name: 'N-Back Task',   subjects: 16, tasks: ['rest', 'nback_1', 'nback_2', 'nback_3'] },
]

function getSubjects(datasetId) {
  const ds = BIDS_DATASETS.find(d => d.id === datasetId)
  if (!ds) return []
  return Array.from({ length: ds.subjects }, (_, i) => ({
    id: `sub-${String(i + 1).padStart(2, '0')}`,
    label: `Subject ${String(i + 1).padStart(2, '0')}`,
  }))
}

const STEP_LABELS = ['Dataset', 'Subject', 'Task']

export default function OnboardingModal({ open, onClose, onStart }) {
  const [step,    setStep]    = useState(0)
  const [dataset, setDataset] = useState(null)
  const [subject, setSubject] = useState(null)
  const [task,    setTask]    = useState(null)
  const [visible, setVisible] = useState(false)

  useEffect(() => {
    if (open) {
      setTimeout(() => setVisible(true), 10)
    } else {
      setVisible(false)
      setTimeout(() => { setStep(0); setDataset(null); setSubject(null); setTask(null) }, 350)
    }
  }, [open])

  function handleNext() {
    if (step < 2) setStep(s => s + 1)
    else {
      const ds = BIDS_DATASETS.find(d => d.id === dataset)
      onStart({ dataset: ds, subject, task })
      onClose()
    }
  }

  function handleBack() { setStep(s => s - 1) }

  const canProceed = step === 0 ? !!dataset : step === 1 ? !!subject : !!task
  const selectedDs = BIDS_DATASETS.find(d => d.id === dataset)

  if (!open) return null

  return (
    <>
      {/* Backdrop */}
      <div
        onClick={onClose}
        style={{
          position: 'fixed', inset: 0,
          background: 'rgba(17,24,39,0.25)',
          backdropFilter: 'blur(3px)',
          zIndex: 50,
          opacity: visible ? 1 : 0,
          transition: 'opacity 0.3s ease',
        }}
      />

      {/* Modal */}
      <div style={{
        position: 'fixed',
        top: '50%', left: '50%',
        transform: visible ? 'translate(-50%, -50%)' : 'translate(-50%, -46%)',
        width: 480,
        background: 'var(--surface)',
        borderRadius: 'var(--r-lg)',
        border: '1px solid var(--border)',
        boxShadow: '0 20px 60px rgba(0,0,0,0.12), 0 4px 16px rgba(0,0,0,0.06)',
        zIndex: 51,
        opacity: visible ? 1 : 0,
        transition: 'opacity 0.3s ease, transform 0.3s ease',
        overflow: 'hidden',
      }}>

        {/* Header */}
        <div style={{
          padding: '20px 24px 16px',
          borderBottom: '1px solid var(--border)',
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        }}>
          <div>
            <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 4 }}>
              New preprocessing run
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              {STEP_LABELS.map((label, i) => (
                <div key={label} style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
                    <div style={{
                      width: 16, height: 16, borderRadius: '50%',
                      background: i < step ? 'var(--accent)' : i === step ? 'var(--accent)' : 'var(--border)',
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                      flexShrink: 0, transition: 'background 0.25s',
                    }}>
                      {i < step
                        ? <CheckIcon />
                        : <span style={{ fontFamily: 'var(--font-mono)', fontSize: 8, color: i === step ? 'white' : 'var(--text-disabled)' }}>{i + 1}</span>
                      }
                    </div>
                    <span style={{
                      fontSize: 11, fontWeight: 500,
                      color: i === step ? 'var(--text-primary)' : i < step ? 'var(--text-tertiary)' : 'var(--text-disabled)',
                      transition: 'color 0.25s',
                    }}>
                      {label}
                    </span>
                  </div>
                  {i < STEP_LABELS.length - 1 && (
                    <div style={{ width: 16, height: 1, background: i < step ? 'var(--accent)' : 'var(--border)', transition: 'background 0.25s' }} />
                  )}
                </div>
              ))}
            </div>
          </div>
          <button onClick={onClose} style={{
            width: 28, height: 28, border: '1px solid var(--border)', borderRadius: 'var(--r-sm)',
            background: 'none', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center',
            color: 'var(--text-tertiary)',
          }}>
            <CloseIcon />
          </button>
        </div>

        {/* Body */}
        <div style={{ padding: '20px 24px', minHeight: 280 }}>

          {/* STEP 0 — Dataset */}
          {step === 0 && (
            <StepFade>
              <StepTitle>Select a BIDS dataset</StepTitle>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {BIDS_DATASETS.map(ds => (
                  <SelectCard
                    key={ds.id}
                    selected={dataset === ds.id}
                    onClick={() => setDataset(ds.id)}
                  >
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ fontSize: 13, fontWeight: 500, color: 'var(--text-primary)' }}>{ds.name}</div>
                      <div style={{ fontSize: 11, color: 'var(--text-tertiary)', marginTop: 2, fontFamily: 'var(--font-mono)' }}>
                        {ds.id} · {ds.subjects} subjects · {ds.tasks.length} task{ds.tasks.length > 1 ? 's' : ''}
                      </div>
                    </div>
                    {dataset === ds.id && <SelectedDot />}
                  </SelectCard>
                ))}
              </div>
            </StepFade>
          )}

          {/* STEP 1 — Subject */}
          {step === 1 && selectedDs && (
            <StepFade>
              <StepTitle>Select a subject</StepTitle>
              <div style={{
                display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 6,
                maxHeight: 220, overflowY: 'auto', paddingRight: 4,
              }}>
                {getSubjects(dataset).map(sub => (
                  <button
                    key={sub.id}
                    onClick={() => setSubject(sub.id)}
                    style={{
                      padding: '8px 4px',
                      borderRadius: 'var(--r-sm)',
                      border: `1px solid ${subject === sub.id ? 'var(--accent-mid)' : 'var(--border)'}`,
                      background: subject === sub.id ? 'var(--accent-soft)' : 'var(--surface-2)',
                      cursor: 'pointer',
                      textAlign: 'center',
                      transition: 'all 0.15s',
                    }}
                  >
                    <div style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: subject === sub.id ? 'var(--accent)' : 'var(--text-secondary)', fontWeight: 500 }}>
                      {sub.id}
                    </div>
                  </button>
                ))}
              </div>
            </StepFade>
          )}

          {/* STEP 2 — Task */}
          {step === 2 && selectedDs && (
            <StepFade>
              <StepTitle>Select a task</StepTitle>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {selectedDs.tasks.map(t => (
                  <SelectCard
                    key={t}
                    selected={task === t}
                    onClick={() => setTask(t)}
                  >
                    <div style={{ flex: 1 }}>
                      <div style={{ fontSize: 13, fontWeight: 500, color: 'var(--text-primary)', fontFamily: 'var(--font-mono)' }}>
                        {t}
                      </div>
                      <div style={{ fontSize: 11, color: 'var(--text-tertiary)', marginTop: 2 }}>
                        {taskDescription(t)}
                      </div>
                    </div>
                    {task === t && <SelectedDot />}
                  </SelectCard>
                ))}
              </div>

              {/* Summary */}
              {task && (
                <div style={{
                  marginTop: 16, padding: '10px 12px',
                  background: 'var(--accent-soft)', border: '1px solid var(--accent-mid)',
                  borderRadius: 'var(--r)', display: 'flex', gap: 10, alignItems: 'flex-start',
                  animation: 'fadein 0.25s ease',
                }}>
                  <div style={{ fontSize: 10, color: 'var(--text-secondary)', lineHeight: 1.6 }}>
                    <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--accent)' }}>
                      {subject}
                    </span>
                    {' · '}
                    <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--text-secondary)' }}>
                      {selectedDs.name}
                    </span>
                    {' · task '}
                    <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--text-secondary)' }}>
                      {task}
                    </span>
                    {' — ready to preprocess'}
                  </div>
                </div>
              )}
            </StepFade>
          )}
        </div>

        {/* Footer */}
        <div style={{
          padding: '14px 24px',
          borderTop: '1px solid var(--border)',
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        }}>
          <button
            onClick={step === 0 ? onClose : handleBack}
            style={{
              padding: '7px 16px', border: '1px solid var(--border)', borderRadius: 'var(--r)',
              background: 'none', cursor: 'pointer', fontSize: 12, fontWeight: 500,
              color: 'var(--text-secondary)', fontFamily: 'var(--font-sans)',
              transition: 'all 0.15s',
            }}
          >
            {step === 0 ? 'Cancel' : '← Back'}
          </button>

          <button
            onClick={handleNext}
            disabled={!canProceed}
            style={{
              padding: '7px 20px', border: 'none', borderRadius: 'var(--r)',
              background: canProceed ? 'var(--accent)' : 'var(--border)',
              color: canProceed ? 'white' : 'var(--text-disabled)',
              cursor: canProceed ? 'pointer' : 'default',
              fontSize: 12, fontWeight: 500, fontFamily: 'var(--font-sans)',
              transition: 'all 0.2s',
            }}
          >
            {step === 2 ? 'Start preprocessing →' : 'Next →'}
          </button>
        </div>
      </div>
    </>
  )
}

// ── Sub-components ────────────────────────────────────────────

function StepFade({ children }) {
  return (
    <div style={{ animation: 'fadein 0.2s ease' }}>
      {children}
    </div>
  )
}

function StepTitle({ children }) {
  return (
    <div style={{ fontSize: 12, fontWeight: 500, color: 'var(--text-secondary)', marginBottom: 14, letterSpacing: '0.1px' }}>
      {children}
    </div>
  )
}

function SelectCard({ selected, onClick, children }) {
  return (
    <div
      onClick={onClick}
      style={{
        padding: '12px 14px',
        border: `1px solid ${selected ? 'var(--accent-mid)' : 'var(--border)'}`,
        borderRadius: 'var(--r)',
        background: selected ? 'var(--accent-soft)' : 'var(--surface-2)',
        cursor: 'pointer',
        display: 'flex', alignItems: 'center', gap: 12,
        transition: 'all 0.15s',
      }}
    >
      {children}
    </div>
  )
}

function SelectedDot() {
  return (
    <div style={{
      width: 16, height: 16, borderRadius: '50%',
      background: 'var(--accent)',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      flexShrink: 0,
    }}>
      <CheckIcon />
    </div>
  )
}

function CheckIcon() {
  return (
    <svg width="8" height="8" viewBox="0 0 8 8" fill="none">
      <path d="M1.5 4l2 2 3-3" stroke="white" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  )
}

function CloseIcon() {
  return (
    <svg width="11" height="11" viewBox="0 0 11 11" fill="none">
      <path d="M1 1l9 9M10 1L1 10" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round"/>
    </svg>
  )
}

function taskDescription(task) {
  const map = {
    rest:         'Eyes open, no task — 5 min resting state',
    motor_left:   'Left hand motor imagery, 80 trials',
    motor_right:  'Right hand motor imagery, 80 trials',
    visual_p300:  'Visual oddball paradigm, 300 stimuli',
    nback_1:      '1-back working memory task',
    nback_2:      '2-back working memory task',
    nback_3:      '3-back working memory task',
  }
  return map[task] || task
}