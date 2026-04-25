/**
 * ESC/POS receipt printing bridge.
 *
 * Two transports supported:
 *   1. Browser print API (window.print on a hidden iframe) — works with any
 *      printer the OS already knows about. No hardware bridge needed.
 *   2. Local print-bridge WebSocket (ws://localhost:8181) — recommended for
 *      kiosk hardware. A tiny Node/Go bridge translates JSON to ESC/POS
 *      bytes and pushes them to the USB/serial printer.
 *
 * See docs/PLAN.md §14 Receipt printing.
 */

export type ReceiptLine = { readonly left: string; readonly right?: string };

export type Receipt = {
  readonly header: readonly string[];
  readonly lines: readonly ReceiptLine[];
  readonly totals: readonly ReceiptLine[];
  readonly footer: readonly string[];
};

const BRIDGE_URL = process.env.NEXT_PUBLIC_PRINT_BRIDGE_URL;

export async function printReceipt(receipt: Receipt): Promise<void> {
  if (BRIDGE_URL) {
    await sendToBridge(receipt);
    return;
  }
  sendViaBrowser(receipt);
}

async function sendToBridge(receipt: Receipt): Promise<void> {
  if (typeof WebSocket === "undefined") throw new Error("WebSocket unavailable");
  await new Promise<void>((resolve, reject) => {
    const socket = new WebSocket(BRIDGE_URL ?? "");
    socket.addEventListener("open", () => {
      socket.send(JSON.stringify({ type: "print", receipt }));
      socket.close();
      resolve();
    });
    socket.addEventListener("error", () => reject(new Error("Print bridge error")));
  });
}

function sendViaBrowser(receipt: Receipt): void {
  const frame = document.createElement("iframe");
  frame.setAttribute("aria-hidden", "true");
  frame.style.position = "fixed";
  frame.style.right = "0";
  frame.style.bottom = "0";
  frame.style.width = "0";
  frame.style.height = "0";
  frame.style.border = "0";
  document.body.appendChild(frame);

  const doc = frame.contentDocument;
  if (!doc) return;
  doc.open();
  doc.write(renderHtml(receipt));
  doc.close();
  frame.contentWindow?.focus();
  frame.contentWindow?.print();
  window.setTimeout(() => frame.remove(), 1000);
}

function renderHtml(r: Receipt): string {
  const line = (l: ReceiptLine): string =>
    `<div style="display:flex;justify-content:space-between;gap:12px"><span>${l.left}</span><span>${l.right ?? ""}</span></div>`;
  return `<!doctype html><html><head><meta charset="utf-8"><style>
    body { font-family: ui-monospace, monospace; font-size: 12px; margin: 0; padding: 8px; }
    h1 { font-size: 14px; text-align: center; margin: 4px 0; }
    hr { border: none; border-top: 1px dashed #000; margin: 6px 0; }
  </style></head><body>
    ${r.header.map((h) => `<h1>${h}</h1>`).join("")}
    <hr/>
    ${r.lines.map(line).join("")}
    <hr/>
    ${r.totals.map(line).join("")}
    <hr/>
    ${r.footer.map((f) => `<p style="text-align:center;margin:4px 0">${f}</p>`).join("")}
  </body></html>`;
}
