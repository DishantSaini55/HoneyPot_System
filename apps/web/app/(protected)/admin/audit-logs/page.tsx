import { PageHeader } from "@/components/page-header";
import { ResourceTable } from "@/components/resource-table";
export default function AuditLogsPage() { return <><PageHeader eyebrow="Administration" title="Audit logs" description="Recorded authentication, incident workflow, user, rule, and export actions." /><ResourceTable endpoint="admin/audit-logs" queryKey="audit-logs" columns={[["created_at","Timestamp"],["action","Action"],["user_id","User"],["source_ip","Source IP"],["metadata","Metadata"]]} /></>; }

