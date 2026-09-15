'use client';

import { useState } from 'react';
import { adminRequestMagicLink } from '@/lib/api/authService';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import Link from 'next/link';

export default function AdminLoginPage() {
    const [email, setEmail] = useState('');
    const [loading, setLoading] = useState(false);
    const [sent, setSent] = useState(false);
    const [error, setError] = useState('');

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError('');

        try {
            await adminRequestMagicLink({ email });
            setSent(true);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to send link');
        } finally {
            setLoading(false);
        }
    };

    if (sent) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-muted/50 px-4">
                <div className="max-w-md w-full p-8 bg-card rounded-lg shadow-lg border">
                    <div className="text-center">
                        <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-green-100">
                            <svg className="h-6 w-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                            </svg>
                        </div>
                        <h2 className="mt-6 text-2xl font-bold">Check your email</h2>
                        <p className="mt-2 text-muted-foreground">
                            We've sent a magic link to <strong>{email}</strong>.
                            Click the link to sign in instantly.
                        </p>
                        <p className="mt-4 text-sm text-muted-foreground">
                            The link expires in 10 minutes.
                        </p>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen flex items-center justify-center bg-muted/50 px-4">
            <div className="max-w-md w-full space-y-8 p-8 bg-card rounded-lg shadow-lg border">
                <div>
                    <div className="mx-auto h-12 w-12 flex items-center justify-center rounded-full bg-primary/10">
                        <svg className="h-6 w-6 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                        </svg>
                    </div>
                    <h2 className="mt-6 text-3xl font-bold text-center">Admin Access</h2>
                    <p className="mt-2 text-center text-muted-foreground">
                        Sign in with your admin email
                    </p>
                </div>

                <form onSubmit={handleSubmit} className="space-y-6">
                    <div>
                        <label htmlFor="email" className="block text-sm font-medium mb-2">
                            Admin Email
                        </label>
                        <Input
                            id="email"
                            type="email"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            placeholder="admin@scapegis.com"
                            required
                            autoFocus
                        />
                        <p className="mt-1 text-xs text-muted-foreground">
                            Admin access only. We'll send you a magic link.
                        </p>
                    </div>

                    {error && (
                        <div className="bg-destructive/10 border border-destructive/20 rounded-md p-3 text-destructive text-sm">
                            {error}
                        </div>
                    )}

                    <Button type="submit" disabled={loading} className="w-full">
                        {loading ? 'Sending...' : 'Send Magic Link'}
                    </Button>
                </form>

                <div className="text-center text-sm">
                    <Link href="/login" className="text-muted-foreground hover:text-foreground hover:underline">
                        ← Back to regular login
                    </Link>
                </div>
            </div>
        </div>
    );
}
