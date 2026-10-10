import { useEffect, useId, useRef, useState } from 'react'
import { Icon } from '../../../components/ui.jsx'
import AssistantPanel, { AssistantAvatar } from './AssistantPanel.jsx'
import { nextFocusIndex } from './assistantModel.js'

function AssistantDialog({ onClose }) {
  const dialog = useRef(null)
  const titleId = useId()
  useEffect(() => {
    const previous = document.activeElement
    dialog.current.showModal()
    dialog.current.querySelector('textarea')?.focus()
    const node = dialog.current
    return () => { node.close(); previous?.focus?.() }
  }, [])
  function trap(event) {
    if (event.key === 'Escape') { event.preventDefault(); onClose(); return }
    if (event.key !== 'Tab') return
    const focusable = [...dialog.current.querySelectorAll('button:not(:disabled), a[href], input:not(:disabled), select:not(:disabled), textarea:not(:disabled), summary, [tabindex="0"]')]
      .filter(element => element.tabIndex >= 0 && element.getClientRects().length)
    const index = focusable.indexOf(document.activeElement)
    if (index < 0 || event.shiftKey && index === 0 || !event.shiftKey && index === focusable.length - 1) {
      const next = nextFocusIndex(index, focusable.length, event.shiftKey)
      if (next !== null) { event.preventDefault(); focusable[next].focus() }
    }
  }
  return <dialog className="assistant-dialog" ref={dialog} aria-labelledby={titleId} onKeyDown={trap}
    onCancel={event => { event.preventDefault(); onClose() }}>
    <header className="assistant-dialog-heading">
      <AssistantAvatar size={44} />
      <div><h2 id={titleId}>Assistant</h2><p>Every answer cites its source · not legal advice</p></div>
      <button type="button" className="assistant-close" onClick={onClose} aria-label="Close assistant"><Icon name="close" size={18} /></button>
    </header>
    <AssistantPanel onNavigate={onClose} loadWorkspaceForDocuments compact />
  </dialog>
}

export default function AssistantLauncher() {
  const [open, setOpen] = useState(false)
  return <><button type="button" className="assistant-launcher" aria-haspopup="dialog" aria-expanded={open} onClick={() => setOpen(true)}>
    <AssistantAvatar size={40} />
    <span className="assistant-launcher-text"><strong>Assistant</strong><small>Help · cited answers</small></span></button>
    {open && <AssistantDialog onClose={() => setOpen(false)} />}</>
}
