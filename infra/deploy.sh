#!/usr/bin/env bash
set -euo pipefail

# SchoolSkim AWS infrastructure deployment
# Prerequisites: aws-cli, aws-sam-cli, configured AWS credentials
#
# Usage:
#   ./infra/deploy.sh              # Deploy to prod
#   STAGE=dev ./infra/deploy.sh    # Deploy to dev

STAGE="${STAGE:-prod}"
STACK_NAME="schoolskim-${STAGE}"
REGION="us-east-1"  # SES inbound only works in specific regions

echo "Deploying SchoolSkim infrastructure (stage: ${STAGE})..."
echo ""

# Check prerequisites
command -v aws >/dev/null 2>&1 || { echo "Error: aws-cli not installed. Run: brew install awscli"; exit 1; }
command -v sam >/dev/null 2>&1 || { echo "Error: aws-sam-cli not installed. Run: brew install aws-sam-cli"; exit 1; }

# Prompt for Anthropic API key if not in environment
if [ -z "${ANTHROPIC_API_KEY:-}" ]; then
    echo -n "Enter your Anthropic API key: "
    read -rs ANTHROPIC_API_KEY
    echo ""
fi

# Build
echo "Building Lambda functions..."
sam build \
    --template-file infra/template.yaml \
    --build-dir .aws-sam/build \
    --use-container

# Deploy
echo "Deploying stack: ${STACK_NAME}..."
sam deploy \
    --template-file .aws-sam/build/template.yaml \
    --stack-name "${STACK_NAME}" \
    --region "${REGION}" \
    --capabilities CAPABILITY_IAM \
    --parameter-overrides \
        "Stage=${STAGE}" \
        "AnthropicApiKey=${ANTHROPIC_API_KEY}" \
    --no-confirm-changeset \
    --resolve-s3

echo ""
echo "Stack deployed. Outputs:"
aws cloudformation describe-stacks \
    --stack-name "${STACK_NAME}" \
    --region "${REGION}" \
    --query "Stacks[0].Outputs" \
    --output table

echo ""
echo "=== MANUAL STEPS REMAINING ==="
echo ""
echo "1. VERIFY DOMAIN IN SES:"
echo "   aws ses verify-domain-identity --domain schoolskim.com --region ${REGION}"
echo "   Then add the TXT record it gives you to Cloudflare DNS."
echo ""
echo "2. ADD MX RECORD IN CLOUDFLARE:"
echo "   Type: MX"
echo "   Name: @"
echo "   Mail server: inbound-smtp.${REGION}.amazonaws.com"
echo "   Priority: 10"
echo ""
echo "3. ACTIVATE SES RECEIPT RULE SET:"
echo "   aws ses set-active-receipt-rule-set --rule-set-name schoolskim-${STAGE} --region ${REGION}"
echo ""
echo "4. REQUEST SES PRODUCTION ACCESS (if still in sandbox):"
echo "   Go to SES console → Account dashboard → Request production access"
echo ""
echo "5. ADD VERCEL ENV VARS:"
echo "   AWS_REGION=${REGION}"
echo "   USERS_TABLE=schoolskim-users-${STAGE}"
echo ""
