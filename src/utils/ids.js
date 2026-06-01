import { customAlphabet } from 'nanoid';

const letters = customAlphabet('abcdefghijklmnopqrstuvwxyz0123456789', 5);

export function generateUsername(prefix, name) {
  const base = String(name || 'user')
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '_')
    .replace(/^_+|_+$/g, '')
    .slice(0, 12) || 'user';
  return `${prefix}_${base}_${letters()}`;
}

export function generatePassword(length = 14) {
  const alphabet = 'ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz23456789!@#';
  return customAlphabet(alphabet, length)();
}

export function toInt(value, fallback = 0) {
  const parsed = Number.parseInt(value, 10);
  return Number.isFinite(parsed) ? parsed : fallback;
}
