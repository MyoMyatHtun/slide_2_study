export interface GeneratedNote {
  id: string;
  title: string;
  summary: string;
  keyConcepts: string[];
  definitions: { term: string; definition: string }[];
}

export interface UploadState {
  file: File | null;
  text: string;
  type: 'file' | 'text';
}