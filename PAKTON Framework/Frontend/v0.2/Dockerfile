# Production Dockerfile for Open Canvas Frontend
# Multi-stage build optimized for Next.js standalone output

FROM node:20-slim AS base

# Install dependencies only when needed
FROM base AS deps
WORKDIR /app

# Copy package files for dependency installation
COPY package.json yarn.lock ./
COPY packages/shared/package.json ./packages/shared/package.json
COPY apps/web/package.json ./apps/web/package.json

# Install dependencies
RUN yarn install --frozen-lockfile

# Build the application
FROM base AS builder
WORKDIR /app

# Accept build arguments for Next.js public env variables
ARG NEXT_PUBLIC_SUPABASE_URL
ARG NEXT_PUBLIC_SUPABASE_ANON_KEY
ARG NEXT_PUBLIC_SUPABASE_URL_DOCUMENTS
ARG NEXT_PUBLIC_SUPABASE_ANON_KEY_DOCUMENTS
ARG NEXT_PUBLIC_ARCHIVIST_API_URL
ARG NODE_ENV=production
ARG LOCAL_DEVELOPMENT=false

# Set them as environment variables for the build
ENV NEXT_PUBLIC_SUPABASE_URL=$NEXT_PUBLIC_SUPABASE_URL
ENV NEXT_PUBLIC_SUPABASE_ANON_KEY=$NEXT_PUBLIC_SUPABASE_ANON_KEY
ENV NEXT_PUBLIC_SUPABASE_URL_DOCUMENTS=$NEXT_PUBLIC_SUPABASE_URL_DOCUMENTS
ENV NEXT_PUBLIC_SUPABASE_ANON_KEY_DOCUMENTS=$NEXT_PUBLIC_SUPABASE_ANON_KEY_DOCUMENTS
ENV NEXT_PUBLIC_ARCHIVIST_API_URL=$NEXT_PUBLIC_ARCHIVIST_API_URL
ENV NODE_ENV=$NODE_ENV
ENV LOCAL_DEVELOPMENT=$LOCAL_DEVELOPMENT

# Copy dependencies from deps stage
COPY --from=deps /app/node_modules ./node_modules
COPY --from=deps /app/packages/shared/node_modules ./packages/shared/node_modules
COPY --from=deps /app/apps/web/node_modules ./apps/web/node_modules

# Copy all source files
COPY . .

# Build shared package and web app
RUN yarn build

# Production image
FROM base AS runner
WORKDIR /app

# These are set at build time and baked into the image
ENV NODE_ENV=production
ENV PORT=3000

# Create non-root user
RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 nextjs

# Copy only the necessary files for production
# Next.js standalone output
COPY --from=builder --chown=nextjs:nodejs /app/apps/web/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/apps/web/.next/static ./apps/web/.next/static
COPY --from=builder --chown=nextjs:nodejs /app/apps/web/public ./apps/web/public

USER nextjs

EXPOSE 3000

# Start the Next.js app
CMD ["node", "apps/web/server.js"]