// ===== ENUMS =====
// ===== ENUMS =====
export type UserRole = 'admin' | 'developer';
// Deprecated enum for backward compatibility if needed, but better to remove
// export enum UserRoleEnum {
//     ADMIN = 'admin',
//     DEVELOPER = 'developer'
// }

export enum AuthProvider {
    LOCAL = 'local',
    GOOGLE = 'google',
    ADMIN_MAGIC_LINK = 'admin_magic_link'
}

// ===== USER =====
export interface User {
    id: string;
    email: string;
    name: string;
    role: UserRole;
    avatar_url?: string | null;
    birthday?: string; // YYYY-MM-DD format
}

// ===== SIGNUP REQUESTS/RESPONSES =====
export interface SignupInitRequest {
    email: string;
}

export interface SignupInitResponse {
    status: 'password_required';
    email: string;
}

export interface SignupPasswordRequest {
    email: string;
    password: string;
}

export interface SignupPasswordResponse {
    status: 'verification_sent';
    email: string;
    message: string;
}

export interface SignupVerifyRequest {
    email: string;
    code: string; // 6 digits
}

export interface SignupVerifyResponse {
    status: 'profile_required';
    email: string;
    temp_token: string;
}

export interface SignupCompleteRequest {
    email: string;
    temp_token: string;
    name: string;
    birthday: string; // YYYY-MM-DD
}

// ===== AUTH TOKENS =====
export interface AuthTokens {
    access_token: string;
    refresh_token?: string;
    token_type: string;
}

// ===== LOGIN =====
export interface LoginRequest {
    email: string;
    password: string;
}

export interface GoogleOAuthRequest {
    id_token: string;
}

// ===== ADMIN =====
export interface AdminMagicLinkRequest {
    email: string;
}

export interface AdminMagicLinkResponse {
    message: string;
}

// ===== SIGNUP STATE (for multi-step form) =====
export interface SignupState {
    email: string;
    password?: string;
    code?: string;
    tempToken?: string;
    name?: string;
    birthday?: string;
    currentStep: 1 | 2 | 3 | 4;
}
