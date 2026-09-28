import { PageHeader } from "@/components/page-header";
import { ResourceTable } from "@/components/resource-table";
export default function HoneypotsPage() { return <><PageHeader eyebrow="Sensors" title="Honeypots" description="Nodes registered by actual ingested events and their last observed heartbeat time." /><ResourceTable endpoint="honeypots" queryKey="honeypots" columns={[["name","Node"],["kind","Type"],["listen_port","Port"],["enabled","Enabled"],["last_seen_at","Last seen"]]} /></>; }

