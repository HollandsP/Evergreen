# Installation Guide - Evergreen Web Application

## Prerequisites

Before you begin, ensure you have the following installed:

- **Node.js**: Version 18.17 or later
- **npm**: Version 9.0 or later (comes with Node.js)
- **Git**: For cloning the repository
- **A code editor**: VS Code recommended

## Step-by-Step Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd Evergreen/web
```

### 2. Install Dependencies

```bash
npm install
```

This will install all required packages including:
- Next.js 14
- React 18
- TypeScript
- Tailwind CSS
- UI components (Radix UI)
- And more...

### 3. Set Up Environment Variables

Copy the example environment file:

```bash
cp .env.example .env.local
```

Edit `.env.local` and add your API keys:

```env
# Required API Keys
OPENAI_API_KEY=sk-your-openai-api-key-here
ELEVENLABS_API_KEY=your-elevenlabs-api-key-here

# Optional (for full functionality)
RUNWAY_API_KEY=your-runway-api-key-here
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
```

### 4. Run the Development Server

```bash
npm run dev
```

The application will be available at [http://localhost:3000](http://localhost:3000)

## Common Installation Issues

### Issue: Module not found errors

**Solution:**
```bash
rm -rf node_modules package-lock.json
npm install
```

### Issue: TypeScript errors

**Solution:**
```bash
npm run type-check
```

If there are errors, they need to be fixed before the build will succeed.

### Issue: Port 3000 already in use

**Solution:**
```bash
# On macOS/Linux
lsof -ti:3000 | xargs kill -9

# On Windows
netstat -ano | findstr :3000
taskkill /PID <PID> /F
```

### Issue: Missing UI components

The UI components are already included in the `/components/ui` directory. If you see import errors, ensure you've run `npm install` to install all dependencies.

### Issue: Environment variables not loading

1. Ensure `.env.local` exists (not `.env`)
2. Restart the development server after making changes
3. Check that variable names start with `NEXT_PUBLIC_` for client-side variables

## Verifying Installation

Run these commands to verify everything is set up correctly:

```bash
# Check Node.js version
node --version  # Should be 18.17 or later

# Check npm version
npm --version   # Should be 9.0 or later

# Check TypeScript compilation
npm run type-check

# Check linting
npm run lint

# Build the project
npm run build
```

## Project Structure

After installation, your project structure should look like this:

```
web/
├── components/       # React components
│   ├── ui/          # UI components (Button, Card, etc.)
│   ├── stages/      # Production stage components
│   └── shared/      # Shared components
├── pages/           # Next.js pages
│   ├── api/         # API routes
│   └── production/  # Production workflow pages
├── lib/             # Utilities and helpers
├── types/           # TypeScript types
├── styles/          # Global styles
├── public/          # Static assets
├── .env.local       # Environment variables (create this)
├── package.json     # Dependencies
├── tsconfig.json    # TypeScript config
└── tailwind.config.js # Tailwind CSS config
```

## Next Steps

1. **Start the backend API server** (see main project README)
2. **Configure your API keys** in `.env.local`
3. **Run the development server**: `npm run dev`
4. **Open the application**: [http://localhost:3000](http://localhost:3000)

## Getting Help

If you encounter issues:

1. Check the console for error messages
2. Review the TypeScript errors: `npm run type-check`
3. Check the main project documentation
4. Open an issue on GitHub with:
   - Error messages
   - Steps to reproduce
   - Your environment (OS, Node version, etc.)

## Production Build

To build for production:

```bash
npm run build
npm start
```

For deployment, see the deployment section in the README.md file.