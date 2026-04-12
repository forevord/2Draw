import { describe, it, expect, vi, beforeEach } from "vitest";

vi.stubEnv("NEXT_PUBLIC_SUPABASE_URL", "https://test.supabase.co");
vi.stubEnv("NEXT_PUBLIC_SUPABASE_ANON_KEY", "test-anon-key");

vi.mock("@supabase/ssr", () => ({
  createBrowserClient: vi.fn(() => ({
    auth: { getUser: vi.fn() },
    from: vi.fn(),
  })),
}));

describe("Supabase browser client", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("createClient returns a client object with auth and from methods", async () => {
    const { createClient } = await import("../lib/supabase/client");
    const client = createClient();
    expect(client).toBeDefined();
    expect(typeof client.auth).toBe("object");
    expect(typeof client.from).toBe("function");
  });
});
