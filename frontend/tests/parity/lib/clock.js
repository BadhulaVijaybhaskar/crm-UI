/**
 * Frozen Date for Playwright — injected via addInitScript only.
 * Never shipped in production bundles.
 */
export function clockInitScript(isoNow) {
  const ms = Date.parse(isoNow)
  return `
(() => {
  const frozen = ${ms};
  const RealDate = Date;
  class FrozenDate extends RealDate {
    constructor(...args) {
      if (args.length === 0) super(frozen);
      else super(...args);
    }
    static now() { return frozen; }
    static parse = RealDate.parse;
    static UTC = RealDate.UTC;
  }
  FrozenDate.prototype = RealDate.prototype;
  window.Date = FrozenDate;
})();
`
}
