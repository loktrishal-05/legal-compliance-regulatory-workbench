import { useNavigate, useParams } from 'react-router'
import { useSession } from './session.jsx'
import { REVIEWERS } from './navigation.js'
import { AgentAvatar, EmptyState, NotFound, PageHeader } from '../components/ui.jsx'
import { ApiState, Audit, Knowledge, QueryConsole, Sovereignty } from '../WorkspacePages.jsx'
import { OperationalWorkspace } from '../OperationalPages.jsx'
import { AutomationStatus } from '../ProductPages.jsx'
import { useResource } from '../hooks/useApi.js'
import { useBackendHealth } from '../hooks/useBackendHealth.js'
import { DashboardView, GovernanceActivity, OperationalBI } from '../features/dashboard/DashboardView.jsx'
import { SensorTrends, WorkOrderBoard } from '../features/maintenance/MaintenanceView.jsx'
import { ReviewDesk } from '../features/approvals/ReviewDesk.jsx'
import { AgentsView } from '../features/agents/AgentsView.jsx'
import { ResourcesView } from '../features/resources/ResourcesView.jsx'
import { ExecutionsView } from '../features/executions/ExecutionsView.jsx'
import { PidViewer } from '../features/pid/PidViewer.jsx'
import { GapBoard, VerifiedRegistry } from '../features/knowledge/KnowledgeViews.jsx'

// Pages wrap existing, backend-connected components. Unfinished areas say so plainly; nothing is fabricated.
export function DashboardPage() {
  const { user } = useSession()
  const { status } = useBackendHealth()
  const reviewer = REVIEWERS.includes(user?.role)
  const today = new Intl.DateTimeFormat(undefined, { weekday: 'long', day: 'numeric', month: 'long' }).format(new Date())
  return <>
    <PageHeader title="Dashboard" description={`${today} · legacy platform data from the backend. These figures are not legal compliance scores.`} />
    <DashboardView user={user} health={status} />
    {reviewer && <OperationalBI />}
  </>
}

export function WorkspacePage() {
  const { user } = useSession()
  return <><PageHeader title="AI Workspace" description="Legacy governed query infrastructure. Legal specialists and legal-source authorization are not yet available." />
    <QueryConsole user={user} /></>
}

export function VoiceWorkspacePage() {
  const { user } = useSession()
  return <><PageHeader title="Voice query" description="Local speech-to-text only. Every transcript is reviewed by you before it can be submitted." />
    <QueryConsole user={user} voiceFocus /></>
}

export function AgentsPage() {
  return <><PageHeader title="Agents" description="Configured specialist routes and read-only tools reported by the backend." actions={<AgentAvatar size={56} />} />
    <AgentsView /></>
}

export function PidPage() {
  return <><PageHeader title="Legacy P&ID Intelligence" description="Industrial regression view retained during migration. As-drawn evidence only; not contract intelligence." />
    <PidViewer /></>
}

export function MaintenancePage() {
  return <><PageHeader title="Legacy Maintenance & Sensors" description="Industrial regression view with source-linked readings and work orders. Not legal compliance monitoring." />
    <section className="panel"><div className="section-heading"><h2>Sensor trends</h2><span className="muted small">Hover or use the arrow keys to read exact values</span></div><SensorTrends /></section>
    <section className="panel"><div className="section-heading"><h2>Work orders</h2></div><WorkOrderBoard /></section></>
}

const OPERATION_VIEWS = { handover: 'Shift Handover', compliance: 'Environmental Compliance', notes: 'Operator Notes' }
export function OperationsPage() {
  const { user } = useSession()
  const { view } = useParams()
  const navigate = useNavigate()
  if (!OPERATION_VIEWS[view]) return <NotFound />
  const change = label => {
    if (label === 'Knowledge Gaps') return navigate('/app/gaps')
    navigate(`/app/operations/${Object.keys(OPERATION_VIEWS).find(key => OPERATION_VIEWS[key] === label)}`)
  }
  return <><PageHeader title="Legacy Operations" description="Industrial handover and environmental workflows retained for regression. Legal compliance assurance is not yet available." />
    <OperationalWorkspace user={user} view={OPERATION_VIEWS[view]} onViewChange={change} /></>
}

