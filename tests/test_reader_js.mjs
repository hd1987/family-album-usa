import assert from "node:assert/strict";
import {
  readPreference,
  togglePreference,
} from "../assets/reader.js";


const storage = new Map();
const fakeStorage = {
  getItem(key) {
    return storage.has(key) ? storage.get(key) : null;
  },
  setItem(key, value) {
    storage.set(key, value);
  },
};

assert.equal(readPreference(fakeStorage), false);
assert.equal(togglePreference(fakeStorage, false), true);
assert.equal(
  fakeStorage.getItem("family-album-hide-chinese"),
  "true",
);
assert.equal(readPreference(fakeStorage), true);
assert.equal(togglePreference(fakeStorage, true), false);
assert.equal(
  fakeStorage.getItem("family-album-hide-chinese"),
  "false",
);

console.log("reader.js tests passed");
