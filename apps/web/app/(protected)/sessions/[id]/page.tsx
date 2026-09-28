import { JsonDetail } from "@/components/json-detail";
import { PageHeader } from "@/components/page-header";
export default async function SessionPage({ params }: { params: Promise<{ id: string }> }) { const { id } = await params; return <><PageHeader eyebrow="Session evidence" title="Session detail" description="The complete event sequence captured for one sensor session." /><JsonDetail endpoint={`sessions/${id}`} queryKey={`session-${id}`} /></>; }