export function KnowledgePage() {
  return <><PageHeader title="Knowledge" description="Retrieve cited evidence from locally indexed documents, and review the verified knowledge registry." />
    <Knowledge />
    <VerifiedRegistry /></>
}

export function GapsPage() {
  return <><PageHeader title="Knowledge Gaps" description="Evidence gaps recorded by governed runs. Resolving a gap requires verified knowledge or an authoritative source." />
    <GapBoard /></>
}

export function ApprovalsPage() {
  const { user } = useSession()
  return <><PageHeader title="Approvals" description="Existing review infrastructure releases advisory output only. Legal findings and scoped reviewer permissions arrive in later phases." />
    <ReviewDesk user={user} /></>
}

export function ExecutionsPage() {
  return <><PageHeader title="Durable executions" description="Checkpointed graph runs you own; administrators see all. No reasoning traces are stored or shown." />
    <ExecutionsView /></>
}

export function AuditPage() {
  return <><PageHeader title="Audit" description="Tamper-evident, not tamper-proof: modification of the recorded chain is detectable." />
    <section className="panel"><div className="section-heading"><h2>Activity</h2></div><GovernanceActivity /></section><Audit /></>
}

export function SovereigntyPage() {
  const proof = useResource('/sovereignty/proof')
  return <><PageHeader title="Private runtime" description="Configuration and process observations, not a deployment attestation. Offline-capable, not automatically air-gapped." /><Sovereignty proof={proof} /></>
}

const POLICY = [
  ['AIKosh', 'Resource registry', 'Downloaded resources need provenance, licence, a named approver and a pinned SHA-256 before local approval.'],
  ['BHASHINI', 'Public data only · disabled for confidential data', 'Off by default. No BHASHINI client ships in this build.'],
  ['data.gov.in', 'Optional public connector', 'Requires public deployment mode, the feature flag and an explicitly public request. Never receives plant data.'],
  ['API Setu', 'Interface-ready', 'No live integration is claimed.'],
  ['DigiLocker', 'Evaluated · future', 'Not part of confidential inference.'],
]
export function ResourcesPage() {
  const status = useResource('/product/status')
  const resources = status.data?.language_resources || []
  return <><PageHeader title="Government Resources" description="Classification is enforced by the server. Confidential data may only use LOCAL_APPROVED resources." />
    <section className="panel"><h2>Policy</h2><ul className="policy-list">{POLICY.map(([name, state, note]) => <li key={name}><strong>{name}</strong><span className="badge">{state}</span><p>{note}</p></li>)}</ul></section>
    <section className="panel"><h2>Language resources reported by this Workbench</h2><ApiState request={status} />
      {resources.length ? <div className="table-scroll" tabIndex={0} role="region" aria-label="Language resources"><table><thead><tr><th>Resource</th><th>Provider</th><th>Classification</th><th>Confidential data</th></tr></thead>
        <tbody>{resources.map(r => <tr key={r.name}><td>{r.name}</td><td>{r.provider}</td><td><code>{r.classification}</code></td><td>{r.confidential_eligible ? 'Allowed' : 'Never'}</td></tr>)}</tbody></table></div>
        : status.data && <EmptyState title="No resources reported" />}
      {status.data && <AutomationStatus data={status.data} />}</section></>
}

export function HelpPage() {
  return <><PageHeader title="Help & Resources" description="Migration guidance and clearly labelled legacy resources. Legal-platform workflows and new terms remain pending." />
    <ResourcesView /></>
}

export { AdminPage, ProfilePage } from '../features/auth/AccountPages.jsx'
