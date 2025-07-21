# AWS Setup Quick Guide for AI Content Pipeline

## 🔍 Finding Your AWS Credentials

### Step 1: Sign in to AWS Console
1. Go to https://console.aws.amazon.com/
2. Sign in with your email and password

### Step 2: Create IAM User
1. In the search bar at top, type **"IAM"** and click on **IAM**
2. In left sidebar, click **"Users"**
3. Click blue **"Create user"** button
4. User name: `ai-pipeline-user`
5. Click **"Next"**

### Step 3: Set Permissions
1. Select **"Attach policies directly"**
2. In the search box, search and check these policies:
   - ✅ **AmazonS3FullAccess**
   - ✅ **CloudFrontFullAccess** (optional)
3. Click **"Next"** → **"Create user"**

### Step 4: Create Access Keys 🔑
1. Click on your new user `ai-pipeline-user`
2. Go to **"Security credentials"** tab
3. Scroll down to **"Access keys"**
4. Click **"Create access key"**
5. Select **"Application running outside AWS"**
6. Click **"Next"** → **"Create access key"**

### Step 5: Save Your Keys! ⚠️
**IMPORTANT: You can only see the Secret Access Key ONCE!**

You'll see:
```
Access key ID: AKIAIOSFODNN7EXAMPLE
Secret access key: wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
```

**Copy both immediately!**

### Step 6: Create S3 Bucket
1. In search bar, type **"S3"** and click on **S3**
2. Click **"Create bucket"**
3. Bucket name: `ai-content-pipeline-media` (must be globally unique)
4. Region: Select **US East (N. Virginia) us-east-1** (or your preference)
5. Uncheck **"Block all public access"** (we need to serve videos)
   - Check the acknowledgment box
6. Leave other settings as default
7. Click **"Create bucket"**

### Step 7: Add to Your .env File

Open `/mnt/c/Users/holla/OneDrive/Desktop/CodeProjects/Evergreen/.env` and add:

```env
# AWS Credentials
AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
AWS_REGION=us-east-1
S3_BUCKET=ai-content-pipeline-media
```

---

## 🧪 Test Your Setup

### Option 1: Test with Python
```python
import boto3

# Test connection
s3 = boto3.client('s3',
    aws_access_key_id='YOUR_ACCESS_KEY',
    aws_secret_access_key='YOUR_SECRET_KEY',
    region_name='us-east-1'
)

# List buckets
buckets = s3.list_buckets()
print("Your buckets:", [b['Name'] for b in buckets['Buckets']])
```

### Option 2: Test with AWS CLI
```bash
# Install AWS CLI first if needed:
pip install awscli

# Configure
aws configure
# Enter your keys when prompted

# Test
aws s3 ls
aws s3 ls s3://ai-content-pipeline-media
```

---

## 🚨 Common Issues

### "Invalid bucket name"
- Bucket names must be globally unique
- Try adding random numbers: `ai-content-pipeline-media-12345`

### "Access Denied"
- Make sure you attached the S3FullAccess policy
- Check that keys are copied correctly (no extra spaces)

### "Region error"
- Ensure AWS_REGION in .env matches bucket region

---

## 📋 Checklist

- [ ] Created IAM user
- [ ] Attached S3FullAccess policy
- [ ] Generated Access Keys
- [ ] Created S3 bucket
- [ ] Added credentials to .env
- [ ] Tested connection

---

## 🔐 Security Tips

1. **Never commit .env to Git!** (already in .gitignore)
2. **Rotate keys regularly** (every 90 days)
3. **Use IAM roles in production** instead of keys
4. **Enable MFA** on your AWS account

---

## Next Steps

Once you have your AWS credentials in the .env file:

```bash
# Restart Docker to load new env vars
docker-compose down
docker-compose up -d

# Test S3 upload in the API
curl -X POST http://localhost:8000/api/v1/test-s3
```

Your pipeline is now ready to store videos in S3! 🎉