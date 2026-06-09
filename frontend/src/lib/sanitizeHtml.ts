const allowedTags = new Set([
  "a",
  "b",
  "blockquote",
  "br",
  "code",
  "div",
  "em",
  "figcaption",
  "figure",
  "h1",
  "h2",
  "h3",
  "h4",
  "h5",
  "h6",
  "hr",
  "i",
  "img",
  "li",
  "ol",
  "p",
  "pre",
  "span",
  "strong",
  "u",
  "ul",
]);

const voidTags = new Set(["br", "hr", "img"]);
const dangerousBlockPattern =
  /<\s*(script|style|iframe|object|embed|svg|math|template|form|input|button|textarea|select|option|link|meta|base)[^>]*>[\s\S]*?<\s*\/\s*\1\s*>/gi;
const dangerousTagPattern =
  /<\s*\/?\s*(script|style|iframe|object|embed|svg|math|template|form|input|button|textarea|select|option|link|meta|base)[^>]*>/gi;
const tokenPattern = /<!--[\s\S]*?-->|<\/?[A-Za-z][^>]*>/g;
const tagPattern = /^<\s*(\/?)\s*([A-Za-z][A-Za-z0-9-]*)([\s\S]*?)(\/?)\s*>$/;
const attrPattern = /([^\s"'<>/=]+)(?:\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s"'=<>`]+)))?/g;
const numericEntityPattern = /&(?:#(\d+)|#x([0-9a-f]+)|amp|lt|gt|quot|apos);/gi;

const namedEntities: Record<string, string> = {
  amp: "&",
  apos: "'",
  gt: ">",
  lt: "<",
  quot: '"',
};

export function sanitizeRawItemHtml(value: string): string {
  const stripped = value.replace(dangerousBlockPattern, "").replace(dangerousTagPattern, "");
  let output = "";
  let cursor = 0;

  // 核心安全边界：只保留可读正文需要的标签和属性，其余内容统一转义或丢弃。
  for (const match of stripped.matchAll(tokenPattern)) {
    const token = match[0];
    const index = match.index ?? 0;
    output += textToHtml(stripped.slice(cursor, index));
    output += sanitizeTag(token);
    cursor = index + token.length;
  }

  output += textToHtml(stripped.slice(cursor));
  return output.trim();
}

function sanitizeTag(token: string): string {
  if (token.startsWith("<!--")) {
    return "";
  }

  const match = tagPattern.exec(token);
  if (!match) {
    return escapeHtml(token);
  }

  const [, closingSlash, rawTagName, rawAttrs, selfClosingSlash] = match;
  const tagName = rawTagName.toLowerCase();
  if (!allowedTags.has(tagName)) {
    return "";
  }

  if (closingSlash) {
    return voidTags.has(tagName) ? "" : `</${tagName}>`;
  }

  const attrs = sanitizeAttributes(tagName, rawAttrs);
  if (tagName === "img" && !attrs.some((attr) => attr.startsWith("src="))) {
    return "";
  }

  const attrText = attrs.length ? ` ${attrs.join(" ")}` : "";
  if (voidTags.has(tagName) || selfClosingSlash) {
    return `<${tagName}${attrText}>`;
  }
  return `<${tagName}${attrText}>`;
}

function sanitizeAttributes(tagName: string, rawAttrs: string): string[] {
  const attrs: string[] = [];
  for (const match of rawAttrs.matchAll(attrPattern)) {
    const name = match[1].toLowerCase();
    const value = match[2] ?? match[3] ?? match[4] ?? "";

    if (name.startsWith("on") || name === "style" || name === "class" || name.startsWith("data-")) {
      continue;
    }

    if (tagName === "a" && name === "href") {
      const safeHref = normalizeSafeUrl(value);
      if (safeHref) {
        attrs.push(`href="${escapeAttribute(safeHref)}"`, 'target="_blank"', 'rel="noopener noreferrer"');
      }
      continue;
    }

    if (tagName === "a" && name === "title") {
      attrs.push(`title="${escapeAttribute(value)}"`);
      continue;
    }

    if (tagName === "img" && name === "src") {
      const safeSrc = normalizeSafeUrl(value);
      if (safeSrc) {
        attrs.push(`src="${escapeAttribute(safeSrc)}"`);
      }
      continue;
    }

    if (tagName === "img" && name === "alt") {
      attrs.push(`alt="${escapeAttribute(value)}"`);
      continue;
    }

    if (tagName === "img" && (name === "width" || name === "height")) {
      const dimension = normalizeDimension(value);
      if (dimension) {
        attrs.push(`${name}="${dimension}"`);
      }
    }
  }

  if (tagName === "img") {
    attrs.push('loading="lazy"', 'decoding="async"');
  }
  return attrs;
}

function normalizeSafeUrl(value: string): string | null {
  const decoded = decodeHtmlEntities(value).trim();
  if (!decoded) {
    return null;
  }

  const normalized = decoded.startsWith("//") ? `https:${decoded}` : decoded;
  const protocolProbe = normalized.replace(/[\u0000-\u001F\u007F\s]+/g, "");
  if (/^[a-z][a-z0-9+.-]*:/i.test(protocolProbe) && !/^https?:/i.test(protocolProbe)) {
    return null;
  }
  if (!/^https?:\/\//i.test(protocolProbe)) {
    return null;
  }
  return normalized;
}

function normalizeDimension(value: string): string | null {
  const trimmed = value.trim();
  return /^\d{1,5}$/.test(trimmed) ? trimmed : null;
}

function textToHtml(value: string): string {
  return escapeHtml(value).replace(/\r?\n/g, "<br>");
}

function escapeHtml(value: string): string {
  return value
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function escapeAttribute(value: string): string {
  return escapeHtml(decodeHtmlEntities(value));
}

function decodeHtmlEntities(value: string): string {
  return value.replace(
    numericEntityPattern,
    (_, decimal: string | undefined, hex: string | undefined, offset: number, input: string) => {
      const entity = input.slice(offset + 1, input.indexOf(";", offset)).toLowerCase();
      if (decimal) {
        return decodeCodePoint(Number.parseInt(decimal, 10));
      }
      if (hex) {
        return decodeCodePoint(Number.parseInt(hex, 16));
      }
      return namedEntities[entity] ?? `&${entity};`;
    },
  );
}

function decodeCodePoint(value: number): string {
  if (!Number.isFinite(value) || value < 0 || value > 0x10ffff) {
    return "";
  }
  return String.fromCodePoint(value);
}
