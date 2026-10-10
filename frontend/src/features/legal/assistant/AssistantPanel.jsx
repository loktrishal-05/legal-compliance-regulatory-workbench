import { useEffect, useId, useMemo, useRef, useState } from 'react'
import { Link } from 'react-router'
import { Icon } from '../../../components/ui.jsx'
import { useRequest, useResource } from '../../../hooks/useApi.js'
import { LegalProblem, WorkspaceProvider } from '../shared/LegalShared.jsx'
import { useWorkspace } from '../shared/workspace.js'
import { citationHref, legalPaths, locatorLabel } from '../shared/legalApi.js'
import { answerState, categoryLabel } from './assistantModel.js'
import VoiceControls from './VoiceControls.jsx'
import './assistant.css'

const HELP_SUGGESTIONS = ['How do I upload a document?', 'How does independent review work?', 'Why is my upload quarantined?']
const DOCUMENT_SUGGESTIONS = ['Which clause sets the payment deadline?', 'Who may terminate the agreement?', 'What notice period applies?']

export function AssistantAvatar({ size = 40 }) {
  return <span className="assistant-avatar" style={{ '--size': `${size}px` }} aria-hidden="true">
    <img src="/assets/branding/agents/research-assistant.webp" alt="" width={size} height={size} decoding="async" /></span>
}

function Answer({ answer, help = false, onNavigate }) {
  if (!answer) return null
  const state = answerState(answer)
  return <div className="assistant-answer">
    <p className="assistant-state" data-tone={state.tone}>{state.label}</p>
    {help ? <><p className="assistant-prose">{answer.answer}</p>
      {answer.status === 'degraded' && <p className="assistant-caution">Guide excerpts are shown because the help model is unavailable or its output was rejected.</p>}
      {!!answer.citations?.length && <ul className="assistant-citations">{answer.citations.map(c => <li key={c.section_id}>
        <Link to={c.href || '/app/help'} onClick={onNavigate}>{c.title}</Link>
        {c.document_status === 'draft_not_in_force' && <span className="assistant-draft"> draft, not in force</span>}
        <details><summary>Exact guide section</summary><blockquote className="assistant-prose">{c.quote}</blockquote></details>
      </li>)}</ul>}</> : <>
      {(answer.statements || []).map((statement, index) => <div className="assistant-statement" key={index}>
        <p className="assistant-category">{categoryLabel(statement.category)}</p>
        <p className="assistant-prose">{statement.text}</p>
        <ul className="assistant-citations">{(statement.citations || []).map((c, n) => <li key={`${c.span_id}-${n}`}>
          {citationHref(c) ? <Link to={citationHref(c)} onClick={onNavigate}>Open source · {locatorLabel(c.locator)}</Link> : <span>Source unavailable</span>}
        </li>)}</ul>
      </div>)}
      {(answer.uncertainties || []).length > 0 && <div className="assistant-caution"><h4>Uncertainty</h4><ul>{answer.uncertainties.map(value => <li key={value}>{value.replaceAll('_', ' ')}</li>)}</ul></div>}
      {(answer.missing_information || []).map(value => <p key={value}>{value}</p>)}
      {!answer.statements?.length && <p>No supported source statement was returned. Try a more specific question or check your document access.</p>}
    </>}
  </div>
}

// Chat log: question bubbles on the right, cited answers beside the assistant avatar. Scrolls to the newest turn.
function Conversation({ turns, pending, help, onNavigate, suggestions, onSuggest, intro }) {
  const end = useRef(null)
  useEffect(() => { end.current?.scrollIntoView?.({ block: 'nearest' }) }, [turns.length, pending])
  return <div className="assistant-log" role="log" aria-label={help ? 'Help conversation' : 'Cited conversation answers'} aria-live="polite" aria-relevant="additions text">
    {!turns.length && !pending && <div className="assistant-welcome">
      <AssistantAvatar size={64} />
      <p className="assistant-welcome-title">{intro.title}</p>
      <p className="muted">{intro.body}</p>
      <ul className="assistant-suggestions">{suggestions.map(text => <li key={text}><button type="button" onClick={() => onSuggest(text)}>{text}</button></li>)}</ul>
    </div>}
    {turns.map((turn, index) => <article className="assistant-turn" key={index}>
      <p className="assistant-bubble"><span className="visually-hidden">You asked: </span>{turn.question}</p>
      <div className="assistant-reply"><AssistantAvatar size={30} /><Answer answer={turn.answer} help={help} onNavigate={onNavigate} /></div>
    </article>)}
    {pending && <article className="assistant-turn"><p className="assistant-bubble">{pending}</p>
      <div className="assistant-reply"><AssistantAvatar size={30} /><p className="assistant-typing" role="status"><span /><span /><span /><span className="visually-hidden">Getting a cited response</span></p></div></article>}
    <span ref={end} />
  </div>
}

