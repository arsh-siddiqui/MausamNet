/** Domain types mirroring backend schemas (backend/app/schemas/common.py). */

export const SOURCE_CATEGORIES = ["GOVERNMENT", "WEATHER_API", "NEWS", "SOCIAL", "PUBLIC_DATASET", "CITIZEN"] as const;
export const EVENT_TYPES = ["RAINFALL", "FLOOD", "THUNDERSTORM", "HEATWAVE", "FOG", "DUST_STORM", "STRONG_WIND", "OTHER"] as const;
export const SEVERITIES = ["LOW", "MEDIUM", "HIGH", "CRITICAL"] as const;
export const EVENT_STATUSES = ["CANDIDATE", "ACTIVE", "VERIFIED", "REJECTED", "RESOLVED"] as const;

export type SourceCategory = (typeof SOURCE_CATEGORIES)[number];
export type EventType = (typeof EVENT_TYPES)[number];
export type Severity = (typeof SEVERITIES)[number];

export const SOURCE_LABELS: Record<string, string> = {
  GOVERNMENT: "Government",
  WEATHER_API: "Weather API",
  PUBLIC_DATASET: "Public Dataset",
  NEWS: "News",
  SOCIAL: "Social",
  CITIZEN: "Citizen",
};

export const EVENT_TYPE_LABELS: Record<string, string> = {
  RAINFALL: "Rainfall",
  FLOOD: "Flood",
  THUNDERSTORM: "Thunderstorm",
  HEATWAVE: "Heatwave",
  FOG: "Fog",
  DUST_STORM: "Dust Storm",
  STRONG_WIND: "Strong Wind",
  OTHER: "Other",
};

export const SEVERITY_COLORS: Record<string, string> = {
  LOW: "#22c55e",
  MEDIUM: "#eab308",
  HIGH: "#f97316",
  CRITICAL: "#ef4444",
};

export interface Signal {
  id: string;
  source_id: string;
  source_category: SourceCategory;
  headline: string;
  content: string;
  media_url: string | null;
  event_type: EventType;
  severity: Severity;
  status: string;
  latitude: number;
  longitude: number;
  city: string;
  district: string;
  state: string;
  occurred_at: string;
  ingested_at: string;
  ai_confidence: number;
  ai_label: string;
  trust_score: number;
  duplicate_of: string | null;
  duplicate_score: number;
  suspicious: boolean;
  suspicious_reasons: string[];
  metrics: Record<string, number | string>;
  event_id: string | null;
  explanation: string[];
}

export interface EvidenceEntry {
  strength: string;
  weight: number;
  count: number;
  note: string;
}

export interface TimelineEntry {
  at: string;
  label: string;
  detail?: string;
}

export interface Event {
  id: string;
  title: string;
  event_type: EventType;
  severity: Severity;
  status: string;
  latitude: number;
  longitude: number;
  city: string;
  district: string;
  state: string;
  radius_km: number;
  started_at: string;
  latest_at: string;
  signal_count: number;
  confidence: number;
  trust_score: number;
  description: string;
  fusion: {
    meteorological?: number;
    spatial_consistency?: number;
    temporal_consistency?: number;
    source_reliability?: number;
    media_authenticity?: number;
    cross_source_agreement?: number;
    confidence?: number;
    explanations?: string[];
  };
  evidence: Record<string, EvidenceEntry>;
  timeline: TimelineEntry[];
  metrics: {
    growth_rate?: number;
    peak_rainfall_mm?: number;
    peak_wind_kph?: number;
    max_temp_c?: number;
    radius_km?: number;
    source_breakdown?: Record<string, number>;
  };
  related_event_ids: string[];
}

export interface EventDetail extends Event {
  signals: Signal[];
  graph: { nodes: { id: string; label: string }[]; edges: { source: string; target: string; relation: string; weight: number }[] } | null;
  anomalies: Anomaly[];
  verification_history: { id: string; action: string; rationale: string; verifier_id: string; created_at: string }[];
  related_events: Event[];
}

