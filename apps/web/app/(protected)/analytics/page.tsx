import { OverviewDashboard } from "@/components/overview-dashboard";
import { PageHeader } from "@/components/page-header";
export default function AnalyticsPage() { return <><PageHeader eyebrow="Database aggregation" title="Analytics" description="Server-side counts and grouped detections computed from persisted PostgreSQL records." /><OverviewDashboard /></>; }

