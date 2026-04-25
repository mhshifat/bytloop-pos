import { apiFetch } from "./fetcher";

export type LoginInput = { readonly email: string; readonly password: string };

export type TokenResponse = {
  readonly accessToken: string;
  readonly expiresIn: number;
};

export type SignupInput = {
  readonly firstName: string;
  readonly lastName: string;
  readonly email: string;
  readonly password: string;
  readonly confirmPassword: string;
  readonly acceptTerms: boolean;
};

export type SignupResponse = {
  readonly userId: string;
  readonly email: string;
  readonly activationSent: boolean;
};

export type ResendActivationResponse = {
  readonly sent: boolean;
  readonly cooldownRemainingSeconds: number;
};

export type MeResponse = {
  readonly id: string;
  readonly email: string;
  readonly firstName: string;
  readonly lastName: string;
  readonly emailVerified: boolean;
  readonly roles: readonly string[];
  readonly tenantId: string;
};

export async function signup(input: SignupInput): Promise<SignupResponse> {
  return apiFetch<SignupResponse>("/auth/signup", { method: "POST", json: input });
}

export async function login(input: LoginInput): Promise<TokenResponse> {
  return apiFetch<TokenResponse>("/auth/login", { method: "POST", json: input });
}

export async function logout(): Promise<void> {
  return apiFetch<void>("/auth/logout", { method: "POST" });
}

export async function refresh(): Promise<TokenResponse> {
  return apiFetch<TokenResponse>("/auth/refresh", { method: "POST" });
}

export async function activate(token: string): Promise<void> {
  return apiFetch<void>("/auth/activate", { method: "POST", json: { token } });
}

export async function resendActivation(email: string): Promise<ResendActivationResponse> {
  return apiFetch<ResendActivationResponse>("/auth/resend-activation", {
    method: "POST",
    json: { email },
  });
}

export async function forgotPassword(email: string): Promise<void> {
  return apiFetch<void>("/auth/forgot-password", { method: "POST", json: { email } });
}

export async function resetPassword(token: string, newPassword: string): Promise<void> {
  return apiFetch<void>("/auth/reset-password", {
    method: "POST",
    json: { token, newPassword },
  });
}

export async function me(accessToken: string): Promise<MeResponse> {
  return apiFetch<MeResponse>("/auth/me", {
    headers: { Authorization: `Bearer ${accessToken}` },
  });
}

export async function meCookie(): Promise<MeResponse> {
  return apiFetch<MeResponse>("/auth/me");
}

export async function changePassword(input: {
  readonly currentPassword: string;
  readonly newPassword: string;
}): Promise<void> {
  return apiFetch<void>("/auth/change-password", { method: "POST", json: input });
}

export type StaffMember = {
  readonly id: string;
  readonly email: string;
  readonly firstName: string;
  readonly lastName: string;
  readonly roles: readonly string[];
  readonly emailVerified: boolean;
};

export async function listStaff(): Promise<readonly StaffMember[]> {
  return apiFetch<readonly StaffMember[]>("/auth/staff");
}

export type StaffInviteInput = {
  readonly firstName: string;
  readonly lastName: string;
  readonly email: string;
  readonly roles: readonly string[];
};

export async function inviteStaff(input: StaffInviteInput): Promise<StaffMember> {
  return apiFetch<StaffMember>("/auth/staff", { method: "POST", json: input });
}

export async function updateStaffRoles(
  userId: string,
  roles: readonly string[],
): Promise<StaffMember> {
  return apiFetch<StaffMember>(`/auth/staff/${userId}/roles`, {
    method: "PATCH",
    json: { roles },
  });
}

export async function removeStaff(userId: string): Promise<void> {
  return apiFetch<void>(`/auth/staff/${userId}`, { method: "DELETE" });
}
