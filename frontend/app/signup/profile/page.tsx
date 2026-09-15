'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { signupComplete, getCurrentUser } from '@/lib/api/authService';
import { useAuthStore } from '@/lib/store';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';

export default function SignupProfilePage() {
    const router = useRouter();
    const setUser = useAuthStore((state) => state.setUser);
    const [email, setEmail] = useState('');
    const [tempToken, setTempToken] = useState('');
    const [name, setName] = useState('');
    const [birthday, setBirthday] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    useEffect(() => {
        const storedEmail = sessionStorage.getItem('signup_email');
        const storedToken = sessionStorage.getItem('signup_temp_token');

        if (!storedEmail || !storedToken) {
            router.push('/signup');
            return;
        }

        setEmail(storedEmail);
        setTempToken(storedToken);
    }, [router]);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError('');

        // ✅ Validate birthday format (YYYY-MM-DD)
        const dateRegex = /^\d{4}-\d{2}-\d{2}$/;
        if (!dateRegex.test(birthday)) {
            setError('Format tanggal lahir salah. Silakan pilih tanggal yang valid.');
            setLoading(false);
            return;
        }

        // ✅ Debug: Log request payload
        console.log('📋 Signup Complete Request:', {
            email,
            temp_token: tempToken,
            name,
            birthday  // Should be YYYY-MM-DD
        });

        try {
            // ✅ FIX: Capture tokens and store in localStorage
            const tokens = await signupComplete({
                email,
                temp_token: tempToken,
                name,
                birthday  // Already in YYYY-MM-DD format from date input
            });

            if (tokens && tokens.access_token) {
                localStorage.setItem('access_token', tokens.access_token);
                if (tokens.refresh_token) {
                    localStorage.setItem('refresh_token', tokens.refresh_token);
                }
            }

            // Fetch user and update store
            const user = await getCurrentUser();
            setUser(user);

            // Clear signup data
            sessionStorage.removeItem('signup_email');
            sessionStorage.removeItem('signup_password');
            sessionStorage.removeItem('signup_temp_token');

            // Redirect to login (tokens should be set by backend via cookies)
            router.push('/dashboard/developer');
        } catch (err) {
            const errorMessage = err instanceof Error ? err.message : 'Gagal membuat akun';
            console.error('❌ Signup Complete Error:', errorMessage);
            setError(errorMessage);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen flex items-center justify-center bg-muted/50 px-4">
            <div className="max-w-md w-full space-y-8 p-8 bg-card rounded-lg shadow-lg border">
                <div>
                    <h2 className="text-3xl font-bold">Konfirmasi usia Anda</h2>
                    <p className="mt-2 text-muted-foreground">
                        Ini membantu kami mempersonalisasi pengalaman Anda dan memberikan
                        pengaturan yang tepat, sesuai dengan Kebijakan Privasi kami
                    </p>
                </div>

                <form onSubmit={handleSubmit} className="space-y-6">
                    <div>
                        <label htmlFor="name" className="block text-sm font-medium mb-2">
                            Nama Lengkap
                        </label>
                        <Input
                            id="name"
                            type="text"
                            value={name}
                            onChange={(e) => setName(e.target.value)}
                            placeholder="John Doe"
                            required
                            autoFocus
                        />
                    </div>

                    <div>
                        <label htmlFor="birthday" className="block text-sm font-medium mb-2">
                            Tanggal Lahir
                        </label>
                        <Input
                            id="birthday"
                            type="date"
                            value={birthday}
                            onChange={(e) => setBirthday(e.target.value)}
                            required
                        />
                    </div>

                    {error && (
                        <div className="bg-destructive/10 border border-destructive/20 rounded-md p-3 text-destructive text-sm">
                            {error}
                        </div>
                    )}

                    <div className="text-xs text-muted-foreground">
                        Dengan mengklik "Lanjutkan", Anda menyetujui{' '}
                        <a href="/terms" className="text-primary hover:underline">Syarat & Ketentuan</a>
                        {' '}dan telah membaca{' '}
                        <a href="/privacy" className="text-primary hover:underline">Kebijakan Privasi</a> kami.
                    </div>

                    <Button type="submit" disabled={loading} className="w-full">
                        {loading ? 'Membuat akun...' : 'Lanjutkan'}
                    </Button>
                </form>
            </div>
        </div>
    );
}
