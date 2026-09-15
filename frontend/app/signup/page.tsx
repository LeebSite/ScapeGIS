'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { signupInit } from '@/lib/api/authService';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import Link from 'next/link';

export default function SignupPage() {
    const router = useRouter();
    const [email, setEmail] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError('');

        try {
            await signupInit({ email });

            // Store email in sessionStorage for next step
            sessionStorage.setItem('signup_email', email);

            router.push('/signup/password');
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to continue');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen flex items-center justify-center bg-muted/50 px-4">
            <div className="max-w-md w-full space-y-8 p-8 bg-card rounded-lg shadow-lg border">
                <div>
                    <div className="flex items-center justify-center gap-2 mb-4">
                        <img src="/img/logo_scapegis.svg" alt="Scapegis Logo" width={48} height={48} className="block" />
                        <span className="font-kayak text-2xl tracking-wide font-semibold text-[#01123E]">Scapegis</span>
                    </div>
                    <h2 className="text-3xl font-bold text-center">Create your account</h2>
                    <p className="mt-2 text-center text-muted-foreground">
                        Get started with ScapeGIS
                    </p>
                </div>

                <form onSubmit={handleSubmit} className="space-y-6">
                    <div>
                        <label htmlFor="email" className="block text-sm font-medium mb-2">
                            Email address
                        </label>
                        <Input
                            id="email"
                            type="email"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            placeholder="you@example.com"
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
                        disabled={loading}
                        className="w-full"
                    >
                        {loading ? 'Checking...' : 'Continue'}
                    </Button>
                </form>

                <div className="text-center text-sm">
                    <span className="text-muted-foreground">Already have an account? </span>
                    <Link href="/login" className="text-primary hover:underline font-medium">
                        Sign in
                    </Link>
                </div>
            </div>
        </div>
    );
}
