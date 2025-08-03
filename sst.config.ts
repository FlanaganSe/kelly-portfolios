/// <reference path="./.sst/platform/config.d.ts" />

export default $config({
  app(input) {
    return {
      name: "portfolio-optimizer",
      removal: input?.stage === "production" ? "retain" : "remove",
      protect: input?.stage === "production",
      home: "aws",
    };
  },
  async run() {
    new sst.aws.StaticSite("PortfolioOptimizer", {
      build: {
        command: "pnpm run build",
        output: "dist",
      },
      domain: $app.stage === "production" ? "yourdomain.com" : undefined,
      environment: {
        VITE_STAGE: $app.stage,
      },
    });
  },
});
