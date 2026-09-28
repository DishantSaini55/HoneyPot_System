import { IncidentsView } from "@/components/incidents-view";
import { PageHeader } from "@/components/page-header";
export default function IncidentsPage() { return <><PageHeader eyebrow="Investigation" title="Incidents" description="Correlated detections grouped by source and time window." /><IncidentsView /></>; }

