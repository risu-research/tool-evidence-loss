/** Provider-independent, intentionally lossy R3 from frozen RAW source fixtures.
 * This module NEVER imports expected labels or accesses prewritten visibleR3.
 * R3.exact_zero means zero visible/returned items (or explicit observed-count zero),
 * NOT a warranty of query completeness. That distinction is the paper's subject.
 */
const allEmpty = xs => Array.isArray(xs) && xs.every(x => Array.isArray(x) && x.length === 0);
const noNext = token => token == null || token === '';

export function projectFromSource(e) {
  if (!e || typeof e !== 'object') throw new Error('missing source evidence');
  let zero, final, root;
  switch(e.provider) {
    case 'google-drive':
      zero = Array.isArray(e.response?.files) && e.response.files.length === 0;
      final = noNext(e.response?.nextPageToken);
      root = e.request?.pageToken == null;
      break;
    case 'google-drive-chain': {
      const pages = e.pages;
      if (!Array.isArray(pages) || pages.length === 0) throw new Error('missing pages');
      zero = allEmpty(pages.map(p => p.files));
      final = noNext(pages[pages.length - 1].nextPageToken);
      root = pages[0].requestPageToken == null;
      break;
    }
    case 'elasticsearch':
    case 'elasticsearch-clusters':
      zero = Array.isArray(e.hits?.hits) && e.hits.hits.length === 0 && e.hits?.total?.value === 0 && e.hits?.total?.relation === 'eq';
      final = true; // a completed transport response, with source timeout/coverage projected away
      root = true;  // request pagination not represented in these controlled raw fixtures
      break;
    case 'algolia':
    case 'algolia-authority':
      zero = Array.isArray(e.response?.hits) && e.response.hits.length === 0 && e.response?.nbHits === 0;
      final = true; // page/view coverage intentionally not encoded in generic R3
      root = true;
      break;
    case 'microsoft-graph-delta': {
      const pages = e.pages;
      if (!Array.isArray(pages) || pages.length === 0) throw new Error('missing pages');
      zero = allEmpty(pages.map(p => p.value));
      final = noNext(pages[pages.length - 1].nextLink);
      root = pages[0].requestUrl === e.rootUrl;
      break;
    }
    default: throw new Error('unsupported source profile: ' + e.provider);
  }
  return {
    final_empty: zero,
    exec_ok: true, // server delivered a successful JSON-RPC result
    continuation_present: !final,
    root_request: root,
    exact_zero: zero,
  };
}

/** Check only request identities actually present in the uploaded source fixtures.
 * An Elasticsearch query receipt is absent: do NOT claim exact premise binding there.
 */
export function checkExistingSourceRequestBinding(e, args) {
  if (!e || !args) return false;
  switch (e.provider) {
    case 'google-drive':
      return typeof e.request?.q === 'string' && e.request.q === args.q;
    case 'google-drive-chain':
      return args.pageToken === null && e.pages?.[0]?.requestPageToken === null;
    case 'algolia':
      return e.requestedIndex === args.requestedIndex;
    case 'algolia-authority':
      return e.requestedIndex === args.requestedIndex && e.requiredAuthorityViewId === args.requiredAuthorityViewId;
    case 'microsoft-graph-delta':
      return e.rootUrl === args.rootUrl;
    default:
      return null; // unassessed, not a positive binding proof
  }
}
