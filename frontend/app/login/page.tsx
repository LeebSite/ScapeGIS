"use client";

import { useState, useRef } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuthStore } from "@/lib/store";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { UserRole } from "@/lib/types/auth";
import { getDashboardRoute } from "@/lib/utils";
import { login, googleOAuth, getCurrentUser, signupInit, adminRequestMagicLink, loginRequestOTP, loginVerifyOTP } from "@/lib/api/authService";
import { GoogleOAuthProvider, GoogleLogin } from '@react-oauth/google';

type LoginStep = 'email' | 'password' | 'otp' | 'admin-link-sent';
type LoginMethod = 'password' | 'otp';

export default function LoginPage() {
	const router = useRouter();
	const setUser = useAuthStore((state) => state.setUser);

	const [step, setStep] = useState<LoginStep>('email');
	const [loginMethod, setLoginMethod] = useState<LoginMethod>('otp'); // Default to OTP
	const [email, setEmail] = useState("");
	const [password, setPassword] = useState("");
	const [otp, setOtp] = useState(['', '', '', '', '', '']);
	const [isLoading, setIsLoading] = useState(false);
	const [showPassword, setShowPassword] = useState(false);
	const [error, setError] = useState<string | null>(null);
	const otpInputRefs = useRef<(HTMLInputElement | null)[]>([]);

	// Step 1: Check email to determine flow
	const handleEmailContinue = async (e: React.FormEvent) => {
		e.preventDefault();
		setIsLoading(true);
		setError(null);

		try {
			// Call backend to check if email exists and get role
			const response = await signupInit({ email });

			// If password_required, this is an existing user
			if (response.status === 'password_required') {
				// ✅ EXISTING USER: Auto-send OTP and redirect to verify page
				console.log('✅ Existing user detected, sending OTP...');
				try {
					await loginRequestOTP({ email });

					// Store session data for verify page
					sessionStorage.setItem('auth_email', email);
					sessionStorage.setItem('auth_type', 'login');

					console.log('✅ OTP sent to:', email);
					router.push('/signup/verify');
				} catch (otpErr: any) {
					// Fallback: If OTP request fails with 404, treat as new user
					const msg = otpErr.message || '';
					if (msg.includes('404') || msg.toLowerCase().includes('not found')) {
						console.log('⚠️ OTP request 404, redirecting to signup...');
						sessionStorage.setItem('signup_email', email);
						router.push('/signup/password');
						return;
					}
					setError('Gagal mengirim OTP. Silakan coba lagi.');
				}
			} else {
				// ✅ NEW USER: Redirect to signup password creation
				console.log('✅ New user detected, redirecting to signup...');
				sessionStorage.setItem('signup_email', email);
				router.push('/signup/password');
				return;
			}
		} catch (err: any) {
			// ✅ FIX: Properly extract error message
			let errorMsg = 'Failed to continue';

			if (err instanceof Error) {
				errorMsg = err.message;
			} else if (typeof err === 'object' && err !== null) {
				errorMsg = err.detail || err.message || JSON.stringify(err);
			}

			// Check if this is "email not found" or "user doesn't exist"
			if (errorMsg.toLowerCase().includes('not found') ||
				errorMsg.toLowerCase().includes('does not exist') ||
				errorMsg.toLowerCase().includes('no user')) {
				// New user - redirect to signup flow
				sessionStorage.setItem('signup_email', email);
				router.push('/signup/password');
				return;
			}

			// ✅ Check if "Email already registered" - EXISTING USER!
			if (errorMsg.toLowerCase().includes('already registered') ||
				errorMsg.toLowerCase().includes('already exists')) {
				// Existing user - send OTP and redirect to verify page
				console.log('✅ Email already registered, sending OTP...');
				try {
					await loginRequestOTP({ email });

					// Store session data for verify page
					sessionStorage.setItem('auth_email', email);
					sessionStorage.setItem('auth_type', 'login');

					console.log('✅ OTP sent to:', email);
					router.push('/signup/verify');
				} catch (otpErr: any) {
					let otpErrorMsg = 'Gagal mengirim OTP';
					if (otpErr instanceof Error) {
						otpErrorMsg = otpErr.message;
					} else if (typeof otpErr === 'object' && otpErr !== null) {
						otpErrorMsg = otpErr.detail || otpErr.message || JSON.stringify(otpErr);
					}
					setError(otpErrorMsg);
				}
				return;
			}

			// Check if this is an admin email
			if (errorMsg.toLowerCase().includes('admin')) {
				// Send magic link for admin
				try {
					await adminRequestMagicLink({ email });
					setStep('admin-link-sent');
				} catch (adminErr: any) {
					setError(adminErr.message || "Failed to send magic link");
				}
			} else {
				// Other errors (including rate limit)
				if (errorMsg.toLowerCase().includes('429') || errorMsg.toLowerCase().includes('too many')) {
					setError('Terlalu banyak percobaan. Silakan tunggu beberapa menit.');
				} else {
					setError(errorMsg);
				}
			}
		} finally {
			setIsLoading(false);
		}
	};

	// Step 2: Login with password (for existing developers)
	const handlePasswordLogin = async (e: React.FormEvent) => {
		e.preventDefault();
		setIsLoading(true);
		setError(null);

		try {
			// ✅ FIX: Capture tokens and store in localStorage
			const tokens = await login({ email, password });

			if (tokens && tokens.access_token) {
				localStorage.setItem('access_token', tokens.access_token);
				// Check if refresh_token exists before saving
				if (tokens.refresh_token) {
					localStorage.setItem('refresh_token', tokens.refresh_token);
				}
			}

			const user = await getCurrentUser();
			setUser(user);

			const dashboardRoute = getDashboardRoute(user.role);
			router.push(dashboardRoute);
		} catch (err: any) {
			const errorMessage = err.message || "Invalid email or password. Please try again.";

			// Check if this is a "user not found" error (new user)
			if (errorMessage.toLowerCase().includes('not found') ||
				errorMessage.toLowerCase().includes('does not exist') ||
				errorMessage.toLowerCase().includes('no user')) {
				// User doesn't exist - redirect to signup flow
				sessionStorage.setItem('signup_email', email);
				sessionStorage.setItem('signup_password', password);
				router.push('/signup/password');
				return;
			}

			// Other errors (wrong password, etc.)
			setError(errorMessage);
			console.error("Login failed:", err);
		} finally {
			setIsLoading(false);
		}
	};

	const handleGoogleSuccess = async (credentialResponse: any) => {
		setIsLoading(true);
		setError(null);

		try {
			// ✅ FIX: Capture tokens and store in localStorage
			const tokens = await googleOAuth({ id_token: credentialResponse.credential });

			if (tokens && tokens.access_token) {
				localStorage.setItem('access_token', tokens.access_token);
				if (tokens.refresh_token) {
					localStorage.setItem('refresh_token', tokens.refresh_token);
				}
			}

			const user = await getCurrentUser();
			setUser(user);
			const dashboardRoute = getDashboardRoute(user.role);
			router.push(dashboardRoute);
		} catch (error: any) {
			const errorMessage = error.message || "Google authentication failed. Please try again.";
			setError(errorMessage);
			console.error("Google Login Failed:", error);
		} finally {
			setIsLoading(false);
		}
	};




	// Email step - ChatGPT style
	if (step === 'email') {
		return (
			<GoogleOAuthProvider clientId={process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID || "YOUR_CLIENT_ID"}>
				<div className="min-h-screen flex items-center justify-center bg-muted/50 px-4">
					<Card className="w-full max-w-md">
						<CardHeader className="space-y-1">
							<div className="flex items-center justify-center mb-4">
								<div className="flex items-center gap-2">
									<img src="/img/logo_scapegis.svg" alt="Scapegis Logo" width={48} height={48} className="block" />
									<span className="font-kayak text-2xl tracking-wide font-semibold text-[#01123E]">Scapegis</span>
								</div>
							</div>
							<CardTitle className="text-2xl text-center">Masuk atau Daftar</CardTitle>
							<CardDescription className="text-center">Anda akan mendapatkan respons yang lebih cerdas dan dapat mengunggah file, gambar, dan lainnya.</CardDescription>
						</CardHeader>
						<CardContent>
							{/* Google OAuth Button */}
							<div className="flex justify-center mb-4">
								<div className="w-full">
									<GoogleLogin
										onSuccess={handleGoogleSuccess}
										text="continue_with"
										width="100%"
										size="large"
									/>
								</div>
							</div>

							{/* Divider */}
							<div className="relative my-4">
								<div className="absolute inset-0 flex items-center">
									<span className="w-full border-t" />
								</div>
								<div className="relative flex justify-center text-xs uppercase">
									<span className="bg-card px-2 text-muted-foreground">ATAU</span>
								</div>
							</div>

							{/* Email Form */}
							<form onSubmit={handleEmailContinue} className="space-y-4">
								<div>
									<Input
										id="email"
										type="email"
										placeholder="Alamat Email"
										value={email}
										onChange={(e) => setEmail(e.target.value)}
										required
										autoFocus
									/>
								</div>

								{error && (
									<div className="bg-destructive/10 border border-destructive/20 rounded-md p-3 text-destructive text-sm">
										{error}
									</div>
								)}

								<Button
									type="submit"
									disabled={isLoading}
									className="w-full"
								>
									{isLoading ? 'Memeriksa...' : 'Lanjutkan'}
								</Button>
							</form>
						</CardContent>
					</Card>
				</div>
			</GoogleOAuthProvider>
		);
	}



	// Password step - for existing developers
	if (step === 'password') {
		return (
			<div className="min-h-screen flex items-center justify-center bg-muted/50 px-4">
				<Card className="w-full max-w-md">
					<CardHeader className="space-y-1">
						<div className="flex items-center justify-center mb-4">
							<div className="flex items-center gap-2">
								<img src="/img/logo_scapegis.svg" alt="Scapegis Logo" width={48} height={48} className="block" />
								<span className="font-kayak text-2xl tracking-wide font-semibold text-[#01123E]">Scapegis</span>
							</div>
						</div>
						<CardTitle className="text-2xl text-center">Masukkan kata sandi Anda</CardTitle>
					</CardHeader>
					<CardContent>
						{/* Show email (read-only) */}
						<div className="mb-4 p-3 bg-muted rounded-md">
							<p className="text-sm text-muted-foreground">Email</p>
							<p className="font-medium">{email}</p>
							<button
								onClick={() => setStep('email')}
								className="text-sm text-primary hover:underline mt-1"
							>
								Ubah
							</button>
						</div>

						{/* Password Form */}
						<form onSubmit={handlePasswordLogin} className="space-y-4">
							<div>
								<div className="relative">
									<Input
										id="password"
										type={showPassword ? "text" : "password"}
										placeholder="Kata Sandi"
										value={password}
										onChange={(e) => setPassword(e.target.value)}
										required
										autoFocus
										className="pr-10"
									/>
									<button
										type="button"
										aria-label={showPassword ? "Hide password" : "Show password"}
										onClick={() => setShowPassword((s) => !s)}
										className="absolute right-2 top-1/2 -translate-y-1/2 inline-flex items-center justify-center rounded px-2 py-1 text-sm text-muted-foreground hover:text-foreground"
									>
										{showPassword ? (
											<svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor">
												<path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13.875 18.825A10.05 10.05 0 0112 19c-5 0-9-3.5-10-8 1-2.5 3-4.5 5.25-5.75M3 3l18 18" />
											</svg>
										) : (
											<svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor">
												<path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
												<path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
											</svg>
										)}
									</button>
								</div>
							</div>

							{error && (
								<div className="bg-destructive/10 border border-destructive/20 rounded-md p-3 text-destructive text-sm">
									{error}
								</div>
							)}

							<Button type="submit" disabled={isLoading} className="w-full">
								{isLoading ? 'Masuk...' : 'Lanjutkan'}
							</Button>
						</form>

						{/* Link to signup */}
						<div className="mt-4 text-center text-sm">
							<span className="text-muted-foreground">Belum punya akun? </span>
							<Link href="/signup" className="text-primary hover:underline">
								Daftar
							</Link>

						</div>
					</CardContent>
				</Card>
			</div>
		);
	}

	// Admin magic link sent
	if (step === 'admin-link-sent') {
		return (
			<div className="min-h-screen flex items-center justify-center bg-muted/50 px-4">
				<Card className="w-full max-w-md">
					<CardContent className="pt-6">
						<div className="text-center">
							<div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-green-100 mb-4">
								<svg className="h-6 w-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
									<path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
								</svg>
							</div>
							<h2 className="text-2xl font-bold mb-2">Periksa email Anda</h2>
							<p className="text-muted-foreground mb-4">
								Kami telah mengirim tautan ajaib ke <strong>{email}</strong>.
								Klik tautan untuk masuk sebagai admin.
							</p>
							<p className="text-sm text-muted-foreground">
								Tautan kadaluarsa dalam 10 menit.
							</p>
							<Button
								variant="ghost"
								onClick={() => setStep('email')}
								className="mt-4"
							>
								← Kembali ke login
							</Button>
						</div>
					</CardContent>
				</Card>
			</div>
		);
	}

	return null;
}
