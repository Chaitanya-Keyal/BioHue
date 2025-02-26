export interface Analysis {
  substrate: string;
  metric: string;
  value: number;
  result: string;
}

export interface FileData {
  id: string;
  base64?: string;
}

export interface ImageData {
  id: string;
  user_id: string;
  original_image: FileData;
  processed_image?: FileData;
  analysis?: Analysis;
  created_at: string;
}
