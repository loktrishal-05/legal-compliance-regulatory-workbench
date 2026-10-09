// Honest "coming in this build" pages. Each owner replaces ONE route line in app/routes.jsx with its real page.
import { ComingInThisBuild } from './LegalShared.jsx'

export const LegalDashboardPlaceholder = () => <ComingInThisBuild title="Legal dashboard" owner="agent C" />
export const DocumentsPlaceholder = () => <ComingInThisBuild title="Documents" owner="agent A" />
export const SourcePlaceholder = () => <ComingInThisBuild title="Source viewer" owner="agent A" />
export const ContractsPlaceholder = () => <ComingInThisBuild title="Contracts" owner="agent A" />
export const ReviewsPlaceholder = () => <ComingInThisBuild title="Review queue" owner="agent A" />
export const CompliancePlaceholder = () => <ComingInThisBuild title="Compliance" owner="agent B" />
export const RegulatoryPlaceholder = () => <ComingInThisBuild title="Regulatory intelligence" owner="agent B" />
export const SummariesPlaceholder = () => <ComingInThisBuild title="Summaries" owner="agent B" />
export const AssistantPlaceholder = () => <ComingInThisBuild title="Legal assistant" owner="agent B" />
export const ObligationsPlaceholder = () => <ComingInThisBuild title="Obligations and tasks" owner="agent C" />
export const LegalAuditPlaceholder = () => <ComingInThisBuild title="Legal audit and exports" owner="agent C" />
