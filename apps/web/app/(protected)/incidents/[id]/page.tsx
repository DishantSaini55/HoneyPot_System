import { IncidentDetail } from "@/components/incidents-view";
import { PageHeader } from "@/components/page-header";
export default async function IncidentPage({ params }: { params: Promise<{ id: string }> }) { const { id } = await params; return <><PageHeader eyebrow="Investigation" title="Incident timeline" description="Review evidence and update the analyst workflow state." /><IncidentDetail id={id} /></>; }

