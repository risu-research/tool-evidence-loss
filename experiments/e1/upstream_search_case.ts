    case "search": {
      const validation = SearchSchema.safeParse(args);
      if (!validation.success) {
        return errorResponse(validation.error.errors[0].message);
      }
      const { query: userQuery, pageSize, pageToken, rawQuery, orderBy } = validation.data;

      let formattedQuery: string;
      if (rawQuery) {
        // Use query directly; auto-append trashed guard unless user already includes it
        formattedQuery = /\btrashed\s*=/.test(userQuery)
          ? userQuery
          : `${userQuery} and trashed = false`;
      } else {
        const escapedQuery = escapeDriveQuery(userQuery);
        formattedQuery = `fullText contains '${escapedQuery}' and trashed = false`;
      }

      const res = await withRetry(
        (signal) => ctx.getDrive().files.list({
          q: formattedQuery,
          pageSize: Math.min(pageSize || 50, 100),
          pageToken: pageToken,
          fields: "nextPageToken, files(id, name, mimeType, createdTime, modifiedTime, size, parents)",
          orderBy,
          ...ALL_DRIVES_LIST_PARAMS
        }, { signal }),
        ctx.runtimeConfig,
        'drive.files.list(search)',
        ctx.log
      );

      // Resolve folder paths from parent IDs (with dedup for concurrent lookups)
      const pathCache: Record<string, Promise<string>> = {};
      function resolveParentPath(folderId: string, depth = 0): Promise<string> {
        if (depth >= 10) return Promise.resolve(folderId);
        if (folderId in pathCache) return pathCache[folderId];
        const promise = (async () => {
          try {
            const folderRes = await withRetry(
              (signal) => ctx.getDrive().files.get({
                fileId: folderId,
                fields: "name, parents",
                supportsAllDrives: true,
              }, { signal }),
              ctx.runtimeConfig,
              'drive.files.get(parentPath)',
              ctx.log
            );
            const name = folderRes.data.name || folderId;
            const parents = folderRes.data.parents;
            if (parents && parents.length > 0 && parents[0] !== folderId) {
              const parentPath = await resolveParentPath(parents[0], depth + 1);
              return `${parentPath}/${name}`;
            }
            return name;
          } catch {
            return folderId;
          }
        })();
        pathCache[folderId] = promise;
        return promise;
      }

      const files = res.data.files || [];
      const fileLines = await Promise.all(
        files.map(async (f: drive_v3.Schema$File) => {
          let folderPath = '';
          if (f.parents && f.parents.length > 0) {
            folderPath = await resolveParentPath(f.parents[0]);
          }
          return `${f.name} (${f.mimeType}) [id: ${f.id}, path: ${folderPath || '/'}] [created: ${f.createdTime || 'N/A'}, modified: ${f.modifiedTime || 'N/A'}]`;
        }),
      );

      ctx.log('Search results', { query: userQuery, rawQuery: !!rawQuery, orderBy, resultCount: files.length });

      // Name the ordering in the response: an unlabeled list invites the caller to
      // pick "the most recent" by eye and get it wrong (#167).
      let response = `Found ${files.length} files (ordered by ${orderBy}):\n${fileLines.join("\n")}`;
      if (res.data.nextPageToken) {
        // Keep the token alone on its line — trailing text after an unquoted token
        // invites the caller to carry it into the token value.
        response += `\n\nMore results available. Use pageToken: ${res.data.nextPageToken}`;
        // orderBy has a default, so a follow-up call carrying only the token would
        // silently fall back to `modifiedTime desc` and re-sort page 2 (#167).
        response += `\nPass orderBy: ${orderBy} again to keep this ordering.`;
      }

      return {
        content: [{ type: "text", text: response }],
        isError: false,
      };
    }
