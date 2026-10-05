import type { Attendance, Person } from './api';

// Fictional showcase data. This is never mixed with the Python application's database.
export const DEMO_DATE = '2026-10-05';
export type DemoPerson = Person & { department: string; color: string };
export const people: DemoPerson[] = [
  { id: 1, employee_id: 'FT-001', name: 'Ayesha Khan', department: 'Design', color: 'mint', created_at: '2026-09-01' },
  { id: 2, employee_id: 'FT-002', name: 'Omar Ahmed', department: 'Engineering', color: 'lavender', created_at: '2026-09-02' },
  { id: 3, employee_id: 'FT-003', name: 'Sarah Ali', department: 'Operations', color: 'peach', created_at: '2026-09-03' },
  { id: 4, employee_id: 'FT-004', name: 'Hamza Malik', department: 'Engineering', color: 'blue', created_at: '2026-09-03' },
  { id: 5, employee_id: 'FT-005', name: 'Zara Hassan', department: 'Marketing', color: 'cream', created_at: '2026-09-04' },
  { id: 6, employee_id: 'FT-006', name: 'Bilal Shah', department: 'Operations', color: 'mint', created_at: '2026-09-05' },
  { id: 7, employee_id: 'FT-007', name: 'Noor Fatima', department: 'Design', color: 'lavender', created_at: '2026-09-05' },
  { id: 8, employee_id: 'FT-008', name: 'Ali Raza', department: 'Marketing', color: 'peach', created_at: '2026-09-06' },
];
export const initialRecords: Attendance[] = people.slice(0, 6).map((person, i) => ({
  employee_id: person.employee_id, name: person.name, date: DEMO_DATE,
  sign_in_time: `${DEMO_DATE}T09:${String(i * 4 + 2).padStart(2, '0')}:00+05:00`,
  sign_out_time: i === 4 ? `${DEMO_DATE}T13:30:00+05:00` : null,
  verification_status: 'sample_verified',
}));

export function initials(name: string) { return name.split(' ').map(word => word[0]).slice(0, 2).join('').toUpperCase(); }
export function formatTime(value: string | null) { return value ? value.slice(11, 16) : '—'; }
export function filterRecords(records: Attendance[], search: string, status: string, date: string) {
  const query = search.trim().toLowerCase();
  return records.filter(record => (!date || record.date === date)
    && `${record.name} ${record.employee_id}`.toLowerCase().includes(query)
    && (status === 'All statuses' || (status === 'Checked in' ? !record.sign_out_time : Boolean(record.sign_out_time))));
}

export function demoMark(records: Attendance[], person: DemoPerson, action: 'in' | 'out'): { records: Attendance[]; message: string; success: boolean } {
  const row = records.find(record => record.employee_id === person.employee_id && record.date === DEMO_DATE);
  if (action === 'in' && row) return { records, message: 'Already checked in for this demo day.', success: false };
  if (action === 'out' && !row) return { records, message: 'This person needs to check in first.', success: false };
  if (action === 'out' && row?.sign_out_time) return { records, message: 'Already checked out for this demo day.', success: false };
  if (action === 'out') return { records: records.map(record => record === row ? { ...record, sign_out_time: `${DEMO_DATE}T17:00:00+05:00` } : record), message: `${person.name} checked out.`, success: true };
  return { records: [...records, { employee_id: person.employee_id, name: person.name, date: DEMO_DATE, sign_in_time: `${DEMO_DATE}T09:30:00+05:00`, sign_out_time: null, verification_status: 'sample_verified' }], message: `${person.name} checked in.`, success: true };
}
