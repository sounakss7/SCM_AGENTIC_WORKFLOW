# Vercel Deployment Setup

## Configuration Files

### vercel.json
- **buildCommand**: Installs dependencies and builds the frontend
- **outputDirectory**: Points to `frontend/dist` (Vite build output)
- **framework**: Set to 'vite' for proper optimization
- **nodeVersion**: 20.x for latest LTS support

### .vercelignore
- Excludes backend, environment files, and unnecessary files from deployment
- Only relevant frontend files are deployed

### .nvmrc
- Specifies Node.js version 20 for consistent builds

## Build Process

1. Vercel clones the repository
2. Navigates to frontend directory
3. Runs `npm ci --legacy-peer-deps` (clean install)
4. Runs build script in sequence:
   - TypeScript compilation: `tsc -b`
   - Vite build: `vite build`
5. Output from `frontend/dist` is deployed

## Troubleshooting

If build fails:
1. Ensure all commits are pushed to `main` branch
2. Check Node version compatibility
3. Verify package-lock.json is current
4. Clear Vercel build cache and redeploy

## Local Testing

```bash
cd frontend
npm ci --legacy-peer-deps
npm run build
npm run preview
```

