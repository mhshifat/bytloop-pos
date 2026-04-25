import { expect, test } from "@playwright/test";

/**
 * Critical auth flows (docs/PLAN.md §18 Verification).
 *
 * Require a running backend at NEXT_PUBLIC_API_BASE_URL with Mailpit/MailHog
 * catching activation emails. Locally: `pnpm dev` + `uv run uvicorn …` + Mailpit.
 */

test.describe("signup and activate flow", () => {
  test("redirects to activate-pending after signup", async ({ page }) => {
    const email = `test+${Date.now()}@example.com`;
    await page.goto("/signup");
    await page.getByLabel("First name").fill("Test");
    await page.getByLabel("Last name").fill("User");
    await page.getByLabel("Email").fill(email);
    await page.getByLabel("Password", { exact: true }).fill("passwordpass");
    await page.getByLabel("Confirm password").fill("passwordpass");
    await page.getByRole("checkbox").check();
    await page.getByRole("button", { name: /create account/i }).click();

    await expect(page).toHaveURL(/\/activate-pending/);
    await expect(page.getByText(/check your email/i)).toBeVisible();
  });

  test("resend button shows 5-minute countdown after click", async ({ page }) => {
    await page.goto("/activate-pending?email=someone@example.com");
    const resendButton = page.getByRole("button", { name: /resend/i });
    await resendButton.click();
    await expect(
      page.getByRole("button", { name: /resend in \d:\d{2}/i }),
    ).toBeVisible();
  });
});

test.describe("route protection", () => {
  test("unauthenticated user is redirected from /dashboard to /login", async ({ page }) => {
    await page.goto("/dashboard");
    await expect(page).toHaveURL(/\/login/);
    await expect(page).toHaveURL(/next=/);
  });

  test("unauthenticated user is redirected from /settings to /login", async ({ page }) => {
    await page.goto("/settings");
    await expect(page).toHaveURL(/\/login/);
  });
});

test.describe("error handling", () => {
  test("invalid login shows a message and a copy-id button", async ({ page }) => {
    await page.goto("/login");
    await page.getByLabel("Email").fill("nobody@example.com");
    await page.getByLabel("Password").fill("wrongpasswrong");
    await page.getByRole("button", { name: /sign in/i }).click();
    await expect(page.getByRole("alert")).toBeVisible();
    await expect(page.getByLabel("Copy correlation ID")).toBeVisible();
  });
});
