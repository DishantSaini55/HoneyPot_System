import { PageHeader } from "@/components/page-header";
import { SystemHealth } from "@/components/system-health";
export default function SettingsPage() { return <><PageHeader eyebrow="Operations" title="System health" description="Direct health checks for the API, PostgreSQL, Redis, worker queue, and registered sensors." /><SystemHealth /></>; }

