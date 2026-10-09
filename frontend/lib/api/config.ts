/**
 * API Configuration - Feature Flags for Mock Data
 * 
 * Controls which features use mock data vs real API endpoints.
 * After backend cleanup, only Auth & Admin use real API.
 */

// Read from environment variables or use defaults
const USE_MOCK_DATA = process.env.NEXT_PUBLIC_USE_MOCK_DATA === 'true' || true;

export const API_CONFIG = {
    // ✅ Real API - Always use backend
    USE_REAL_AUTH: true,
    USE_REAL_ADMIN: true,

    // 🎭 Mock Data - Until backend implements these features
    USE_MOCK_WORKSPACE: USE_MOCK_DATA,
    USE_MOCK_PROJECT: USE_MOCK_DATA,
    USE_MOCK_LAYER: USE_MOCK_DATA,
    USE_MOCK_SUBSCRIPTION: USE_MOCK_DATA,

    // Spatial AI - Connected to backend (/api/v1/spatial-ai/chat, /analyze)
    USE_MOCK_AI: false, // Real backend endpoints active
    USE_MOCK_INVITATION: true, // Always mock since removed from backend

    // Mock behavior settings
    ENABLE_MOCK_DELAY: true, // Simulate network latency
    MOCK_DELAY_MS: 500, // Default delay in milliseconds
} as const;

/**
 * Get mock delay based on config
 */
export const getMockDelay = (): number => {
    return API_CONFIG.ENABLE_MOCK_DELAY ? API_CONFIG.MOCK_DELAY_MS : 0;
};

/**
 * Helper to check if we should use mock for a feature
 */
export const shouldUseMock = (feature: keyof typeof API_CONFIG): boolean => {
    const value = API_CONFIG[feature];
    return typeof value === 'boolean' ? value : false;
};

/**
 * Log configuration on app start
 */
if (typeof window !== 'undefined' && process.env.NODE_ENV === 'development') {
    console.group('🔧 ScapeGIS API Configuration');
    console.log('Environment:', process.env.NODE_ENV);
    console.table({
        'Auth (Real API)': API_CONFIG.USE_REAL_AUTH ? '✅' : '❌',
        'Admin (Real API)': API_CONFIG.USE_REAL_ADMIN ? '✅' : '❌',
        'Workspace': API_CONFIG.USE_MOCK_WORKSPACE ? '🎭 Mock' : '✅ Real',
        'Project': API_CONFIG.USE_MOCK_PROJECT ? '🎭 Mock' : '✅ Real',
        'Layer': API_CONFIG.USE_MOCK_LAYER ? '🎭 Mock' : '✅ Real',
        'Subscription': API_CONFIG.USE_MOCK_SUBSCRIPTION ? '🎭 Mock' : '✅ Real',
    });
    console.groupEnd();
}