function Composer({ question, setQuestion, onSubmit, loading, help, answerText }) {
  const id = useId()
  const max = help ? 1200 : 2000
  return <form className="assistant-composer" onSubmit={onSubmit}>
    <label htmlFor={id} className="visually-hidden">{help ? 'Ask how to use the application' : 'Ask about permitted documents'}</label>
    <div className="assistant-input">
      <textarea id={id} rows={2} value={question} maxLength={max} required
        onChange={event => setQuestion(event.target.value)}
        onKeyDown={event => { if (event.key === 'Enter' && !event.shiftKey && !event.nativeEvent.isComposing) { event.preventDefault(); event.currentTarget.form.requestSubmit() } }}
        placeholder={help ? 'Ask how to use the application…' : 'Ask about your permitted documents…'} />
      <button type="submit" className="assistant-send" disabled={loading || !question.trim()} aria-label={loading ? 'Sending' : 'Send question'}><Icon name="send" size={18} /></button>
    </div>
    <p className="assistant-fineprint">{help ? 'Uses only the public user guide and terms draft. It cannot read your documents or give legal advice.' : 'Deterministic source matches, not legal conclusions. Open and verify every citation.'} Enter sends · Shift+Enter adds a line.</p>
    <details className="assistant-more"><summary>Voice options</summary>
      <VoiceControls answerText={answerText} onTranscript={value => setQuestion(value.slice(0, max))} /></details>
  </form>
}

function HelpTab({ onNavigate }) {
  const [question, setQuestion] = useState('')
  const [turns, setTurns] = useState([])
  const [pending, setPending] = useState('')
  const request = useRequest()
  async function submit(event) {
    event.preventDefault()
    const asked = question.trim()
    setPending(asked)
    const answer = await request.run('/v1/help/chat', { method: 'POST', body: { question: asked } })
    setPending('')
    if (answer) { setTurns(value => [...value, { question: asked, answer }]); setQuestion('') }
  }
  return <>
    <Conversation turns={turns} pending={pending} help onNavigate={onNavigate} suggestions={HELP_SUGGESTIONS} onSuggest={setQuestion}
      intro={{ title: 'How can I help?', body: 'Ask how to use the platform. Answers quote the user guide and link to the exact section.' }} />
    {request.error && (request.error.status === 429 ? <p role="alert" className="assistant-caution">Too many help requests. Wait one minute, then try again.</p> : <LegalProblem error={request.error} what="application help" />)}
    <Composer question={question} setQuestion={setQuestion} onSubmit={submit} loading={request.loading} help answerText={turns.at(-1)?.answer?.answer || ''} />
  </>
}

