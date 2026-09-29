import { PageHeader } from "@/components/page-header";
import { ResourceTable } from "@/components/resource-table";
export default function SessionsPage() { return <><PageHeader eyebrow="Correlation" title="Sessions" description="Sensor sessions linked to attackers and normalized events." /><ResourceTable endpoint="sessions?page_size=100" queryKey="sessions" columns={[["id","Session"],["source_ip","Source IP"],["protocol","Protocol"],["status","Status"],["started_at","Started"],["ended_at","Ended"],["event_count","Events"]]} linkPrefix="/sessions" linkField="id" /></>; }
