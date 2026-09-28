import { PageHeader } from "@/components/page-header";
import { ResourceTable } from "@/components/resource-table";
export default function RulesPage() { return <><PageHeader eyebrow="Administration" title="Alert rules" description="Persisted alert delivery rules. Detection rules are version-controlled deterministic code." /><ResourceTable endpoint="admin/rules" queryKey="rules" columns={[["name","Rule"],["minimum_score","Minimum score"],["attack_type","Attack type"],["enabled","Enabled"],["channels","Channels"]]} /></>; }

