"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import { parseScaleLineToGrams } from "@/lib/pos/scale-line-parser";

export type SerialScaleStatus = "closed" | "connecting" | "open" | "error";

export function useSerialScale(baudRate = 9600): {
  readonly status: SerialScaleStatus;
  readonly lastLine: string;
  readonly lastGrams: number | null;
  readonly error: string | null;
  readonly isSupported: boolean;
  connect: () => Promise<void>;
  disconnect: () => Promise<void>;
} {
  const [status, setStatus] = useState<SerialScaleStatus>("closed");
  const [lastLine, setLastLine] = useState("");
  const [lastGrams, setLastGrams] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const portRef = useRef<SerialPort | null>(null);
  const runRef = useRef(true);
  const readerRef = useRef<ReadableStreamDefaultReader<Uint8Array> | null>(null);

  const isSupported = typeof window !== "undefined" && "serial" in navigator && !!navigator.serial;

  const disconnect = useCallback(async () => {
    runRef.current = false;
    const r = readerRef.current;
    readerRef.current = null;
    if (r) {
      try {
        await r.cancel();
      } catch {
        // ignore
      }
      try {
        r.releaseLock();
      } catch {
        // ignore
      }
    }
    const p = portRef.current;
    portRef.current = null;
    if (p) {
      try {
        await p.close();
      } catch {
        // ignore
      }
    }
    setStatus("closed");
  }, []);

  const connect = useCallback(async () => {
    if (!isSupported || !navigator.serial) {
      setError("Web Serial is not available. Use Chrome or Edge over HTTPS or localhost.");
      setStatus("error");
      return;
    }
    setError(null);
    setStatus("connecting");
    runRef.current = true;
    try {
      const port = await navigator.serial.requestPort();
      await port.open({ baudRate, dataBits: 8, stopBits: 1, parity: "none", flowControl: "none" });
      if (!port.readable) {
        setError("Port is not readable.");
        setStatus("error");
        return;
      }
      portRef.current = port;
      setStatus("open");

      const dec = new TextDecoder();
      let buf = "";
      const reader = port.readable.getReader();
      readerRef.current = reader;

      const loop = async () => {
        try {
          while (runRef.current) {
            const { value, done } = await reader.read();
            if (done) break;
            if (value) {
              buf += dec.decode(value, { stream: true });
              const lines = buf.split(/\r\n|\n|\r/);
              buf = lines.pop() ?? "";
              for (const line of lines) {
                if (!line.trim()) continue;
                setLastLine(line);
                const g = parseScaleLineToGrams(line);
                if (g != null) {
                  setLastGrams(g);
                }
              }
            }
          }
        } catch (e) {
          if (runRef.current) {
            setError(e instanceof Error ? e.message : "Read error");
            setStatus("error");
          }
        }
      };
      void loop();
    } catch (e) {
      if ((e as Error).name === "NotFoundError") {
        setError("No port selected.");
      } else {
        setError(e instanceof Error ? e.message : "Serial error");
      }
      setStatus("error");
    }
  }, [baudRate, isSupported]);

  useEffect(() => {
    return () => {
      void disconnect();
    };
  }, [disconnect]);

  return {
    status,
    lastLine,
    lastGrams,
    error,
    isSupported,
    connect,
    disconnect,
  };
}
