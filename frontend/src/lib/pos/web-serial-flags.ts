/**
 * Opt-in for Web Serial (USB) scale in the browser.
 * 1) `NEXT_PUBLIC_EXPERIMENTAL_WEB_SERIAL_SCALE=true` in env, or
 * 2) tenant `config.posWebSerialScale = true` (e.g. set via API / admin in future).
 */
export function isWebSerialScaleEnabled(config?: Record<string, unknown> | null): boolean {
  const env = process.env.NEXT_PUBLIC_EXPERIMENTAL_WEB_SERIAL_SCALE;
  if (env === "1" || env === "true") {
    return true;
  }
  if (config?.posWebSerialScale === true) {
    return true;
  }
  return false;
}
