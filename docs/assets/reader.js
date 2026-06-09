const STORAGE_KEY = "family-album-hide-chinese";


export function readPreference(storage) {
  try {
    return storage.getItem(STORAGE_KEY) === "true";
  } catch {
    return false;
  }
}


export function togglePreference(storage, current) {
  const next = !current;
  try {
    storage.setItem(STORAGE_KEY, String(next));
  } catch {
    return next;
  }
  return next;
}


function applyPreference(root, button, hidden) {
  root.dataset.chineseHidden = String(hidden);
  button.setAttribute("aria-pressed", String(hidden));
  button.textContent = hidden ? "显示中文" : "隐藏中文";
}


function enhanceReader() {
  const button = document.querySelector("[data-chinese-toggle]");
  if (!button) {
    return;
  }

  let hidden = readPreference(window.localStorage);
  applyPreference(document.documentElement, button, hidden);
  button.addEventListener("click", () => {
    hidden = togglePreference(window.localStorage, hidden);
    applyPreference(document.documentElement, button, hidden);
  });
}


if (typeof document !== "undefined") {
  enhanceReader();
}
