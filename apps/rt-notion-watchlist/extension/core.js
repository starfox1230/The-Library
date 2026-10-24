export const DATA_SOURCE_ID = '8a9a4d6e-106e-4da1-bcc2-b9a10a7083d7';
export const WATCHLIST_URL = 'https://www.notion.so/880c2a70f6344b5c8824f65fafd7f9f4?v=4031d7063539815db35a000cfc86069f';
export const API_VERSION = '2026-03-11';

export function canonicalMediaUrl(value) {
  const url = new URL(value);
  if (url.protocol !== 'https:' || !['www.rottentomatoes.com', 'rottentomatoes.com'].includes(url.hostname) || url.username || url.password || url.port) {
    throw new Error('Open a movie or TV show on Rotten Tomatoes first.');
  }
  const match = url.pathname.match(/^\/(m|tv)\/([a-zA-Z0-9_-]+)(?:\/.*)?$/);
  if (!match) throw new Error('Open a movie or TV show on Rotten Tomatoes first.');
  return `https://www.rottentomatoes.com/${match[1]}/${match[2]}`;
}

export function validateMedia(input, senderUrl) {
  const url = canonicalMediaUrl(input?.url);
  if (canonicalMediaUrl(senderUrl) !== url) throw new Error('The page changed. Refresh and try again.');
  const title = typeof input?.title === 'string' ? input.title.replace(/\s+/g, ' ').trim() : '';
  if (!title || title.length > 500) throw new Error('Could not read this title. Refresh the Rotten Tomatoes page.');
  return {url, title, type: new URL(url).pathname.startsWith('/m/') ? 'Movie' : 'TV Show'};
}

export function validateSchema(source) {
  const properties = source?.properties || {};
  const required = {Name: 'title', Status: 'select', Type: 'select', 'Rotten Tomatoes': 'url', 'Date Added to Watchlist': 'date'};
  for (const [name, type] of Object.entries(required)) {
    if (properties[name]?.type !== type) throw new Error(`Watchlist needs a ${type} property named “${name}”. Check the selected Notion connection.`);
  }
  if (!properties.Status.select.options.some(option => option.name === 'For Later')) throw new Error('Status must include “For Later”.');
  for (const name of ['Movie', 'TV Show']) {
    if (!properties.Type.select.options.some(option => option.name === name)) throw new Error(`Type must include “${name}”.`);
  }
  return source;
}

export function localDate(date = new Date()) {
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;
}

export function createPayload(media, date = new Date()) {
  return {
    parent: {type: 'data_source_id', data_source_id: DATA_SOURCE_ID},
    icon: {type: 'emoji', emoji: media.type === 'Movie' ? '🎬' : '📺'},
    properties: {
      Name: {title: [{type: 'text', text: {content: media.title}}]},
      Status: {select: {name: 'For Later'}},
      Type: {select: {name: media.type}},
      'Rotten Tomatoes': {url: media.url},
      'Date Added to Watchlist': {date: {start: localDate(date)}}
    },
    children: [{object: 'block', type: 'paragraph', paragraph: {rich_text: [{type: 'text', text: {content: 'View on Rotten Tomatoes ↗', link: {url: media.url}}}]}}]
  };
}

export function notionPageUrl(page) {
  if (!/^[a-f0-9-]{32,36}$/i.test(page?.id || '')) throw new Error('Notion returned an invalid entry.');
  return `https://www.notion.so/${page.id.replaceAll('-', '')}`;
}

export function createNotionClient(token, fetcher = fetch) {
  return async (path, body) => {
    let response;
    try {
      response = await fetcher(`https://api.notion.com/v1/${path}`, {
        method: body ? 'POST' : 'GET',
        headers: {Authorization: `Bearer ${token}`, 'Notion-Version': API_VERSION, 'Content-Type': 'application/json'},
        ...(body ? {body: JSON.stringify(body)} : {}),
        signal: AbortSignal.timeout(20000), redirect: 'error', credentials: 'omit'
      });
    } catch {
      throw new Error('Could not reach Notion. Check your connection and try again; the next save checks for an existing entry first.');
    }
    if (!response.ok) {
      const errors = {
        401: 'Notion rejected this token. Open extension settings and reconnect.',
        403: 'Allow this Notion connection to read and insert content in your Watchlist.',
        404: 'Share the Watchlist database with this Notion connection, then reconnect.',
        429: 'Notion is busy. Wait a few seconds and try again.'
      };
      // Never echo server bodies: they may include sensitive request details.
      throw new Error(errors[response.status] || `Notion could not complete the request (${response.status}). Check the Watchlist fields and try again.`);
    }
    return response.json();
  };
}

export async function saveMedia(api, media, allowSeparate = false) {
  const exact = await api(`data_sources/${DATA_SOURCE_ID}/query`, {filter: {property: 'Rotten Tomatoes', url: {equals: media.url}}, page_size: 1});
  if (exact.results?.length) return {state: 'existing', url: notionPageUrl(exact.results[0])};
  if (!allowSeparate) {
    const legacy = await api(`data_sources/${DATA_SOURCE_ID}/query`, {filter: {and: [
      {property: 'Name', title: {equals: media.title}},
      {or: [{property: 'Type', select: {equals: media.type}}, {property: 'Type', select: {is_empty: true}}]},
      {property: 'Rotten Tomatoes', url: {is_empty: true}}
    ]}, page_size: 1});
    if (legacy.results?.length) return {state: 'possible', url: notionPageUrl(legacy.results[0])};
  }
  const page = await api('pages', createPayload(media));
  return {state: 'created', url: notionPageUrl(page)};
}
