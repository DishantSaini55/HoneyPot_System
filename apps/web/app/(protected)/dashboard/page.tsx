import { OverviewDashboard } from "@/components/overview-dashboard";
import { PageHeader } from "@/components/page-header";

export default function DashboardPage() {
  return <><PageHeader eyebrow="Security operations" title="Threat overview" description="Database-backed telemetry, detections, incidents, and alerts. Values update when sensors ingest real events." /><OverviewDashboard /></>;
}

