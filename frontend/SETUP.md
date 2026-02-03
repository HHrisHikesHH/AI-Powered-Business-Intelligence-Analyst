# Frontend Setup Guide

## Quick Start

1. **Install dependencies:**
   ```bash
   cd frontend
   npm install
   ```

2. **Start development server:**
   ```bash
   npm run dev
   ```

3. **Open browser:**
   Navigate to `http://localhost:3000`

## Prerequisites

- Node.js 18+ (check with `node --version`)
- npm, yarn, or pnpm
- Backend API running on `http://localhost:8000`

## Installation Steps

### 1. Install Node.js Dependencies

```bash
npm install
```

This will install all required packages including:
- React 18
- TypeScript
- Vite
- TanStack Query
- Recharts
- Shadcn/ui components
- Export libraries (jsPDF, xlsx)

### 2. Configure Environment

Create a `.env` file in the `frontend/` directory:

```bash
cp .env.example .env
```

Edit `.env` if your backend API is on a different URL:

```env
VITE_API_BASE_URL=/api/v1
```

### 3. Start Development Server

```bash
npm run dev
```

The app will be available at `http://localhost:3000`.

### 4. Verify Backend Connection

Make sure the backend API is running:

```bash
# In the backend directory
cd ../backend
source venv/bin/activate
uvicorn app.main:app --reload
```

The backend should be running on `http://localhost:8000`.

## Development Workflow

### Running Tests

**Unit Tests:**
```bash
npm test
```

**End-to-End Tests:**
```bash
# Start the dev server first, then in another terminal:
npm run test:e2e
```

### Building for Production

```bash
npm run build
```

The production build will be in the `dist/` directory.

### Preview Production Build

```bash
npm run preview
```

## Troubleshooting

### Port Already in Use

If port 3000 is already in use, Vite will automatically try the next available port. Check the terminal output for the actual port.

### API Connection Errors

1. **Check backend is running:**
   ```bash
   curl http://localhost:8000/health
   ```

2. **Check proxy configuration:**
   The `vite.config.ts` includes a proxy that forwards `/api` requests to `http://localhost:8000`. Verify this is correct.

3. **Check CORS:**
   Ensure the backend has CORS enabled for `http://localhost:3000`.

### Build Errors

1. **Clear cache and reinstall:**
   ```bash
   rm -rf node_modules package-lock.json
   npm install
   ```

2. **Check TypeScript errors:**
   ```bash
   npm run build
   ```

3. **Check for missing dependencies:**
   If you see import errors, ensure all packages are installed:
   ```bash
   npm install --save <package-name>
   ```

### Styling Issues

If Tailwind CSS styles aren't working:

1. **Verify Tailwind config:**
   Check `tailwind.config.js` is properly configured.

2. **Check PostCSS:**
   Ensure `postcss.config.js` is present.

3. **Restart dev server:**
   Sometimes a restart fixes styling issues.

## Project Structure

```
frontend/
├── src/
│   ├── components/       # React components
│   │   ├── ui/           # Shadcn/ui base components
│   │   ├── QueryInterface.tsx
│   │   ├── QueryResults.tsx
│   │   ├── DataTable.tsx
│   │   ├── Visualization.tsx
│   │   └── ExplainQuery.tsx
│   ├── hooks/            # Custom React hooks
│   ├── lib/              # Utilities and API client
│   ├── types/            # TypeScript type definitions
│   ├── App.tsx           # Main app component
│   └── main.tsx          # Entry point
├── tests/                # Test files
│   └── e2e/             # End-to-end tests
├── public/               # Static assets
├── package.json
├── tsconfig.json
├── vite.config.ts
└── tailwind.config.js
```

## Next Steps

1. **Test the application:**
   - Submit a test query
   - Check query history
   - Try export functionality
   - View visualizations

2. **Customize styling:**
   - Edit `tailwind.config.js` for theme customization
   - Modify `src/index.css` for global styles

3. **Add features:**
   - Extend components as needed
   - Add new API endpoints
   - Enhance visualizations

## Support

For issues or questions:
1. Check the main project README
2. Review backend API documentation
3. Check browser console for errors
4. Review network tab for API requests

