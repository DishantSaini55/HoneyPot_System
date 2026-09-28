import { JsonDetail } from "@/components/json-detail";
import { PageHeader } from "@/components/page-header";
export default async function AttackerPage({ params }: { params: Promise<{ ip: string }> }) { const { ip } = await params; return <><PageHeader eyebrow="Source profile" title={decodeURIComponent(ip)} description="Observed sessions and configured threat-intelligence results for this source." /><JsonDetail endpoint={`attackers/${encodeURIComponent(ip)}`} queryKey={`attacker-${ip}`} /></>; }

