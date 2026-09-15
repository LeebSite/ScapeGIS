export const mockSubscriptionPlans = [
    {
        id: "plan-free",
        name: "Free",
        price: 0,
        currency: "USD",
        interval: "month",
        features: [
            "Up to 3 projects",
            "Basic GIS layers",
            "5 GB storage",
            "Community support"
        ],
        max_projects: 3,
        max_members: 1,
        max_storage_gb: 5,
        is_active: true
    },
    {
        id: "plan-basic",
        name: "Basic",
        price: 29,
        currency: "USD",
        interval: "month",
        features: [
            "Up to 15 projects",
            "Basic + Premium layers",
            "50 GB storage",
            "Email support",
            "Team collaboration (5 members)"
        ],
        max_projects: 15,
        max_members: 5,
        max_storage_gb: 50,
        is_active: true
    },
    {
        id: "plan-professional",
        name: "Professional",
        price: 99,
        currency: "USD",
        interval: "month",
        features: [
            "Unlimited projects",
            "All GIS layers",
            "500 GB storage",
            "Priority support",
            "Advanced AI analysis",
            "Team collaboration (20 members)",
            "API access"
        ],
        max_projects: 999,
        max_members: 20,
        max_storage_gb: 500,
        is_active: true
    }
];

export const mockUserSubscription = {
    id: "subscription-1",
    user_id: "user-1",
    plan_id: "plan-professional",
    plan_name: "Professional",
    status: "active",
    current_period_start: "2024-03-01T00:00:00Z",
    current_period_end: "2024-04-01T00:00:00Z",
    cancel_at_period_end: false,
    usage: {
        projects_used: 5,
        projects_limit: 999,
        storage_used_gb: 45.2,
        storage_limit_gb: 500,
        members_count: 3,
        members_limit: 20
    }
};

const delay = (ms: number = 500) => new Promise(resolve => setTimeout(resolve, ms));

export const getPlans = async () => {
    await delay();
    return { data: mockSubscriptionPlans };
};

export const getUserSubscription = async () => {
    await delay();
    return { data: mockUserSubscription };
};

export const upgradePlan = async (planId: string) => {
    await delay();

    const plan = mockSubscriptionPlans.find(p => p.id === planId);
    if (!plan) {
        throw new Error(`Plan ${planId} not found`);
    }

    const updatedSubscription = {
        ...mockUserSubscription,
        plan_id: planId,
        plan_name: plan.name,
        current_period_start: new Date().toISOString(),
        current_period_end: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString()
    };

    return { data: updatedSubscription };
};

export const cancelSubscription = async () => {
    await delay();

    const updatedSubscription = {
        ...mockUserSubscription,
        cancel_at_period_end: true
    };

    return { data: updatedSubscription };
};
