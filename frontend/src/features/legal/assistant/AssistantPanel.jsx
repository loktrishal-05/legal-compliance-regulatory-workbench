import { useId, useMemo, useRef, useState } from 'react'
import { Link } from 'react-router'
import { useRequest, useResource } from '../../../hooks/useApi.js'
import { LegalProblem, WorkspaceProvider } from '../shared/LegalShared.jsx'
import { useWorkspace } from '../shared/workspace.js'
import { citationHref, legalPaths, locatorLabel } from '../shared/legalApi.js'
import { answerState, categoryLabel } from './assistantModel.js'
import VoiceControls from './VoiceControls.jsx'
import './assistant.css'

function Answer({ answer, help = false, onNavigate }) {
  if (!answer) return null
  const state = answerState(answer)
  return <section className="assistant-answer" aria-live="polite" aria-relevant="additions text">
    <h3>{state.label}</h3>
    {help ? <><p className="assistant-prose">{answer.answer}</p>
      {answer.status === 'degraded' && <p className="assistant-caution">Guide excerpts are shown because the help model is unavailable or its output was rejected.</p>}
      {!!answer.citations?.length && <ul className="assistant-citations">{answer.citations.map(c => <li key={c.section_id}>
        <Link to={c.href || '/app/help'} onClick={onNavigate}>{c.title}</Link>
        {c.document_status === 'draft_not_in_force' && <span> — draft, not in force</span>}
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
  </section>
}

function QuestionForm({ question, setQuestion, onSubmit, loading, help, answerText }) {
  const id = useId()
  return <form className="assistant-question" onSubmit={onSubmit}>
    <label htmlFor={id}>{help ? 'Ask how to use the application' : 'Ask about permitted documents'}</label>
    <textarea id={id} rows={3} value={question} maxLength={help ? 1200 : 2000} required
      onChange={event => setQuestion(event.target.value)} placeholder={help ? 'How do I upload a document?' : 'Which source mentions the invoice deadline?'} />
    <p className="muted small">{help ? 'Help uses only the public user guide and terms draft. It cannot read your documents or give legal advice.' : 'Answers are deterministic source matches, not accepted legal conclusions. Open and verify every citation.'}</p>
    <button className="button primary" type="submit" disabled={loading || !question.trim()}>{loading ? 'Getting cited response…' : 'Send question'}</button>
    <VoiceControls answerText={answerText} onTranscript={value => setQuestion(value.slice(0, help ? 1200 : 2000))} />
  </form>
}

function HelpTab({ onNavigate }) {
  const [question, setQuestion] = useState('')
  const request = useRequest()
  async function submit(event) {
    event.preventDefault()
    await request.run('/v1/help/chat', { method: 'POST', body: { question: question.trim() } })
  }
  return <><QuestionForm question={question} setQuestion={setQuestion} onSubmit={submit} loading={request.loading}
    help answerText={request.data?.answer || ''} />
    {request.error && (request.error.status === 429 ? <p role="alert">Too many help requests. Wait one minute, then try again.</p> : <LegalProblem error={request.error} what="application help" />)}
    <Answer answer={request.data} help onNavigate={onNavigate} />
  </>
}

function DocumentTab({ onNavigate }) {
  const { workspace, status, error } = useWorkspace()
  const paths = useMemo(() => workspace ? legalPaths(workspace.workspace_id) : null, [workspace])
  const conversations = useResource(paths?.conversations)
  const request = useRequest()
  const history = useRequest()
  const [question, setQuestion] = useState('')
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
    const answer = await request.run(paths.assistant, { method: 'POST', body: { question: submitted,
      matter_id: matter.trim() || null, conversation_id: id } })
    if (answer) { setTurns(value => [...value, { question: submitted, answer }]); setQuestion('') }
  }

  async function remove() {
    if (!conversationId) return
    const deleted = await history.run(`${paths.conversations}/${encodeURIComponent(conversationId)}`, { method: 'DELETE' })
    if (deleted) { setConversationId(''); setTurns([]); request.reset(); conversations.refresh() }
  }

  if (error) return <LegalProblem error={error} what="workspace" />
  if (status !== 'ready') return <p role="status">Loading permitted workspaces…</p>
  if (!workspace) return <p>No permitted workspace is available. Application Help remains available in the other tab.</p>
  const latest = turns.at(-1)?.answer
  return <>
    <p className="muted small">Workspace: <strong>{workspace.name}</strong>. <Link to="/app/legal/documents" onClick={onNavigate}>Change workspace in the Legal area</Link>.</p>
    <div className="assistant-history-controls">
      <label htmlFor={questionId}>Conversation<select id={questionId} value={conversationId} onChange={event => load(event.target.value)} disabled={history.loading || request.loading}>
        <option value="">New conversation</option>
        {(conversations.data?.items || []).map(c => <option value={c.conversation_id} key={c.conversation_id}>Conversation {c.conversation_id.slice(0, 8)}</option>)}
      </select></label>
      <label htmlFor={matterId}>Matter UUID (optional)<input id={matterId} value={matter} disabled={Boolean(conversationId)}
        onChange={event => setMatter(event.target.value)} placeholder="Leave empty for workspace scope" /></label>
      <div className="assistant-history-actions"><button type="button" className="button" disabled={history.loading || request.loading} onClick={() => load('')}>New conversation</button>
        <button type="button" className="button" disabled={!conversationId || history.loading || request.loading} onClick={remove}>Delete history</button></div>
    </div>
    <p className="muted small">History is scoped to your account and workspace/matter, rechecked on every read, and never used as legal evidence. Legal hold can block deletion.</p>
    {conversations.error && <LegalProblem error={conversations.error} what="conversation list" />}
    {history.loading && <p role="status">Updating conversation…</p>}
    {history.error && <LegalProblem error={history.error} what="conversation" />}
    <QuestionForm question={question} setQuestion={setQuestion} onSubmit={submit} loading={request.loading || history.loading}
      answerText={(latest?.statements || []).map(s => s.text).join('\n')} />
    {request.error && <LegalProblem error={request.error} what="document answer" />}
    <div className="assistant-turns" role="log" aria-label="Cited conversation answers" aria-live="polite">
      {turns.map((turn, index) => <article className="assistant-turn" key={index}><h3>Your question</h3><p>{turn.question}</p>
        <Answer answer={turn.answer} onNavigate={onNavigate} /></article>)}
    </div>
  </>
}

export default function AssistantPanel({ onNavigate, loadWorkspaceForDocuments = false }) {
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
  return <div className="assistant-panel">
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
