param (
    [Parameter(Mandatory=$true)]
    [string]$ViteApiUrl
)

$ErrorActionPreference = "Stop"

# 1. Build the frontend
Write-Host "Building frontend with VITE_API_URL = $ViteApiUrl..."
cd frontend
$env:VITE_API_URL = $ViteApiUrl
$env:GITHUB_ACTIONS = "true"

# Check if npm is installed
if (!(Get-Command npm -ErrorAction SilentlyContinue)) {
    Write-Error "npm command not found. Please install Node.js."
}

Write-Host "Running npm install..."
npm install

Write-Host "Running npm run build..."
npm run build
cd ..

# 2. Deploy to gh-pages branch
Write-Host "Deploying to gh-pages branch..."
cd frontend/dist

# Initialize temporary repository
git init
git checkout -b gh-pages
git add -A
git commit -m "Deploy frontend to GitHub Pages"

# Force push to GitHub
git remote add origin https://github.com/nithyanarikimilli/jobschedular.git
git push -f origin gh-pages

# Clean up
cd ../..
Write-Host "Deployment completed successfully! Frontend live at https://nithyanarikimilli.github.io/jobschedular/"
