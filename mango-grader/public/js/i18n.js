// i18n.js — minimal dictionary-based i18n. No framework, no build step:
// each language is a flat dot-key -> string object in ./i18n/<lang>.js.
import ja from './i18n/ja.js';
import en from './i18n/en.js';
import zh from './i18n/zh.js';

export const SUPPORTED_LANGS = ['ja', 'en', 'zh'];
export const DEFAULT_LANG = 'ja';

const DICTS = { ja, en, zh };

function detectBrowserLang() {
  const langs = navigator.languages && navigator.languages.length ? navigator.languages : [navigator.language];
  for (const raw of langs) {
    const code = (raw || '').toLowerCase().split('-')[0];
    if (SUPPORTED_LANGS.includes(code)) return code;
  }
  return DEFAULT_LANG;
}

let currentLang = localStorage.getItem('mango_lang') || detectBrowserLang();
if (!SUPPORTED_LANGS.includes(currentLang)) currentLang = DEFAULT_LANG;

export function getLang() {
  return currentLang;
}

export function setLang(lang) {
  if (!SUPPORTED_LANGS.includes(lang)) return;
  currentLang = lang;
  localStorage.setItem('mango_lang', lang);
  document.documentElement.lang = lang;
  applyTranslations();
}

/**
 * t('some.key', {a: 1, b: 2}) -> looks up the string for the active
 * language and replaces {{a}}/{{b}} placeholders. Falls back to Japanese,
 * then to the raw key, if a translation is missing.
 */
export function t(key, vars) {
  const dict = DICTS[currentLang] || DICTS[DEFAULT_LANG];
  let str = dict[key] ?? DICTS[DEFAULT_LANG][key] ?? key;
  if (vars) {
    for (const [k, v] of Object.entries(vars)) {
      str = str.replaceAll(`{{${k}}}`, String(v));
    }
  }
  return str;
}

/**
 * Applies translations to every element with a data-i18n attribute
 * (innerHTML — dictionary values are developer-authored, not user input,
 * so this is safe and lets translated strings keep inline <strong>/<code>
 * markup) and every [data-i18n-attr] for attribute values like
 * placeholder/aria-label (format: "attr:key", e.g. "placeholder:foo.bar").
 */
export function applyTranslations(root = document) {
  root.querySelectorAll('[data-i18n]').forEach((el) => {
    const value = t(el.getAttribute('data-i18n'));
    if (el.tagName === 'TITLE') el.textContent = value;
    else el.innerHTML = value;
  });
  root.querySelectorAll('[data-i18n-attr]').forEach((el) => {
    for (const pair of el.getAttribute('data-i18n-attr').split(',')) {
      const [attr, key] = pair.split(':').map((s) => s.trim());
      if (attr && key) el.setAttribute(attr, t(key));
    }
  });
}

document.documentElement.lang = currentLang;
