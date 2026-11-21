export function sourceQualifiedDecision(e) {
  const exactZero = (hits) => hits?.total?.value === 0 && hits?.total?.relation === 'eq' && Array.isArray(hits?.hits) && hits.hits.length === 0;
  const shardsComplete = (s) => Number.isInteger(s?.total) && s.total > 0 && s.successful === s.total && s.failed === 0;
  switch (e.provider) {
    case 'google-drive':
      return e.request?.pageToken == null && Array.isArray(e.response?.files) && e.response.files.length === 0 && e.response.incompleteSearch === false && e.response.nextPageToken == null;
    case 'google-drive-chain': {
      const p=e.pages;
      if (!Array.isArray(p) || p.length < 2 || p[0].requestPageToken != null) return false;
      for (let i=0;i<p.length;i++) {
        if (!Array.isArray(p[i].files) || p[i].files.length !== 0 || p[i].incompleteSearch !== false) return false;
        if (i < p.length-1 && (!p[i].nextPageToken || p[i+1].requestPageToken !== p[i].nextPageToken)) return false;
      }
      return p[p.length-1].nextPageToken == null;
    }
    case 'elasticsearch':
      return e.timed_out === false && shardsComplete(e._shards) && exactZero(e.hits);
    case 'elasticsearch-clusters': {
      const c=e._clusters;
      return e.timed_out === false && shardsComplete(e._shards) && exactZero(e.hits) && Number.isInteger(c?.total) && c.total>0 && c.successful===c.total && c.skipped===0 && c.partial===0 && c.failed===0;
    }
    case 'algolia':
      return e.response?.nbHits === 0 && e.response?.exhaustiveNbHits === true && Array.isArray(e.response?.hits) && e.response.hits.length === 0 && e.response.indexUsed === e.requestedIndex;
    case 'algolia-authority':
      return e.response?.nbHits === 0 && e.response?.exhaustiveNbHits === true && Array.isArray(e.response?.hits) && e.response.hits.length === 0 && e.response.indexUsed === e.requestedIndex && e.authorityViewId === e.requiredAuthorityViewId;
    case 'microsoft-graph-delta': {
      const p=e.pages;
      if (!Array.isArray(p) || p.length===0 || p[0].requestUrl !== e.rootUrl) return false;
      for (let i=0;i<p.length;i++) {
        if (!Array.isArray(p[i].value) || p[i].value.length !== 0) return false;
        if (i < p.length-1 && (!p[i].nextLink || p[i+1].requestUrl !== p[i].nextLink)) return false;
      }
      const last=p[p.length-1];
      return !last.nextLink && typeof last.deltaLink === 'string' && last.deltaLink.length > 0;
    }
    default: return false;
  }
}
