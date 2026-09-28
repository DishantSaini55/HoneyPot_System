import { EventDetail } from "@/components/event-detail";
import { PageHeader } from "@/components/page-header";
export default async function EventPage({ params }: { params: Promise<{ id: string }> }) { const { id } = await params; return <><PageHeader eyebrow="Telemetry evidence" title="Event detail" description="Normalized metadata, detections, and captured payload for one stored event." /><EventDetail id={id} /></>; }

