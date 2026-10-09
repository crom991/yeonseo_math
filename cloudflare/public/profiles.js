export const PROFILES = Object.freeze({
  yeonseo: Object.freeze({ id: "yeonseo", name: "연서", emoji: "🌷" }),
  haeun: Object.freeze({ id: "haeun", name: "하은", emoji: "🌼" }),
});

export const DEFAULT_PROFILE_ID = "yeonseo";

export function normalizeProfileId(value) {
  const profileId = String(value || "").trim().toLowerCase();
  return Object.hasOwn(PROFILES, profileId) ? profileId : null;
}

export function profileName(profileId) {
  return PROFILES[normalizeProfileId(profileId)]?.name || PROFILES[DEFAULT_PROFILE_ID].name;
}
