# GitHub Secrets Reference

Required GitHub Secrets for PAKTON CI/CD deployment.

## How to Add Secrets

1. Go to your GitHub repository
2. **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Add each secret below with the exact name

---

## EC2 Connection

| Secret Name | Description | Example |
|------------|-------------|---------| Example |
|------------|-------------|---------||
| `DEV_EC2_HOST` | EC2 instance public IP | `54.123.45.67` |
| `DEV_EC2_USER` | SSH username | `ubuntu` |
| `DEV_EC2_SSH_KEY` | Private SSH key (complete key including headers) | `-----BEGIN OPENSSH PRIVATE KEY-----\n...` |
| `DEV_EC2_PORT` | SSH port (optional) | `22` |

---

## API Configuration

## API Configuration

| Secret Name | Required | Description |
|------------|----------|-------------|
| `DEV_SUPABASE_URL` | ✅ | Supabase project URL |
| `DEV_SUPABASE_JWT_SECRET` | ✅ | Supabase JWT secret |
| `DEV_ENABLE_AUTHENTICATION` | ✅ | Enable auth (`true` or `false`) |
| `DEV_POSTGRES_DB` | ✅ | PostgreSQL database name |
| `DEV_POSTGRES_USER` | ✅ | PostgreSQL username |
| `DEV_POSTGRES_PASSWORD` | ✅ | PostgreSQL password |

---

## AI/ML Service Keys

| Secret Name | Required | Description |
|------------|----------|-------------|
| `DEV_OPENAI_API_KEY` | ✅ | OpenAI API key |
| `DEV_HUGGINGFACE_TOKEN` | ✅ | HuggingFace token |
| `DEV_EMBEDDINGS_API_KEY` | ✅ | Embeddings API key |
| `DEV_TAVILY_API_KEY` | ✅ | Tavily search API |
| `DEV_PINECONE_API_KEY` | ✅ | Pinecone vector DB |
| `DEV_GOOGLE_API_KEY` | ❌ | Google API (optional) |
| `DEV_LANGCHAIN_API_KEY` | ❌ | LangSmith API (optional) |
| `DEV_LANGCHAIN_PROJECT` | ❌ | LangSmith project (optional) |

---

## AWS Configuration

| Secret Name | Required | Description |
|------------|----------|-------------|
| `DEV_AWS_ACCESS_KEY_ID` | ✅ | AWS access key ID |
| `DEV_AWS_SECRET_ACCESS_KEY` | ✅ | AWS secret access key |
| `DEV_AWS_REGION_NAME` | ✅ | AWS region (e.g., `us-west-2`) |

---

## Frontend Configuration

| Secret Name | Required | Description |
|------------|----------|-------------|
| `DEV_NEXT_PUBLIC_SUPABASE_URL` | ✅ | Supabase URL (public) |
| `DEV_NEXT_PUBLIC_SUPABASE_ANON_KEY` | ✅ | Supabase anon key |
| `DEV_NEXT_PUBLIC_SUPABASE_URL_DOCUMENTS` | ✅ | Supabase docs URL |
| `DEV_NEXT_PUBLIC_SUPABASE_ANON_KEY_DOCUMENTS` | ✅ | Supabase docs key |
| `DEV_LOCAL_DEVELOPMENT` | ✅ | Set to `true` for dev |

---

## Security Best Practices

1. **Never commit secrets to Git**
2. **Rotate secrets periodically**
3. **Use IAM roles with minimal permissions**
4. **Enable MFA on service accounts**
5. **Limit secret access to necessary workflows**
6. **Use strong, unique passwords for databases**

---

**Last Updated**: November 25, 2025
