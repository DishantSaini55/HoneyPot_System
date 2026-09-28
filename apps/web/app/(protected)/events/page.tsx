import { EventsView } from "@/components/events-view";
import { PageHeader } from "@/components/page-header";
export default function EventsPage() { return <><PageHeader eyebrow="Telemetry" title="Events" description="Search and filter normalized events persisted by authenticated honeypot sensors." /><EventsView /></>; }

