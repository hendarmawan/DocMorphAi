# syntax=docker/dockerfile:1.7
# Build context: repository root.

FROM node:22-bookworm-slim AS build
WORKDIR /repo
RUN corepack enable
COPY . .
RUN pnpm install --frozen-lockfile
# Next.js bakes rewrites in at build time, so the API address is a build argument.
ARG DOCMORPH_API_URL=http://api:8000
ENV DOCMORPH_STANDALONE=1 NEXT_TELEMETRY_DISABLED=1 DOCMORPH_API_URL=${DOCMORPH_API_URL}
RUN pnpm turbo run build --filter=@docmorph/web...

FROM node:22-bookworm-slim AS web
ENV NODE_ENV=production NEXT_TELEMETRY_DISABLED=1 PORT=3000 HOSTNAME=0.0.0.0
WORKDIR /app
COPY --from=build /repo/apps/web/.next/standalone ./
COPY --from=build /repo/apps/web/.next/static ./apps/web/.next/static
USER node
EXPOSE 3000
CMD ["node", "apps/web/server.js"]
