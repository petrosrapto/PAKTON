# GitHub Secrets Quick Reference

This is a quick reference for all GitHub Secrets needed for the PAKTON CI/CD pipelines.

## How to Add Secrets

1. Go to your GitHub repository
2. Navigate to **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Add each secret with the exact name and value

---

## EC2 Connection (Required for Dev & Prod)

### Development Environment

| Secret Name | Description |
|------------|-------------|
| `DEV_EC2_HOST` | EC2 instance IP or domain |
| `DEV_EC2_USER` | SSH username (usually `ubuntu`) |
| `DEV_EC2_SSH_KEY` | Private SSH key for EC2 access |
| `DEV_EC2_PORT` | SSH port (optional, defaults to 22) |

### Production Environment (Future)

| Secret Name | Description |
|------------|-------------|
| `PROD_EC2_HOST` | EC2 instance IP or domain |
| `PROD_EC2_USER` | SSH username |
| `PROD_EC2_SSH_KEY` | Private SSH key |
| `PROD_EC2_PORT` | SSH port (optional) |

---

## API Environment Variables

### Development

| Secret Name | Required | Example Value |
|------------|----------|---------------|
| `DEV_SUPABASE_URL` | ✅ | `https://xxxxx.supabase.co` |
| `DEV_SUPABASE_JWT_SECRET` | ✅ | `your-jwt-secret-here` |
| `DEV_ENABLE_AUTHENTICATION` | ✅ | `true` or `false` |
| `DEV_POSTGRES_DB` | ✅ | `pakton_dev` |
| `DEV_POSTGRES_USER` | ✅ | `pakton_user` |
| `DEV_POSTGRES_PASSWORD` | ✅ | `secure-password-here` |

### Production (Future)

Replace `DEV_` prefix with `PROD_` for production secrets.

---

## AI/ML Service Keys

### Development

| Secret Name | Required | Description |
|------------|----------|-------------|
| `DEV_OPENAI_API_KEY` | ✅ | OpenAI API key |
| `DEV_HUGGINGFACE_TOKEN` | ✅ | HuggingFace token |
| `DEV_EMBEDDINGS_API_KEY` | ✅ | Embeddings API key |
| `DEV_TAVILY_API_KEY` | ✅ | Tavily search API key |
| `DEV_PINECONE_API_KEY` | ✅ | Pinecone vector DB key |
| `DEV_GOOGLE_API_KEY` | ❌ | Google API key (optional) |
| `DEV_LANGCHAIN_API_KEY` | ❌ | LangSmith API key (optional) |
| `DEV_LANGCHAIN_PROJECT` | ❌ | LangSmith project name (optional) |

### Production (Future)

Replace `DEV_` prefix with `PROD_` for production secrets.

---

## AWS Configuration

### Development

| Secret Name | Required | Description |
|------------|----------|-------------|
| `DEV_AWS_ACCESS_KEY_ID` | ✅ | AWS access key ID |
| `DEV_AWS_SECRET_ACCESS_KEY` | ✅ | AWS secret access key |
| `DEV_AWS_REGION_NAME` | ✅ | AWS region (e.g., `us-west-2`) |

### Production (Future)

Replace `DEV_` prefix with `PROD_` for production secrets.

---

## Frontend Environment Variables

### Development

| Secret Name | Required | Description |
|------------|----------|-------------|
| `DEV_NEXT_PUBLIC_SUPABASE_URL` | ✅ | Supabase URL (public) |
| `DEV_NEXT_PUBLIC_SUPABASE_ANON_KEY` | ✅ | Supabase anon key |
| `DEV_NEXT_PUBLIC_SUPABASE_URL_DOCUMENTS` | ✅ | Supabase docs URL |
| `DEV_NEXT_PUBLIC_SUPABASE_ANON_KEY_DOCUMENTS` | ✅ | Supabase docs anon key |
| `DEV_NEXT_PUBLIC_GOOGLE_CLIENT_ID` | ❌ | Google OAuth client ID (optional) |
| `DEV_LOCAL_DEVELOPMENT` | ✅ | Set to `true` for dev |

### Production (Future)

Replace `DEV_` prefix with `PROD_` and set `LOCAL_DEVELOPMENT` to `false`.

---

## Checklist for Initial Setup

### Step 1: EC2 Setup
- [ ] Launch EC2 instance
- [ ] Generate SSH key pair
- [ ] Add public key to EC2 authorized_keys
- [ ] Add private key to `DEV_EC2_SSH_KEY` secret
- [ ] Add EC2 IP to `DEV_EC2_HOST` secret
- [ ] Add username to `DEV_EC2_USER` secret

### Step 2: Database Setup
- [ ] Choose PostgreSQL database name
- [ ] Choose PostgreSQL username
- [ ] Generate strong PostgreSQL password
- [ ] Add to `DEV_POSTGRES_*` secrets

### Step 3: Supabase Setup
- [ ] Create Supabase project
- [ ] Get Supabase URL
- [ ] Get JWT secret from project settings
- [ ] Get anon key
- [ ] Add to `DEV_SUPABASE_*` secrets

### Step 4: AI/ML Services
- [ ] Sign up for OpenAI → get API key → add to `DEV_OPENAI_API_KEY`
- [ ] Sign up for HuggingFace → get token → add to `DEV_HUGGINGFACE_TOKEN`
- [ ] Get embeddings key → add to `DEV_EMBEDDINGS_API_KEY`
- [ ] Sign up for Tavily → get key → add to `DEV_TAVILY_API_KEY`
- [ ] Sign up for Pinecone → get key → add to `DEV_PINECONE_API_KEY`
- [ ] (Optional) Get Google API key
- [ ] (Optional) Sign up for LangSmith → get key

### Step 5: AWS Setup
- [ ] Create AWS IAM user
- [ ] Generate access key/secret
- [ ] Add to `DEV_AWS_*` secrets
- [ ] Configure appropriate IAM permissions

### Step 6: Frontend Setup
- [ ] Add Supabase public keys to `DEV_NEXT_PUBLIC_*` secrets
- [ ] (Optional) Add Google OAuth client ID
- [ ] Set `DEV_LOCAL_DEVELOPMENT` to `true`

### Step 7: Test Deployment
- [ ] Commit to `develop` branch
- [ ] Monitor GitHub Actions
- [ ] Verify services are running
- [ ] Test API health endpoint
- [ ] Test Frontend access

---

## Security Best Practices

1. **Never commit secrets to Git**
2. **Use different secrets for dev and prod**
3. **Rotate secrets periodically**
4. **Use IAM roles with minimal permissions**
5. **Enable MFA on service accounts**
6. **Monitor secret usage in CloudWatch/logs**
7. **Use GitHub's secret scanning feature**
8. **Limit secret access to necessary workflows**

---

## Troubleshooting

### Secret not found error
- Verify secret name matches exactly (case-sensitive)
- Check secret is in repository settings, not organization
- Ensure workflow has access to secrets

### Secret value not working
- Check for trailing spaces or newlines
- Verify secret was copied completely
- Test secret value outside GitHub Actions first

### Environment file creation fails
- Check all required secrets are set
- Verify `create-env-files.sh` has execute permissions
- Check deployment logs on EC2

---

## Next Steps

After setting up dev environment secrets:
1. Set up production secrets (replace `DEV_` with `PROD_`)
2. Configure production deployment workflow
3. Set up monitoring and alerting
4. Configure backup automation
