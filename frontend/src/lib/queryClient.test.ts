import { describe, it, expect } from 'vitest';
import { queryClient } from './queryClient';

describe('QueryClient configuration', () => {
  it('configures query client with clinical dental caching defaults', () => {
    expect(queryClient).toBeDefined();
    const defaultOptions = queryClient.getDefaultOptions();
    expect(defaultOptions.queries?.retry).toBe(1);
    expect(defaultOptions.queries?.refetchOnWindowFocus).toBe(false);
  });
});
