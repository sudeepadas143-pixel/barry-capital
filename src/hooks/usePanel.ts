import { useCallback } from 'react';
import { useSearchParams } from 'react-router-dom';

/** The trader panel is driven by `?trader=<id>` so it opens from any route and can be linked. */
export function usePanel() {
  const [params, setParams] = useSearchParams();
  const open = useCallback(
    (id: string) =>
      setParams(
        (p) => {
          const n = new URLSearchParams(p);
          n.set('trader', id);
          return n;
        },
        { replace: false },
      ),
    [setParams],
  );
  const close = useCallback(
    () =>
      setParams(
        (p) => {
          const n = new URLSearchParams(p);
          n.delete('trader');
          return n;
        },
        { replace: true },
      ),
    [setParams],
  );
  return { openId: params.get('trader'), open, close };
}
