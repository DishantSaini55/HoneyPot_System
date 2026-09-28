import { PageHeader } from "@/components/page-header";
import { ResourceTable } from "@/components/resource-table";
export default function AttackersPage() { return <><PageHeader eyebrow="Sources" title="Attackers" description="Observed source addresses and provider-backed location data. Unavailable enrichment is never inferred." /><ResourceTable endpoint="attackers?page_size=100" queryKey="attackers" columns={[["source_ip","Source IP"],["first_seen_at","First seen"],["last_seen_at","Last seen"],["country","Country"],["organization","Organization"],["event_count","Events"],["max_risk_score","Max risk"]]} link={(row) => `/attackers/${row.source_ip}`} /></>; }

