import { PageHeader } from "@/components/page-header";
import { ResourceTable } from "@/components/resource-table";
export default function UsersPage() { return <><PageHeader eyebrow="Administration" title="Users" description="Authenticated dashboard accounts and their assigned roles." /><ResourceTable endpoint="admin/users" queryKey="users" columns={[["email","Email"],["role","Role"],["is_active","Active"],["created_at","Created"]]} /></>; }

