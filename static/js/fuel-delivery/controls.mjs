/** UI editing helpers, independent of the engineering calculation engine. */
export const hasHardBounds = field => ["fuelOptimisationScale", "simulationDurationS", "timeStepS"].includes(field.key);

export function sliderBounds(field, value) {
  // Extend soft classroom ranges to represent a typed value, never a capped surrogate.
  const usable = Number.isFinite(value) && Math.abs(value) <= 1e6;
  return hasHardBounds(field) || !usable ? {min: field.min, max: field.max} :
    {min: Math.min(field.min, value), max: Math.max(field.max, value)};
}

export function nudgeValue(field, value, direction) {
  const next = Number(((Number.isFinite(value) ? value : field.value) + direction * field.step).toPrecision(12));
  return hasHardBounds(field) ? Math.min(field.max, Math.max(field.min, next)) : next;
}
