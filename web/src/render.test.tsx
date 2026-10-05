import { afterEach, describe, expect, it, vi } from 'vitest';
import { renderToStaticMarkup } from 'react-dom/server';
import App from './App';

afterEach(() => vi.unstubAllGlobals());

describe('public website rendering', () => {
  it('renders the marketing page with a working demo target and product sections', () => {
    vi.stubGlobal('window', { location: { hash: '' } });
    const html = renderToStaticMarkup(<App />);
    expect(html).toContain('Great teams');
    expect(html).toContain('Explore the live demo');
    expect(html).toContain('id="platform"');
    expect(html).toContain('id="workflow"');
    expect(html).toContain('id="privacy"');
    expect(html).not.toContain('<iframe');
  });
  it('opens the demo directly and clearly identifies sample records', () => {
    vi.stubGlobal('window', { location: { hash: '#demo' } });
    const html = renderToStaticMarkup(<App />);
    expect(html).toContain('All people and records are fictional');
    expect(html).toContain('Ayesha Khan');
    expect(html).toContain('Search attendance');
    expect(html).toContain('Export report');
    expect(html).toContain('SAMPLE DAY');
  });
});
