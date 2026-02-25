# Portfolio Optimizer

A web app for calculating Kelly criterion for investment portfolios. Still a work in progress!

Edit: work in progress sometime.. I've said that for 6 years now. Someday this will be picked up again though.....

Site: https://kellyportfolios.com/

## What it does (eventually)

Calculate optimal position sizing using the Kelly criterion to maximize long-term growth while managing risk across different investments.

## Tech Stack

- **SolidJS** - Fine-grained reactive UI framework
- **@solidjs/router** - Official SolidJS routing library
- **TailwindCSS** - Styling
- **Vite** - Build tool with vite-plugin-solid
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
