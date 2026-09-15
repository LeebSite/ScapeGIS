# Scapegis - AI-Assisted GIS Platform

A professional SaaS WebGIS platform built for property developers with AI-powered insights.

## Tech Stack

- **Next.js 14** (App Router)
- **React 18**
- **TypeScript**
- **Tailwind CSS**
- **Shadcn UI**
- **Zustand** (State Management)
- **React Hook Form** (Form Management)
- **Zod** (Schema Validation)

## Features

### Authentication
- User registration and login
- Role-based access control (Admin & Property Developer)
- Protected routes

### Role-Based Dashboards

#### Admin Dashboard
- User management
- Platform analytics
- System settings
- Map management

#### Property Developer Dashboard
- GIS map interface
- AI chatbot assistant
- Subscription management
- Project management

### Core Features
- **Interactive Maps**: Professional GIS mapping interface
- **AI Assistant**: Chatbot for spatial analysis and insights
- **Subscription Management**: Multiple plan tiers (Free, Basic, Professional, Enterprise)
- **Responsive Design**: Mobile-friendly interface

## Getting Started

### Prerequisites

- Node.js 18+ 
- npm or yarn

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd scapegis_saas_webgis-frontend
```

2. Install dependencies:
```bash
npm install
```

3. Run the development server:
```bash
npm run dev
```

4. Open [http://localhost:3000](http://localhost:3000) in your browser.

## Project Structure

```
├── app/                    # Next.js App Router pages
│   ├── dashboard/         # Dashboard pages
│   │   ├── admin/        # Admin-specific pages
│   │   └── developer/    # Developer-specific pages
│   ├── login/            # Authentication pages
│   └── register/
├── components/           # React components
│   ├── ai/              # AI chatbot components
│   ├── gis/             # GIS map components
│   ├── layout/          # Layout components
│   └── ui/              # Shadcn UI components
├── lib/                 # Utilities and stores
│   ├── store.ts         # Zustand state management
│   ├── types.ts         # TypeScript types
│   └── utils.ts         # Utility functions
└── public/              # Static assets
```

## Design Principles

- **Clean & Minimal**: Professional enterprise SaaS aesthetic
- **Not Flashy**: Focus on functionality over visual effects
- **Responsive**: Works on all device sizes
- **Accessible**: Following WCAG guidelines

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run start` - Start production server
- `npm run lint` - Run ESLint

## Environment Variables

Create a `.env.local` file for environment-specific configuration:

```env
# Add your environment variables here
NEXT_PUBLIC_API_URL=your_api_url
```

## License

Private - All rights reserved

