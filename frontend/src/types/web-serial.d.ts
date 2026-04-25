/**
 * Minimal types for the Web Serial API (Chromium), used for USB label scales
 * and similar devices. @see https://wicg.github.io/serial/
 */
interface SerialPortInfo {
  readonly usbVendorId?: number;
  readonly usbProductId?: number;
}

type SerialOptions = {
  readonly baudRate?: number;
  readonly dataBits?: number;
  readonly stopBits?: number;
  readonly parity?: "none" | "even" | "odd";
  readonly flowControl?: "none" | "hardware";
  readonly bufferSize?: number;
};

type SerialPort = {
  readonly readable: ReadableStream<Uint8Array> | null;
  readonly writable: WritableStream<Uint8Array> | null;
  open: (options: SerialOptions) => Promise<void>;
  close: () => Promise<void>;
};

type Serial = {
  requestPort: (options?: { readonly filters?: readonly USBDeviceFilter[] }) => Promise<SerialPort>;
  getPorts: () => Promise<readonly SerialPort[]>;
};

type USBDeviceFilter = {
  readonly usbVendorId?: number;
  readonly usbProductId?: number;
  readonly classCode?: number;
  readonly protocolCode?: number;
  readonly subclassCode?: number;
  readonly serialNumber?: string;
};

interface Navigator {
  /** Present in Chromium (Chrome, Edge) over HTTPS or localhost. */
  readonly serial?: Serial;
}
