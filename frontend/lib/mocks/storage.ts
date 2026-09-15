/**
 * LocalStorage utility for persisting mock data
 * Useful for maintaining state across page reloads during development
 */

const STORAGE_PREFIX = 'scapegis_mock_';

export const saveMockData = <T>(key: string, data: T): void => {
    try {
        const serialized = JSON.stringify(data);
        localStorage.setItem(`${STORAGE_PREFIX}${key}`, serialized);
    } catch (error) {
        console.error(`Failed to save mock data for ${key}:`, error);
    }
};

export const loadMockData = <T>(key: string, fallback: T): T => {
    try {
        const stored = localStorage.getItem(`${STORAGE_PREFIX}${key}`);
        if (stored) {
            return JSON.parse(stored) as T;
        }
    } catch (error) {
        console.error(`Failed to load mock data for ${key}:`, error);
    }
    return fallback;
};

export const clearMockData = (key: string): void => {
    localStorage.removeItem(`${STORAGE_PREFIX}${key}`);
};

export const clearAllMockData = (): void => {
    const keys = Object.keys(localStorage);
    keys.forEach(key => {
        if (key.startsWith(STORAGE_PREFIX)) {
            localStorage.removeItem(key);
        }
    });
};
