import { describe, expect, it, vi } from "vitest";
import { ApiError, createClient } from "./index";

describe("createClient", () => {
  it("sends the tenant header and parses JSON", async () => {
    const fetchMock = vi.fn(async () =>
      new Response(JSON.stringify({ status: "ok", version: "0.1.0" }), {
        headers: { "content-type": "application/json" },
      }),
    );
    const client = createClient({ baseUrl: "http://api/", tenantId: "t1", fetch: fetchMock });
    await expect(client.health()).resolves.toEqual({ status: "ok", version: "0.1.0" });
    const [url, init] = fetchMock.mock.calls[0] as unknown as [string, RequestInit];
    expect(url).toBe("http://api/health");
    expect((init.headers as Record<string, string>)["X-Tenant-ID"]).toBe("t1");
  });

  it("raises ApiError with the server error code", async () => {
    const fetchMock = vi.fn(async () =>
      new Response(JSON.stringify({ error: { code: "unsupported_format", message: "nope" } }), {
        status: 415,
        headers: { "content-type": "application/json" },
      }),
    );
    const client = createClient({ baseUrl: "http://api", fetch: fetchMock });
    await expect(client.listDocuments()).rejects.toMatchObject({
      status: 415,
      code: "unsupported_format",
    } satisfies Partial<ApiError>);
  });

  it("builds render and export URLs", () => {
    const client = createClient({ baseUrl: "http://api" });
    expect(client.renderUrl("d1", "swipe")).toBe("http://api/v1/documents/d1/render?reader_mode=swipe");
    expect(client.exportUrl("d1")).toBe("http://api/v1/documents/d1/export");
  });
});
