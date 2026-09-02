"""Client Web Portal
Svelte-based client portal for Omni Logistics users.
"""

# Omni Logistics Client Portal

Client-facing portal for Omni Logistics onboarding, billing, and support.

## Features

- Account overview for onboarding status
- Billing and subscription visibility
- Support and feedback entry points
- Tracking portal handoff links
- Responsive design

## Setup

```bash
npm install
```

## Development

```bash
npm run dev
```

Access at: http://localhost:5174

## Deployment

The client web is deployed via Netlify.

## Build

```bash
npm run build
```

## Project Structure

- `src/` - Source code
  - `components/` - Reusable Svelte components
  - `pages/` - Page components
  - `stores/` - Svelte stores
  - `api/` - API integration
  - `App.svelte` - Root component
- `static/` - Static assets
- `public/` - Public assets
