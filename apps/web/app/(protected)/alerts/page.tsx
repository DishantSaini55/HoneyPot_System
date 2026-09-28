import { PageHeader } from "@/components/page-header";
import { ResourceTable } from "@/components/resource-table";
export default function AlertsPage() { return <><PageHeader eyebrow="Response" title="Alerts" description="Stored alert records produced by correlation thresholds and brute-force detections." /><ResourceTable endpoint="alerts" queryKey="alerts" columns={[["title","Alert"],["severity","Severity"],["status","Status"],["created_at","Created"],["incident_id","Incident"]]} /></>; }

