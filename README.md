# Portfolio Optimizer

A web app for calculating Kelly criterion for investment portfolios. Still a work in progress!

Site: https://kellyportfolios.com/

## What it does (eventually)

Calculate optimal position sizing using the Kelly criterion to maximize long-term growth while managing risk across different investments.

## Tech Stack

- **Preact** - Lightweight React alternative
- **Wouter** - Lightweight Router
- **TailwindCSS** - Styling
- **Vite** - Build tool
- **SST v3** - AWS deployment built on pulumi

## Development

```bash
# Requirements
brew install pnpm
brew install awscli

# Set up pre-push hook 
pnpm setup

# Install dependencies
pnpm install

# Start dev server
pnpm dev

# Deploy to AWS
pnpm sst deploy --stage <stage>
```

## Misc

- Under construction... Obviously. 
- Significant claude code usage. This is largely just a for-fun project. 