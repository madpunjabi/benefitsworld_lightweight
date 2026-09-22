export interface CaseOut {
  case_id: string;
  status: string;
  open_requirements: string[];
  reported_employer: string | null;
  interview: InterviewState | null;
  recertification: Record<string, unknown> | null;
  received_document_ids: string[];
}

export interface InterviewState {
  status: "scheduled" | "completed";
  slot_id: string;
  day: number;
  start_time: string;
  end_time: string;
}

export interface NoticeOut {
  id: string;
  day: number;
  text: string;
}

export interface DocumentOut {
  id: string;
  filename: string;
  date: string;
  type: string;
  visible_text: string;
}

export interface PolicyItemOut {
  id: string;
  title: string;
  source: string;
  source_url: string | null;
  jurisdiction: string;
  effective_date: string | null;
  source_version: string | null;
  topic: string;
  text: string;
}

export interface InterviewSlotOut {
  id: string;
  day: number;
  start_time: string;
  end_time: string;
}

export interface CalendarEventOut {
  day: number;
  start_time: string;
  end_time: string;
  label: string;
}

export interface InboxMessageOut {
  id: number;
  day: number;
  sender: string;
  subject: string;
  body: string;
  is_read: boolean;
}
