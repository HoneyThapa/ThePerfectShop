#!/bin/bash

# ThePerfectShop AWS Deployment Script
# This script automates the deployment to AWS ECS

set -e

# Configuration
PROJECT_NAME="theperfectshop"
AWS_REGION="us-east-1"
STACK_NAME="${PROJECT_NAME}-infrastructure"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check AWS CLI
    if ! command -v aws &> /dev/null; then
        log_error "AWS CLI is not installed. Please install AWS CLI first."
        exit 1
    fi
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    # Check AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        log_error "AWS credentials not configured. Run 'aws configure' first."
        exit 1
    fi
    
    log_success "Prerequisites check completed"
}

# Get AWS account ID
get_account_id() {
    aws sts get-caller-identity --query Account --output text
}

# Deploy CloudFormation stack
deploy_infrastructure() {
    log_info "Deploying AWS infrastructure..."
    
    aws cloudformation deploy \
        --template-file aws-infrastructure.yaml \
        --stack-name $STACK_NAME \
        --capabilities CAPABILITY_IAM \
        --region $AWS_REGION \
        --parameter-overrides ProjectName=$PROJECT_NAME
    
    log_success "Infrastructure deployed successfully"
}

# Build and push Docker image
build_and_push_image() {
    log_info "Building and pushing Docker image..."
    
    ACCOUNT_ID=$(get_account_id)
    ECR_URI="${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${PROJECT_NAME}-backend"
    
    # Login to ECR
    aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ECR_URI
    
    # Build image
    docker build -t $PROJECT_NAME-backend .
    
    # Tag image
    docker tag $PROJECT_NAME-backend:latest $ECR_URI:latest
    
    # Push image
    docker push $ECR_URI:latest
    
    log_success "Docker image pushed successfully"
}

# Update ECS service
update_service() {
    log_info "Updating ECS service..."
    
    aws ecs update-service \
        --cluster $PROJECT_NAME-cluster \
        --service $PROJECT_NAME-service \
        --force-new-deployment \
        --region $AWS_REGION
    
    log_success "ECS service updated successfully"
}

# Get service URL
get_service_url() {
    log_info "Getting service information..."
    
    # Get task ARN
    TASK_ARN=$(aws ecs list-tasks \
        --cluster $PROJECT_NAME-cluster \
        --service-name $PROJECT_NAME-service \
        --query 'taskArns[0]' \
        --output text \
        --region $AWS_REGION)
    
    if [ "$TASK_ARN" != "None" ] && [ "$TASK_ARN" != "" ]; then
        # Get task details
        PUBLIC_IP=$(aws ecs describe-tasks \
            --cluster $PROJECT_NAME-cluster \
            --tasks $TASK_ARN \
            --query 'tasks[0].attachments[0].details[?name==`networkInterfaceId`].value' \
            --output text \
            --region $AWS_REGION)
        
        if [ "$PUBLIC_IP" != "" ]; then
            # Get the actual public IP
            PUBLIC_IP=$(aws ec2 describe-network-interfaces \
                --network-interface-ids $PUBLIC_IP \
                --query 'NetworkInterfaces[0].Association.PublicIp' \
                --output text \
                --region $AWS_REGION)
            
            log_success "Service deployed successfully!"
            log_info "API URL: http://$PUBLIC_IP:8000"
            log_info "Health Check: http://$PUBLIC_IP:8000/health"
            log_info "API Documentation: http://$PUBLIC_IP:8000/docs"
        fi
    fi
}

# Main deployment function
main() {
    log_info "Starting ThePerfectShop AWS deployment..."
    
    check_prerequisites
    deploy_infrastructure
    build_and_push_image
    update_service
    
    log_info "Waiting for service to stabilize..."
    sleep 30
    
    get_service_url
    
    log_success "Deployment completed successfully!"
}

# Show help
show_help() {
    cat << EOF
ThePerfectShop AWS Deployment Script

Usage: $0 [COMMAND]

Commands:
    deploy          Deploy the complete infrastructure and application
    build           Build and push Docker image only
    update          Update ECS service only
    status          Show deployment status
    cleanup         Clean up AWS resources
    help            Show this help message

Examples:
    $0 deploy       # Full deployment
    $0 build        # Build and push image
    $0 update       # Update service
EOF
}

# Handle commands
case "${1:-deploy}" in
    deploy)
        main
        ;;
    build)
        check_prerequisites
        build_and_push_image
        ;;
    update)
        check_prerequisites
        update_service
        get_service_url
        ;;
    status)
        get_service_url
        ;;
    cleanup)
        log_warning "This will delete all AWS resources. Are you sure? (y/N)"
        read -r response
        if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
            aws cloudformation delete-stack --stack-name $STACK_NAME --region $AWS_REGION
            log_success "Cleanup initiated"
        fi
        ;;
    help)
        show_help
        ;;
    *)
        log_error "Unknown command: $1"
        show_help
        exit 1
        ;;
esac