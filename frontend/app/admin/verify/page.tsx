'use client';

import { useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { adminVerifyMagicLink } from '@/lib/api/authService';
import { Button } from '@/components/ui/button';

export default function AdminVerifyPage() {
    const router = useRouter();
    const searchParams = useSearchParams();
    const [status, setStatus] = useState<'verifying' | 'success' | 'error'>('verifying');
    const [error, setError] = useState('');

    useEffect(() => {
        const token = searchParams.get('token');

        if (!token) {
            setStatus('error');
            setError('No token provided');
            return;
        }

        verifyToken(token);
    }, [searchParams]);

    const verifyToken = async (token: string) => {
        try {
            await adminVerifyMagicLink(token);
            setStatus('success');

            setTimeout(() => {
                router.push('/dashboard/admin');
            }, 1000);
        } catch (err) {
            setStatus('error');
            setError(err instanceof Error ? err.message : 'Invalid or expired link');
        }
    };

    if (status === 'verifying') {
        return (
            <div className="min-h-screen flex items-center justify-center bg-muted/50">
                <div className="text-center">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto" />
                    <p className="mt-4 text-lg">Verifying your admin access...</p>
                </div>
            </div>
        );
    }

    if (status === 'error') {
        return (
            <div className="min-h-screen flex items-center justify-center bg-muted/50 px-4">
                <div className="max-w-md w-full p-8 bg-card rounded-lg shadow-lg border text-center">
                    <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-destructive/10">
                        <svg className="h-6 w-6 text-destructive" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                        </svg>
                    </div>
                    <h2 className="mt-6 text-2xl font-bold text-destructive">Verification Failed</h2>
                    <p className="mt-2 text-muted-foreground">{error}</p>
                    <Button
                        onClick={() => router.push('/admin/login')}
                        className="mt-6"
                    >
                        Request New Link
                    </Button>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen flex items-center justify-center bg-muted/50 px-4">
            <div className="max-w-md w-full p-8 bg-card rounded-lg shadow-lg border text-center">
                <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-green-100">
                    <svg className="h-6 w-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                </div>
                <h2 className="mt-6 text-2xl font-bold text-green-600">Success!</h2>
                <p className="mt-2 text-muted-foreground">Redirecting to dashboard...</p>
            </div>
        </div>
    );
}
