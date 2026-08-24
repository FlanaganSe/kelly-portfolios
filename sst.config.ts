/// <reference path="./.sst/platform/config.d.ts" />

export default $config({
  app(input) {
    return {
      name: "portfolio-optimizer",
      removal: input?.stage === "production" ? "retain" : "remove",
      protect: ["production"].includes(input?.stage),
      home: "aws",
    };
  },
  async run() {
    // Import infrastructure modules (imported for side effects - creating AWS resources)
    await import("./infra/storage");
    await import("./infra/database");
    const { api } = await import("./infra/api");
    // await import("./infra/ingestion");
    // await import("./infra/monitoring");

    // Create static site with API URL environment variable
    const site = new sst.aws.StaticSite("PortfolioOptimizer", {
      build: {
        command: "pnpm run build",
        output: "dist",
      },
      // The client is a single-page app with real URLs (`/portfolios/candidate`).
      // Without this, a direct load or a refresh of any route but `/` returns the
      // bucket's 404 rather than the app.
      errorPage: "index.html",
      environment: {
        VITE_API_URL: api.url,
      },
    });

    return {
      api: api.url,
      site: site.url,
    };
  },
});
