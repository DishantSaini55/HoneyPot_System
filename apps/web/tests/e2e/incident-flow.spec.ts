import { expect, test } from "@playwright/test";

test("login, ingest, investigate, acknowledge, and resolve", async ({ page, request }) => {
  const email = process.env.E2E_ADMIN_EMAIL ?? "admin@example.com";
  const password = process.env.E2E_ADMIN_PASSWORD ?? "e2e-admin-password";
  const api = process.env.E2E_API_URL ?? "http://127.0.0.1:8000";
  const sensorKey = process.env.E2E_SENSOR_API_KEY;
  test.skip(!sensorKey, "E2E_SENSOR_API_KEY is required");

  await request.post(`${api}/api/v1/auth/register`, { data: { email, password } });
  await page.goto("/login");
  await page.getByLabel("Email").fill(email);
  await page.getByLabel("Password").fill(password);
  await page.getByRole("button", { name: "Sign in" }).click();
  await expect(page).toHaveURL(/\/dashboard/);

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

  await page.goto("/incidents");
  await page.getByRole("link", { name: /INC-/ }).first().click();
  await expect(page.getByText("Correlated timeline")).toBeVisible();
  await page.getByRole("button", { name: "Acknowledge" }).click();
  await expect(page.getByText("ACKNOWLEDGED")).toBeVisible();
  await page.getByRole("button", { name: "Resolve" }).click();
  await expect(page.getByText("RESOLVED")).toBeVisible();
});