function DocumentTab({ onNavigate }) {
  const { workspace, status, error } = useWorkspace()
  const paths = useMemo(() => workspace ? legalPaths(workspace.workspace_id) : null, [workspace])
  const conversations = useResource(paths?.conversations)
  const request = useRequest()
  const history = useRequest()
  const [question, setQuestion] = useState('')
  const [pending, setPending] = useState('')
  const [matter, setMatter] = useState('')
  const [conversationId, setConversationId] = useState('')
  const [turns, setTurns] = useState([])
  const questionId = useId()
  const matterId = useId()

  async function load(id) {
    request.reset()
    setConversationId(id)
    if (!id) { setTurns([]); setMatter(''); return }
    const value = await history.run(`${paths.conversations}/${encodeURIComponent(id)}`)
    if (value) { setTurns(value.messages || []); setMatter(value.matter_id || '') }
    else setTurns([])
  }

  async function startConversation() {
    const value = await history.run(paths.conversations, { method: 'POST', body: { matter_id: matter.trim() || null } })
    if (value) { setConversationId(value.conversation_id); conversations.refresh(); setTurns([]); request.reset() }
    return value?.conversation_id
  }

  async function submit(event) {
    event.preventDefault()
    const id = conversationId || await startConversation()
    if (!id) return
    const submitted = question.trim()
    setPending(submitted)
    const answer = await request.run(paths.assistant, { method: 'POST', body: { question: submitted,
      matter_id: matter.trim() || null, conversation_id: id } })
    setPending('')
    if (answer) { setTurns(value => [...value, { question: submitted, answer }]); setQuestion('') }
  }

  async function remove() {
    if (!conversationId) return
    const deleted = await history.run(`${paths.conversations}/${encodeURIComponent(conversationId)}`, { method: 'DELETE' })
    if (deleted) { setConversationId(''); setTurns([]); request.reset(); conversations.refresh() }
  }

  if (error) return <LegalProblem error={error} what="workspace" />
  if (status !== 'ready') return <p role="status" className="assistant-status">Loading permitted workspaces…</p>
  if (!workspace) return <p className="assistant-status">No permitted workspace is available. Application Help remains available in the other tab.</p>
  const latest = turns.at(-1)?.answer
  return <>
    <details className="assistant-more assistant-settings"><summary>Conversation · {workspace.name}{conversationId ? ` · ${conversationId.slice(0, 8)}` : ' · new'}</summary>
      <div className="assistant-history-controls">
        <label htmlFor={questionId}>Conversation<select id={questionId} value={conversationId} onChange={event => load(event.target.value)} disabled={history.loading || request.loading}>
          <option value="">New conversation</option>
          {(conversations.data?.items || []).map(c => <option value={c.conversation_id} key={c.conversation_id}>Conversation {c.conversation_id.slice(0, 8)}</option>)}
        </select></label>
        <label htmlFor={matterId}>Matter UUID (optional)<input id={matterId} value={matter} disabled={Boolean(conversationId)}
          onChange={event => setMatter(event.target.value)} placeholder="Leave empty for workspace scope" /></label>
        <div className="assistant-history-actions"><button type="button" className="button" disabled={history.loading || request.loading} onClick={() => load('')}>New conversation</button>
          <button type="button" className="button" disabled={!conversationId || history.loading || request.loading} onClick={remove}>Delete history</button>
          <Link to="/app/legal/documents" onClick={onNavigate}>Change workspace</Link></div>
      </div>
      <p className="assistant-fineprint">History is scoped to your account and workspace/matter, rechecked on every read, and never used as legal evidence. Legal hold can block deletion.</p>
    </details>
    {conversations.error && <LegalProblem error={conversations.error} what="conversation list" />}
    {history.loading && <p role="status" className="assistant-status">Updating conversation…</p>}
    {history.error && <LegalProblem error={history.error} what="conversation" />}
    <Conversation turns={turns} pending={pending} onNavigate={onNavigate} suggestions={DOCUMENT_SUGGESTIONS} onSuggest={setQuestion}
      intro={{ title: 'Ask your documents', body: `Answers come only from documents you can open in ${workspace.name}, each statement linked to its exact source.` }} />
    {request.error && <LegalProblem error={request.error} what="document answer" />}
    <Composer question={question} setQuestion={setQuestion} onSubmit={submit} loading={request.loading || history.loading}
      answerText={(latest?.statements || []).map(s => s.text).join('\n')} />
  </>
}

export default function AssistantPanel({ onNavigate, loadWorkspaceForDocuments = false, compact = false }) {
  const [tab, setTab] = useState('help')
  const { workspace } = useWorkspace()
  const id = useId()
  const buttons = useRef([])
  function move(event, index) {
    if (!['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(event.key)) return
    event.preventDefault()
    const next = event.key === 'Home' ? 0 : event.key === 'End' ? 1 : index === 0 ? 1 : 0
    setTab(next === 0 ? 'help' : 'documents')
    buttons.current[next]?.focus()
  }
  return <div className={`assistant-panel${compact ? ' is-compact' : ''}`}>
    <div className="assistant-tabs" role="tablist" aria-label="Assistant scope">
      {[['help', 'Help'], ['documents', 'Ask my documents']].map(([value, label], index) => <button type="button" key={value}
        ref={element => { buttons.current[index] = element }} role="tab" id={`${id}-tab-${value}`} aria-selected={tab === value}
        aria-controls={`${id}-panel-${value}`} tabIndex={tab === value ? 0 : -1} onClick={() => setTab(value)} onKeyDown={event => move(event, index)}>{label}</button>)}
    </div>
    <div role="tabpanel" id={`${id}-panel-${tab}`} aria-labelledby={`${id}-tab-${tab}`} className="assistant-tab-content">
      {tab === 'help' ? <HelpTab onNavigate={onNavigate} /> : loadWorkspaceForDocuments
        ? <WorkspaceProvider><DocumentTab onNavigate={onNavigate} /></WorkspaceProvider>
        : <DocumentTab key={workspace?.workspace_id || 'none'} onNavigate={onNavigate} />}
    </div>
  </div>
}
