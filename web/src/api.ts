export const COMPANY = import.meta.env.VITE_COMPANY_NAME || 'FaceTrack';

export type Person = { id: number; employee_id: string; name: string; created_at: string };
export type Attendance = { employee_id: string; name: string; date: string; sign_in_time: string; sign_out_time: string | null; verification_status: string };

export function safeCell(value: string | null): string {
  const text = value ?? '';
  const safe = /^[\s]*[=+\-@]/.test(text) || /^[\t\r\n]/.test(text) ? `'${text}` : text;
  return `"${safe.replaceAll('"', '""')}"`;
}

export function csv(records: Attendance[]): string {
  const columns: (keyof Attendance)[] = ['employee_id', 'name', 'date', 'sign_in_time', 'sign_out_time', 'verification_status'];
  return '\uFEFF' + [columns.join(','), ...records.map(row => columns.map(key => safeCell(row[key])).join(','))].join('\r\n');
}

export function download(records: Attendance[]) {
  const url = URL.createObjectURL(new Blob([csv(records)], { type: 'text/csv;charset=utf-8;' }));
  const anchor = document.createElement('a'); anchor.href = url; anchor.download = 'facetrack-demo-attendance.csv'; anchor.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
