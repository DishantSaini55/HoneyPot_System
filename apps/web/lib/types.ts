export type Severity = "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";

export interface Detection {
  rule_id: string;
  attack_type: string;
  score: number;
  evidence: Record<string, unknown>;
}

export interface EventRecord {
  id: string;
  timestamp: string;
  source_ip: string;
  source_port: number | null;
  destination_port: number;
  protocol: string;
  honeypot: string;
  session_id: string;
  event_type: string;
  username: string | null;
  command: string | null;
  user_agent: string | null;
  payload: Record<string, unknown>;
  severity: Severity;
  risk_score: number;
  detections: Detection[];
}

export interface Incident {
  id: string;
  incident_number: number;
  source_ip: string;
  attack_type: string;
  severity: Severity;
  risk_score: number;
  status: "NEW" | "ACKNOWLEDGED" | "RESOLVED";
  first_seen_at: string;
  last_seen_at: string;
  assigned_to_id: string | null;
  note: string | null;
}

export interface Page<T> {
  items: T[];
  page: number;
  page_size: number;
  total: number;
}

export interface Overview {
  total_events: number;
  active_sessions: number;
  unique_attackers: number;
  critical_incidents: number;
  detection_count: number;
  alert_count: number;
  authentication_failures: number;
  average_session_duration_seconds: number | null;
  detection_rate: number | null;
  severity: Record<string, number>;
  categories: Record<string, number>;
  timeline: { bucket: string; count: number }[];
  top_attackers: { source_ip: string; count: number }[];
  top_targeted_endpoints: { path: string; count: number }[];
  top_commands: { command: string; count: number }[];
}

export interface AttackMapData {
  points: { source_ip: string; country: string | null; city: string | null; latitude: number; longitude: number }[];
  unavailable_count: number;
}
