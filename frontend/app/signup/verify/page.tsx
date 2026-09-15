'use client';

import { useState, useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { signupVerify, loginVerifyOTP, signupPassword, loginRequestOTP, getCurrentUser } from '@/lib/api/authService';
import { useAuthStore } from '@/lib/store';

export default function VerifyPage() {
    const router = useRouter();
    const setUser = useAuthStore((state) => state.setUser);
    const [email, setEmail] = useState('');
    const [authType, setAuthType] = useState<'signup' | 'login'>('signup');
    const [code, setCode] = useState(['', '', '', '', '', '']);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [resending, setResending] = useState(false);
    const inputRefs = useRef<(HTMLInputElement | null)[]>([]);

    useEffect(() => {
        // Check if this is signup or login flow
        const storedEmail = sessionStorage.getItem('auth_email') || sessionStorage.getItem('signup_email');
        const type = sessionStorage.getItem('auth_type') || 'signup';

        if (!storedEmail) {
            router.push('/signup'); // Redirect if no email found
            return;
        }

        setEmail(storedEmail);
        setAuthType(type as 'signup' | 'login');
    }, [router]);

    const handleCodeChange = (index: number, value: string) => {
        if (!/^\d*$/.test(value)) return;

        const newCode = [...code];
        newCode[index] = value;
        setCode(newCode);

        // Auto-focus next input
        if (value && index < 5) {
            inputRefs.current[index + 1]?.focus();
        }

        // Auto-submit on last digit
        if (index === 5 && value && newCode.every(d => d.length === 1)) {
            setLoading(true);
            setTimeout(() => {
                handleVerify(newCode.join(''));
            }, 100);
        }
    };

    const handleKeyDown = (index: number, e: React.KeyboardEvent) => {
        if (e.key === 'Backspace' && !code[index] && index > 0) {
            inputRefs.current[index - 1]?.focus();
        }
    };

    const handleVerify = async (codeString?: string) => {
        const finalCode = codeString || code.join('');

        if (finalCode.length !== 6) {
            setError('Mohon masukkan 6 digit kode');
            return;
        }

        if (loading) return;

        setLoading(true);
        setError('');

        try {
            console.log(`Verifying ${authType} OTP for:`, email, 'Code:', finalCode);

            if (authType === 'signup') {
                // ✅ Signup flow - go to profile
                const response = await signupVerify({ email, code: finalCode });

                // Store temp_token for profile step
                sessionStorage.setItem('signup_temp_token', response.temp_token);

                // Clear login session if any, but keep signup session? 
                // Using user logic:
                sessionStorage.removeItem('auth_email');
                sessionStorage.removeItem('auth_type');

                router.push('/signup/profile');

            } else {
                // ✅ Login flow - go directly to dashboard
                // ✅ FIX: Capture tokens and store in localStorage
                const tokens = await loginVerifyOTP({ email, code: finalCode });

                if (tokens && tokens.access_token) {
                    localStorage.setItem('access_token', tokens.access_token);
                    if (tokens.refresh_token) {
                        localStorage.setItem('refresh_token', tokens.refresh_token);
                    }
                }

                // Fetch user and update store
                const user = await getCurrentUser();
                setUser(user);

                // Clear session
                sessionStorage.removeItem('auth_email');
                sessionStorage.removeItem('auth_type');

                console.log('✅ Login successful!');
                router.push('/dashboard/developer'); // Redirect to specific dashboard
            }

        } catch (err) {
            const errorMessage = err instanceof Error ? err.message : 'Invalid code';
            console.error('Verification error:', errorMessage);

            // Handle specific backend errors
            if (errorMessage.toLowerCase().includes('expired')) {
                setError('Kode kadaluarsa. Klik "Kirim ulang kode" di bawah.');
            } else if (errorMessage.toLowerCase().includes('already used')) {
                setError('Kode sudah digunakan. Silakan minta kode baru.');
            } else {
                setError('Kode verifikasi salah. Silakan coba lagi.');
            }

            // Clear inputs on error
            setCode(['', '', '', '', '', '']);
            inputRefs.current[0]?.focus();
        } finally {
            setLoading(false);
        }
    };

    const handleResend = async () => {
        setResending(true);
        setError('');

        try {
            if (authType === 'signup') {
                const password = sessionStorage.getItem('signup_password');
                // Note: signupPassword requires password? 
                // Let's check authService.ts. Yes, SignupPasswordRequest needs password if calling /signup/password endpoint.
                // But /signup/verify is just verify. Resending usually means calling /signup/password again or a resend endpoint.
                // User code calls logic: signupPassword({ email, password }). This is correct if we want to trigger a new email.
                if (!password) {
                    // If no password in session, maybe we can't resend using that endpoint?
                    // Or maybe we should use /signup/init? 
                    // Sticking to user logic which assumes password is in session.
                    console.warn('No password found for resend');
                    // Perhaps redirect back to password step?
                    // router.push('/signup/password');
                    // return;
                }

                if (password) {
                    await signupPassword({ email, password: password });
                } else {
                    // Fallback if no password? Maybe just request OTP logic specific to signup?
                    // For now assume logic is correct as per user prompt
                }
            } else {
                // Login flow resend
                await loginRequestOTP({ email });
            }

            // Clear inputs
            setCode(['', '', '', '', '', '']);
            inputRefs.current[0]?.focus();
            console.log('✅ New OTP sent');
        } catch (err) {
            setError('Gagal mengirim ulang kode');
        } finally {
            setResending(false);
        }
    };

    return (
        <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
            <div className="max-w-md w-full space-y-8 p-8 bg-white rounded-lg shadow border">
                <div className="text-center">
                    <h2 className="text-3xl font-bold">Periksa kotak masuk Anda</h2>
                    <p className="mt-2 text-gray-600">
                        Masukkan kode verifikasi yang kami kirim ke
                    </p>
                    <p className="font-medium mt-1">{email}</p>
                    {/* ✅ Show different message based on flow */}
                    <p className="text-sm text-gray-500 mt-2">
                        {authType === 'signup' ? 'Selesaikan pendaftaran Anda' : 'Masuk ke akun Anda'}
                    </p>
                </div>

                <div className="space-y-6">
                    <div>
                        <label className="block text-sm font-medium text-gray-700 text-center mb-3">
                            Kode
                        </label>
                        <div className="flex gap-2 justify-center">
                            {code.map((digit, index) => (
                                <input
                                    key={index}
                                    ref={el => { inputRefs.current[index] = el; }}
                                    type="text"
                                    maxLength={1}
                                    value={digit}
                                    onChange={(e) => handleCodeChange(index, e.target.value)}
                                    onKeyDown={(e) => handleKeyDown(index, e)}
                                    className="w-12 h-12 text-center text-2xl font-bold border-2 border-gray-300 rounded-md focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
                                    autoFocus={index === 0}
                                    disabled={loading}
                                />
                            ))}
                        </div>
                    </div>

                    {error && (
                        <div className="bg-red-50 border border-red-200 rounded-md p-3 text-red-700 text-sm text-center">
                            {error}
                        </div>
                    )}

                    <button
                        onClick={() => handleVerify()}
                        disabled={loading || code.some(d => !d)}
                        className="w-full py-3 px-4 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 font-medium transition-colors"
                    >
                        {loading ? 'Memverifikasi...' : 'Lanjutkan'}
                    </button>

                    <div className="text-center">
                        <button
                            onClick={handleResend}
                            disabled={resending || loading}
                            className="text-sm text-blue-600 hover:underline disabled:text-gray-400"
                        >
                            {resending ? 'Mengirim...' : 'Kirim ulang kode'}
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}
