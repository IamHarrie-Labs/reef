/** Display punctuation only. Stored notebooks and evidence remain unchanged. */
export const cleanCopy = (text: string) => text.replace(/\s*\u2014\s*/g, '; ');
