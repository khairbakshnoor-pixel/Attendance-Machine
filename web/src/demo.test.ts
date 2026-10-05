import { describe, expect, it } from 'vitest';
import { csv, safeCell } from './api';
import { DEMO_DATE, demoMark, filterRecords, initialRecords, people } from './demo';

describe('showcase attendance rules', () => {
  it('adds a sample check-in without mutating the starting data', () => {
    const result = demoMark(initialRecords, people[6], 'in');
    expect(result.success).toBe(true);
    expect(result.records).toHaveLength(7);
    expect(initialRecords).toHaveLength(6);
  });
  it('rejects duplicate sample check-ins', () => {
    const result = demoMark(initialRecords, people[0], 'in');
    expect(result.success).toBe(false);
    expect(result.records).toEqual(initialRecords);
  });
  it('requires a check-in before a check-out', () => {
    expect(demoMark(initialRecords, people[6], 'out').success).toBe(false);
  });
  it('records a single check-out and prevents overwriting it', () => {
    const result = demoMark(initialRecords, people[0], 'out');
    expect(result.success).toBe(true);
    expect(result.records[0].sign_out_time).toBeTruthy();
    expect(demoMark(result.records, people[0], 'out').success).toBe(false);
  });
  it('filters names, IDs, status and dates', () => {
    expect(filterRecords(initialRecords, 'AYESHA', 'All statuses', DEMO_DATE)).toHaveLength(1);
    expect(filterRecords(initialRecords, 'FT-001', 'Checked in', DEMO_DATE)).toHaveLength(1);
    expect(filterRecords(initialRecords, '', 'Checked out', DEMO_DATE)).toHaveLength(1);
    expect(filterRecords(initialRecords, '', 'All statuses', '2025-01-01')).toHaveLength(0);
  });
});

describe('sample CSV exports', () => {
  it('escapes spreadsheet formula prefixes, commas and quotes', () => {
    expect(safeCell('=1+1')).toBe('"\'=1+1"');
    expect(safeCell('  @SUM(A1)')).toBe('"\'  @SUM(A1)"');
    expect(safeCell('Alex "A", Test')).toBe('"Alex ""A"", Test"');
  });
  it('exports just the supplied filtered rows', () => {
    const result = csv(initialRecords.slice(0, 1));
    expect(result).toContain('Ayesha Khan');
    expect(result).not.toContain('Omar Ahmed');
    expect(result.split('\r\n')).toHaveLength(2);
  });
});
