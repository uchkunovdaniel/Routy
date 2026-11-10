// XSS defence, layer 1: React escapes all rendered text (we never use dangerouslySetInnerHTML).
// Layer 2 (this file): normalise user input before it is stored. Repeat this on your real backend –
// never trust client-side sanitising alone.
export const clean = (value, max = 2000) =>
  String(value ?? '')
    .replace(/<[^>]*>/g, '')                                   // strip HTML tags
    .replace(/[\u0000-\u0008\u000B\u000C\u000E-\u001F]/g, '')  // control chars
    .trim()
    .slice(0, max)

// Only allow images we produced ourselves (data URLs) – blocks javascript: and remote tracking URLs.
export const safeImage = (src) => (/^data:image\/(jpeg|png|webp);base64,/.test(src) ? src : '')

export const validCoords = (lat, lng) =>
  Number.isFinite(lat) && Number.isFinite(lng) && Math.abs(lat) <= 90 && Math.abs(lng) <= 180
