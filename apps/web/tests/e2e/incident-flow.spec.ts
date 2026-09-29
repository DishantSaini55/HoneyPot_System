import { expect, test } from "@playwright/test";

test("login, ingest, investigate, acknowledge, and resolve", async ({ page, request }) => {
  const email = process.env.E2E_ADMIN_EMAIL ?? "admin@example.com";
  const password = process.env.E2E_ADMIN_PASSWORD ?? "e2e-admin-password";
  const api = process.env.E2E_API_URL ?? "http://127.0.0.1:8000";
  const sensorKey = process.env.E2E_SENSOR_API_KEY;
  test.skip(!sensorKey, "E2E_SENSOR_API_KEY is required");

  let streamConnections = 0;
  await page.route("**/api/management/stream/events", async (route) => {
    streamConnections += 1;
    if (streamConnections === 1) await route.abort("connectionreset");
    else await route.continue();
  });

  await request.post(`${api}/api/v1/auth/register`, { data: { email, password } });
  await page.goto("/login");
  await page.getByLabel("Email").fill(email);
  await page.getByLabel("Password").fill(password);
  await page.getByRole("button", { name: "Sign in" }).click();
  await expect(page).toHaveURL(/\/dashboard/);
  await expect(page.getByText("Total events", { exact: true })).toBeVisible();
  await expect.poll(() => streamConnections, { timeout: 15_000 }).toBeGreaterThan(1);
  const totalCard = page.getByText("Total events", { exact: true }).locator("..");
  const before = Number(await totalCard.locator("p").nth(1).innerText());

  const eventId = crypto.randomUUID();
  const sessionId = crypto.randomUUID();
  const response = await request.post(`${api}/api/v1/ingest/events`, {
    headers: { "X-Sensor-Key": sensorKey! },
    data: {
      event_id: eventId,
      timestamp: new Date().toISOString(),
      source_ip: "192.0.2.240",
      source_port: 45678,
      destination_port: 8080,
      protocol: "HTTP",
      honeypot: "HTTP",
      session_id: sessionId,
      event_type: "HTTP_REQUEST",
      user_agent: "sqlmap/e2e",
      payload: { method: "GET", path: "/../../etc/passwd", raw_target: "/..%2f..%2fetc/passwd?id=1%20OR%201=1--", query: { id: "1 OR 1=1--" }, headers: {}, body_size: 0, response_code: 404 },
    },
  });
  expect(response.status()).toBe(202);
  await expect.poll(async () => Number(await totalCard.locator("p").nth(1).innerText()), { timeout: 15_000 }).toBeGreaterThan(before);

  await page.goto("/incidents");
  await page.getByRole("link", { name: /INC-/ }).first().click();
  await expect(page.getByText("Correlated timeline")).toBeVisible();
  await page.getByRole("button", { name: "Acknowledge" }).click();
  await expect(page.getByText("ACKNOWLEDGED")).toBeVisible();
  await page.getByRole("button", { name: "Resolve" }).click();
  await expect(page.getByText("RESOLVED")).toBeVisible();
});

test("major SOC routes render backend-backed states", async ({ page }) => {
  const email = process.env.E2E_ADMIN_EMAIL ?? "admin@example.com";
  const password = process.env.E2E_ADMIN_PASSWORD ?? "e2e-admin-password";
  await page.goto("/login");
  await page.getByLabel("Email").fill(email);
  await page.getByLabel("Password").fill(password);
  await page.getByRole("button", { name: "Sign in" }).click();
  await expect(page).toHaveURL(/\/dashboard/);

  const routes = [
    "/dashboard", "/events", "/analytics", "/attackers", "/sessions", "/honeypots",
    "/incidents", "/alerts", "/threat-intelligence", "/admin/users", "/admin/rules",
    "/admin/audit-logs", "/settings",
  ];
  for (const route of routes) {
    const response = await page.goto(route);
    expect(response?.ok(), route).toBeTruthy();
    await expect(page.locator("main")).toBeVisible();
    await expect(page.locator("main")).not.toContainText("Unable to load the management API");
  }
});