export interface SignalDetail extends Signal {
  location_consistency: { score: number; distance_from_city_center_km?: number; note?: string };
  time_consistency: { score: number; age_hours: number };
  weather_evidence: { score: number; observed_peak_mm: number | null; note: string };
  related_signals: { id: string; headline: string; source_category: string; city: string; similarity: number }[];
  media_analysis: Record<string, unknown> | null;
  verification_history: Record<string, unknown>[];
}

export interface Anomaly {
  id: string;
  metric: string;
  city: string;
  district: string;
  state: string;
  latitude: number;
  longitude: number;
  observed_at: string;
  expected_low: number;
  expected_high: number;
  observed_value: number;
  deviation_pct: number;
  zscore: number;
  risk: Severity;
  event_id: string | null;
  explanation: string[];
}

export interface Source {
  id: string;
  name: string;
  category: SourceCategory;
  mode: string;
  status: string;
  reliability: number;
  signals_per_day: number;
  latency_ms: number;
  last_sync_at: string | null;
  config: Record<string, unknown>;
}

export interface DashboardOverview {
  signals_processed: number;
  active_events: number;
  critical_events: number;
  suspicious_signals: number;
  verified_events: number;
  pending_reviews: number;
  generated_at: string;
}

export interface EventsPage {
  items: Event[];
  total: number;
  page: number;
  pages: number;
}

export interface SignalsPage {
  items: Signal[];
  total: number;
  page: number;
  pages: number;
}

export interface Alert {
  id: string;
  type: string;
  severity: string;
  title: string;
  message: string;
  event_id: string | null;
  signal_id: string | null;
  read_at: string | null;
  created_at: string;
}

export interface AlertsPage {
  items: Alert[];
  total: number;
  page: number;
  pages: number;
}

export interface MapPoint {
  id: string;
  kind: "event" | "signal" | "anomaly";
  latitude: number;
  longitude: number;
  title: string;
  event_type: string;
  severity: string;
  status?: string | null;
  source_category?: string | null;
  confidence?: number | null;
  trust_score?: number | null;
  signal_count?: number | null;
  suspicious?: boolean;
  deviation_pct?: number | null;
  metric?: string | null;
  occurred_at?: string | null;
  state?: string | null;
  district?: string | null;
  city?: string | null;
}

export interface AnalyticsOverview {
  event_trend: { bucket: string; events: number; signals: number }[];
  state_ranking: StateRow[];
  event_categories: { name: string; value: number }[];
  verification_rate: { bucket: string; events: number; signals: number }[];
  suspicious_trend: { bucket: string; events: number; signals: number }[];
  source_reliability: {
    category: string;
    signals: number;
    verified_pct: number;
    suspicious_pct: number;
    avg_trust: number;
    reliability: number;
  }[];
  hourly_distribution: { hour: string; events: number }[];
  severity_distribution: { severity: string; count: number }[];
  states: StateRow[];
}

export interface StateRow {
  state: string;
  signals: number;
  events: number;
  verified_pct: number;
  suspicious_pct: number;
  critical: number;
  avg_confidence: number;
}

export interface SimulationStatus {
  running: boolean;
  speed: number;
  scenario: string;
  stage: number;
  ticks: number;
  signals_generated: number;
  scenario_stages: string[];
}

export interface VerificationItem {
  event: Event;
  source_breakdown: Record<string, number>;
  trust_score: number;
  ai_recommendation: string;
  evidence_summary: string[];
}

export interface GroundReport {
  id: string;
  tracking_id: string;
  reporter_name: string;
  event_type: string;
  description: string;
  city: string;
  district: string;
  state: string;
  status: string;
  signal_id: string | null;
  created_at: string;
}

export interface MediaAnalysis {
  id: string;
  filename: string;
  phash: string;
  width: number;
  height: number;
  filesize: number;
  format: string;
  captured_at: string | null;
  exif_ok: boolean;
  similarity: number;
  match_signal_id: string | null;
  previous_seen_at: string | null;
  previous_location: string;
  finding: string;
  checks: Record<string, unknown>;
  explanation: string[];
}

export interface SystemHealth {
  overall: string;
  components: { name: string; status: string; latency_ms: number; last_heartbeat: string; detail: string }[];
  version: string;
  environment: string;
}

export interface SearchResults {
  events: Event[];
  signals: Signal[];
  sources: Source[];
  locations: { city: string; state: string; label: string }[];
}
