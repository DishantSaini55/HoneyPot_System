import { PageHeader } from "@/components/page-header";
import { ResourceTable } from "@/components/resource-table";
export default function ThreatIntelPage() { return <><PageHeader eyebrow="Enrichment" title="Threat intelligence" description="Results from the configured provider. UNAVAILABLE means no provider was configured; no location or reputation is fabricated." /><ResourceTable endpoint="threat-intelligence" queryKey="threat-intelligence" columns={[["source_ip","Source IP"],["provider","Provider"],["status","Status"],["reputation_score","Reputation"],["known_malicious","Known malicious"],["checked_at","Checked"]]} /></>; }

