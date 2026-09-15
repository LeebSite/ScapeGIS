'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { signupPassword } from '@/lib/api/authService';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';

export default function SignupPasswordPage() {
    const router = useRouter();
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    useEffect(() => {
        const storedEmail = sessionStorage.getItem('signup_email');
        const storedPassword = sessionStorage.getItem('signup_password');

        if (!storedEmail) {
            router.push('/signup');
            return;
        }

        setEmail(storedEmail);

        // If password already provided from login page, auto-send verification code
        if (storedPassword && storedPassword.length >= 8) {
            setPassword(storedPassword);
            setLoading(true);

            // Auto-submit to send verification code
            signupPassword({ email: storedEmail, password: storedPassword })
                .then(() => {
                    router.push('/signup/verify');
                })
                .catch((err) => {
                    setError(err instanceof Error ? err.message : 'Gagal mengirim kode');
                    setLoading(false);
                });
        }
    }, [router]);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError('');

        if (password.length < 8) {
            setError('Kata sandi harus minimal 8 karakter');
            setLoading(false);
            return;
        }

        try {
            await signupPassword({ email, password });

            // Store for next step
            sessionStorage.setItem('signup_password', password);

            router.push('/signup/verify');
        } catch (err) {
            // ✅ FIX: Properly extract error message
            let errorMessage = 'Gagal mengirim kode';

            if (err instanceof Error) {
                errorMessage = err.message;
            } else if (typeof err === 'object' && err !== null) {
                errorMessage = (err as any).detail ||
                    (err as any).message ||
                    JSON.stringify(err);
            }

            // Handle specific errors
            if (errorMessage.includes('429') || errorMessage.includes('Too Many Requests')) {
                setError('Terlalu banyak percobaan. Silakan tunggu beberapa menit.');
            } else if (errorMessage.includes('already registered')) {
                setError('Email sudah terdaftar. Silakan login.');
            } else {
                setError(errorMessage);
            }
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen flex items-center justify-center bg-muted/50 px-4">
            <div className="max-w-md w-full space-y-8 p-8 bg-card rounded-lg shadow-lg border">
                <div>
                    <h2 className="text-3xl font-bold">Buat kata sandi</h2>
                    <p className="mt-2 text-muted-foreground">
                        Anda akan menggunakan kata sandi ini untuk masuk ke ScapeGIS
                    </p>
                </div>

                <div className="bg-muted rounded-md p-3">
                    <p className="text-sm text-muted-foreground">Alamat Email</p>
                    <p className="font-medium">{email}</p>
                    <button
                        onClick={() => router.push('/signup')}
                        className="text-sm text-primary hover:underline mt-1"
                    >
                        Ubah
                    </button>
                </div>

                <form onSubmit={handleSubmit} className="space-y-6">
                    <div>
                        <label htmlFor="password" className="block text-sm font-medium mb-2">
                            Kata Sandi
                        </label>
                        <Input
                            id="password"
                            type="password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            placeholder="Minimal 8 karakter"
                            required
                            autoFocus
                        />
                        <p className="mt-1 text-xs text-muted-foreground">
                            Gunakan minimal 8 karakter
                        </p>
                    </div>

                    {error && (
                        <div className="bg-destructive/10 border border-destructive/20 rounded-md p-3 text-destructive text-sm">
                            {error}
                        </div>
                    )}

                    <Button type="submit" disabled={loading} className="w-full">
                        {loading ? 'Mengirim kode...' : 'Lanjutkan'}
                    </Button>
                </form>
            </div>
        </div>
    );
}
