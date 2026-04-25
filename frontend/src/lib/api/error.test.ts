import { describe, expect, it } from "vitest";

import { isApiError, networkApiError, toApiError } from "./error";

describe("toApiError", () => {
  it("extracts the whitelisted envelope from a valid error response", async () => {
    const body = {
      error: {
        correlationId: "01HXYZ",
        code: "not_found",
        message: "Not found.",
        details: null,
      },
    };
    const response = new Response(JSON.stringify(body), {
      status: 404,
      headers: { "X-Correlation-Id": "01HXYZ" },
    });
    const err = await toApiError(response);
    expect(err.correlationId).toBe("01HXYZ");
    expect(err.code).toBe("not_found");
    expect(err.message).toBe("Not found.");
    expect(err.status).toBe(404);
  });

  it("falls back to the X-Correlation-Id header when body is not JSON", async () => {
    const response = new Response("<html>gateway</html>", {
      status: 502,
      headers: { "X-Correlation-Id": "01HCID" },
    });
    const err = await toApiError(response);
    expect(err.correlationId).toBe("01HCID");
    expect(err.code).toBe("internal_error");
    expect(err.status).toBe(502);
  });

  it("generates a client correlation ID when body and header are missing", async () => {
    const response = new Response("", { status: 500 });
    const err = await toApiError(response);
    expect(err.correlationId).toMatch(/^client_/);
  });
});

describe("networkApiError", () => {
  it("returns a client-generated correlation ID and network_error code", () => {
    const err = networkApiError();
    expect(err.correlationId).toMatch(/^client_/);
    expect(err.code).toBe("network_error");
    expect(err.status).toBe(0);
  });
});

describe("isApiError", () => {
  it("narrows unknown to ApiError", () => {
    const value: unknown = {
      correlationId: "x",
      code: "c",
      message: "m",
      details: null,
      status: 400,
    };
    expect(isApiError(value)).toBe(true);
  });

  it("rejects partial shapes", () => {
    expect(isApiError({ correlationId: "x" })).toBe(false);
    expect(isApiError(null)).toBe(false);
    expect(isApiError("string")).toBe(false);
  });
});
