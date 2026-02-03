# AI-Powered Business Intelligence Analyst - Frontend

React + TypeScript frontend for the AI-Powered Business Intelligence Analyst application.

## Features

- 🎯 **Conversational Query Interface** - Natural language query input with history
- 📊 **Interactive Visualizations** - Recharts integration for dynamic charts
- 📋 **Data Tables** - Paginated data tables with export functionality
- 💡 **Query Explanation** - Detailed breakdown of agent reasoning
- 📥 **Export Options** - Export to CSV, Excel, and PDF
- 🎨 **Modern UI** - Built with Shadcn/ui and Tailwind CSS

## Prerequisites

- Node.js 18+ and npm/yarn/pnpm
- Backend API running on `http://localhost:8000`

## Setup

1. **Install dependencies:**

```bash
npm install
# or
yarn install
# or
pnpm install
```

2. **Configure environment:**

Copy `.env.example` to `.env` and adjust if needed:

```bash
cp .env.example .env
```

3. **Start development server:**

```bash
npm run dev
# or
yarn dev
# or
pnpm dev
```

The app will be available at `http://localhost:3000`.

## Project Structure

```
frontend/
├── src/
│   ├── components/          # React components
│   │   ├── ui/              # Shadcn/ui components
│   │   ├── QueryInterface.tsx
│   │   ├── QueryResults.tsx
│   │   ├── DataTable.tsx
│   │   ├── Visualization.tsx
│   │   └── ExplainQuery.tsx
│   ├── hooks/               # Custom React hooks
│   │   ├── useQuery.ts
│   │   └── useQueryHistory.ts
│   ├── lib/                  # Utilities
│   │   ├── api.ts           # API client
│   │   ├── export.ts        # Export functions
│   │   └── utils.ts         # Helper functions
│   ├── types/                # TypeScript types
│   │   └── api.ts
│   ├── App.tsx              # Main app component
│   ├── main.tsx             # Entry point
│   └── index.css            # Global styles
├── public/                   # Static assets
├── package.json
├── tsconfig.json
├── vite.config.ts
└── tailwind.config.js
```

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint
- `npm test` - Run unit tests
- `npm run test:e2e` - Run end-to-end tests

## API Integration

The frontend communicates with the backend API at `/api/v1/queries/`. The API endpoint expects:

**Request:**
```json
{
  "query": "Show me total revenue by month",
  "page": 1,
  "page_size": 100
}
```

**Response:**
```json
{
  "query_id": "uuid",
  "natural_language_query": "Show me total revenue by month",
  "generated_sql": "SELECT ...",
  "results": [...],
  "analysis": {...},
  "visualization": {...},
  "execution_time_ms": 1234.56,
  "pagination": {...},
  "cost_breakdown": {...}
}
```

## Key Components

### QueryInterface

Main component for query input and history management. Features:
- Natural language query input
- Query history sidebar
- Real-time query submission
- Keyboard shortcuts (Cmd/Ctrl + Enter)

### QueryResults

Displays query results with tabs for:
- Data table view
- Visualization charts
- Generated SQL
- Analysis and insights

### Visualization

Renders charts using Recharts based on backend visualization config:
- Line charts
- Bar charts
- Pie charts
- Auto-detection of chart type

### ExplainQuery

Modal dialog showing:
- Query explanation
- Generated SQL with syntax highlighting
- Execution details (time, cost, tokens)
- Agent pipeline breakdown

## Export Functionality

The app supports exporting query results to:
- **CSV** - Comma-separated values
- **Excel** - XLSX format with metadata sheet
- **PDF** - Formatted PDF with query details and results

## Testing

### Unit Tests

```bash
npm test
```

### End-to-End Tests

```bash
npm run test:e2e
```

E2E tests use Playwright and cover:
- Query submission flow
- Results display
- Export functionality
- Query history

## Building for Production

```bash
npm run build
```

The production build will be in the `dist/` directory.

## Deployment

The frontend can be deployed to:
- **Vercel** - Recommended for Vite apps
- **Netlify** - Static site hosting
- **AWS S3 + CloudFront** - For AWS infrastructure
- **Any static hosting** - The build output is static

Make sure to set the `VITE_API_BASE_URL` environment variable to point to your backend API.

## Troubleshooting

### API Connection Issues

If the frontend can't connect to the backend:
1. Ensure the backend is running on `http://localhost:8000`
2. Check the proxy configuration in `vite.config.ts`
3. Verify `VITE_API_BASE_URL` in `.env`

### Build Errors

If you encounter build errors:
1. Clear `node_modules` and reinstall: `rm -rf node_modules && npm install`
2. Clear Vite cache: `rm -rf node_modules/.vite`
3. Check TypeScript errors: `npm run build`

## License

See the main project README for license information.

