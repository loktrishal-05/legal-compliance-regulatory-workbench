// Shared legal UI: workspace provider/picker, honest state components, citation link and placeholder page.
import { useCallback, useState } from 'react'
import { Link, Outlet } from 'react-router'
import { EmptyState, ErrorState, LoadingState, PageHeader, PlannedCapability } from '../../../components/ui.jsx'
import { useResource } from '../../../hooks/useApi.js'
import { citationHref, locatorLabel, problemKind, REVIEW_STATUS } from './legalApi.js'
import { WorkspaceContext, chooseWorkspace, rememberWorkspace, rememberedWorkspace, useWorkspace } from './workspace.js'

export function WorkspaceProvider({ children }) {
  const resource = useResource('/v1/workspaces')
  const [selected, setSelected] = useState(rememberedWorkspace)
  const workspaces = resource.data?.items || []
  const workspace = chooseWorkspace(workspaces, selected)
  const status = resource.error ? 'error' : resource.data ? 'ready' : 'loading'
  const select = useCallback(id => { rememberWorkspace(id); setSelected(id) }, [])
  return <WorkspaceContext.Provider value={{ workspaces, workspace, status, error: resource.error, select,
    reload: resource.refresh }}>{children}</WorkspaceContext.Provider>
}

export function WorkspacePicker() {
  const { workspaces, workspace, select, status } = useWorkspace()
  if (status !== 'ready' || workspaces.length < 2) return workspace
    ? <p className="muted small" aria-live="polite">Workspace: <strong>{workspace.name}</strong> · role {workspace.role}</p> : null
  return <label className="legal-picker">Workspace
    <select value={workspace?.workspace_id || ''} onChange={event => select(event.target.value)}>
      {workspaces.map(item => <option key={item.workspace_id} value={item.workspace_id}>{item.name} ({item.role})</option>)}
    </select></label>
}

// Layout for every /app/legal page: loads the caller's workspaces once and refuses to guess one.
export function LegalLayout() {
  return <WorkspaceProvider><LegalGate /></WorkspaceProvider>
}

function LegalGate() {
  const { status, error, workspace, reload } = useWorkspace()
  if (status === 'loading') return <LoadingState label="Loading your legal workspaces…" />
  if (status === 'error') return <LegalProblem error={error} onRetry={reload} />
  if (!workspace) return <EmptyState title="No legal workspace" message="You are not an active member of any legal workspace. A workspace administrator grants membership; the browser cannot." />
  return <><div className="toolbar legal-context"><WorkspacePicker /></div><Outlet /></>
}

// One place that turns server answers into honest states. 404 deny is shown like "not found" on purpose.
export function LegalProblem({ error, onRetry, what = 'this item' }) {
  const kind = problemKind(error)
  if (kind === 'denied') return <EmptyState title="Unavailable" message={`${what[0].toUpperCase()}${what.slice(1)} does not exist or you do not currently have access.`} />
  if (kind === 'terms') return <EmptyState title="Terms acceptance required" message="Accept the current terms to continue." />
  if (kind === 'session') return <EmptyState title="Session expired" message="Sign in again to continue." />
  if (kind === 'degraded') return <ErrorState title="Service degraded" message={`${error.message} No data is shown rather than a stale or guessed result.`} onRetry={onRetry} />
  if (kind === 'conflict') return <ErrorState title="Not applied" message={`The server refused the change (${error.data?.detail?.code || 'conflict'}). Reload to see the current state.`} onRetry={onRetry} />
  if (kind === 'busy') return <ErrorState title="Busy" message="Too many active jobs in this workspace. Try again shortly." onRetry={onRetry} />
  return <ErrorState message={error?.message} onRetry={onRetry} />
}

// Loading / error / empty wrapper for simple resource states.
export function LegalResource({ resource, empty, emptyMessage, children, what }) {
  if (resource.error) return <LegalProblem error={resource.error} onRetry={resource.refresh} what={what} />
  if (resource.loading || !resource.data) return <LoadingState label="Loading live data…" />
  const items = Array.isArray(resource.data) ? resource.data : resource.data.items
  if (items && !items.length && empty) return <EmptyState title={empty} message={emptyMessage} />
  return children(resource.data)
}

export function CitationLink({ citation, children }) {
  const href = citationHref(citation)
  const label = children || `${locatorLabel(citation?.locator)}${citation?.quote ? `: “${citation.quote.trim().slice(0, 80)}”` : ''}`
  return href ? <Link to={href} className="citation-link">{label}</Link> : <span className="muted">{label} (source not linkable)</span>
}

export function ReviewBadge({ status }) {
  return <span className={`badge review-${status || 'none'}`}>{REVIEW_STATUS[status] || status || 'Not submitted'}</span>
}


export function ComingInThisBuild({ title, owner }) {
  return <><PageHeader title={title} />
    <PlannedCapability title={title} phase="Step 8 frontend" available="The backend API for this area is implemented and tested."
      planned={`This page is being built in the current parallel build (${owner}).`} requires="No mock data is shown meanwhile." /></>
}
