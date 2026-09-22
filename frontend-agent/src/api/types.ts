export interface CaseOut {
  case_id: string;
  status: string;
  open_requirements: string[];
  reported_employer: string | null;
  interview: Record<string, unknown> | null;
  recertification: Record<string, unknown> | null;
  received_document_ids: string[];
}

export interface NoticeOut {
  id: string;
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
  effective_date: string;
  topic: string;
  text: string;
}
