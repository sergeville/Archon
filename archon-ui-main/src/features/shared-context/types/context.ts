export interface ContextEntry {
  id: string;
  context_key: string;
  value: unknown;
  set_by: string;
  session_id?: string | null;
  expires_at?: string | null;
  created_at: string;
  updated_at: string;
}

export interface ContextHistoryEntry {
  id: string;
  context_key: string;
  old_value?: unknown;
  new_value: unknown;
  changed_by: string;
  changed_at: string;
}

export interface SetContextRequest {
  value: unknown;
  set_by: string;
  session_id?: string;
  expires_at?: string;
}

export interface ContextListResponse {
  success: boolean;
  context: ContextEntry[];
  count: number;
}

export interface ContextHistoryResponse {
  success: boolean;
  history: ContextHistoryEntry[];
  count: number;
}
