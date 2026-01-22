#!/bin/bash
# One-click deployment script for Socratic Parent
# Supports multiple platforms: Railway, Render, Fly.io, or GitHub Pages only

set -e

# Colors
CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BOLD='\033[1m'
NC='\033[0m'

echo -e "${BOLD}${CYAN}"
echo "======================================================================"
echo "  🎓 SOCRATIC PARENT - DEPLOYMENT WIZARD"
echo "======================================================================"
echo -e "${NC}"

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if we're in a git repo
check_git_repo() {
    if ! git rev-parse --git-dir > /dev/null 2>&1; then
        echo -e "${RED}✗ Not a git repository${NC}"
        echo -e "${YELLOW}Initializing git repository...${NC}"
        git init
        git add .
        git commit -m "Initial commit"
        echo -e "${GREEN}✓ Git repository initialized${NC}"
    fi
}

# Function to deploy to GitHub Pages
deploy_github_pages() {
    echo -e "\n${BOLD}Deploying GitHub Pages...${NC}"
    
    check_git_repo
    
    # Check if remote exists
    if ! git remote | grep -q "origin"; then
        echo -e "${YELLOW}Please add a GitHub remote:${NC}"
        read -p "Enter your GitHub repository URL (e.g., https://github.com/username/SocraticParent.git): " repo_url
        git remote add origin "$repo_url"
    fi
    
    # Push to GitHub
    echo -e "${YELLOW}Pushing to GitHub...${NC}"
    git add .
    git commit -m "Deploy GitHub Pages" || true
    git push -u origin main || git push -u origin master
    
    echo -e "\n${GREEN}✓ GitHub Pages deployment initiated!${NC}"
    echo -e "\n${CYAN}Next steps:${NC}"
    echo -e "1. Go to your repository settings on GitHub"
    echo -e "2. Navigate to 'Pages' section"
    echo -e "3. GitHub Actions should automatically deploy your site"
    echo -e "4. Your site will be available at: https://USERNAME.github.io/REPO-NAME/"
    echo -e "\n${YELLOW}Note: GitHub Pages hosts the frontend only. Users need their own Gemini API key.${NC}"
}

# Function to deploy to Railway
deploy_railway() {
    echo -e "\n${BOLD}Deploying to Railway...${NC}"
    
    if ! command_exists railway; then
        echo -e "${YELLOW}Railway CLI not found. Installing...${NC}"
        npm i -g @railway/cli || {
            echo -e "${RED}✗ Failed to install Railway CLI${NC}"
            echo -e "${YELLOW}Install manually: npm i -g @railway/cli${NC}"
            exit 1
        }
    fi
    
    check_git_repo
    
    # Login to Railway
    echo -e "${YELLOW}Logging into Railway...${NC}"
    railway login
    
    # Initialize project
    if ! railway status > /dev/null 2>&1; then
        echo -e "${YELLOW}Initializing Railway project...${NC}"
        railway init
    fi
    
    # Set environment variable
    echo -e "${YELLOW}Setting environment variables...${NC}"
    read -p "Enter your Gemini API Key: " api_key
    railway variables set GEMINI_API_KEY="$api_key"
    
    # Deploy
    echo -e "${YELLOW}Deploying...${NC}"
    railway up
    
    echo -e "\n${GREEN}✓ Railway deployment complete!${NC}"
    echo -e "\n${CYAN}Get your deployment URL:${NC}"
    railway open
}

# Function to deploy to Render
deploy_render() {
    echo -e "\n${BOLD}Deploying to Render...${NC}"
    
    check_git_repo
    
    echo -e "${CYAN}Steps to deploy on Render:${NC}"
    echo -e "1. Push your code to GitHub (if not done already)"
    echo -e "2. Go to https://render.com"
    echo -e "3. Click 'New +' → 'Blueprint'"
    echo -e "4. Connect your GitHub repository"
    echo -e "5. Render will detect the render.yaml file automatically"
    echo -e "6. Set your GEMINI_API_KEY in environment variables"
    echo -e "7. Click 'Apply'"
    
    read -p "Press Enter to push to GitHub and open Render dashboard..." 
    
    git add .
    git commit -m "Deploy to Render" || true
    git push origin main || git push origin master
    
    # Open Render dashboard
    if command_exists open; then
        open "https://dashboard.render.com/"
    elif command_exists xdg-open; then
        xdg-open "https://dashboard.render.com/"
    else
        echo -e "\n${CYAN}Open in browser: https://dashboard.render.com/${NC}"
    fi
}

# Function to deploy to Fly.io
deploy_fly() {
    echo -e "\n${BOLD}Deploying to Fly.io...${NC}"
    
    if ! command_exists flyctl; then
        echo -e "${YELLOW}Fly CLI not found. Installing...${NC}"
        curl -L https://fly.io/install.sh | sh
        echo -e "${GREEN}Please restart your terminal and run this script again${NC}"
        exit 0
    fi
    
    # Login
    echo -e "${YELLOW}Logging into Fly.io...${NC}"
    flyctl auth login
    
    # Launch app
    echo -e "${YELLOW}Launching app...${NC}"
    flyctl launch --no-deploy
    
    # Set secrets
    read -p "Enter your Gemini API Key: " api_key
    flyctl secrets set GEMINI_API_KEY="$api_key"
    
    # Deploy
    echo -e "${YELLOW}Deploying...${NC}"
    flyctl deploy
    
    echo -e "\n${GREEN}✓ Fly.io deployment complete!${NC}"
    flyctl open
}

# Main menu
main() {
    echo -e "${BOLD}Choose your deployment platform:${NC}\n"
    echo -e "  ${CYAN}1)${NC} GitHub Pages ${YELLOW}(Frontend only, free, users need API key)${NC}"
    echo -e "  ${CYAN}2)${NC} Railway ${YELLOW}(Full stack, $5/month after free trial)${NC}"
    echo -e "  ${CYAN}3)${NC} Render ${YELLOW}(Full stack, free tier with sleep)${NC}"
    echo -e "  ${CYAN}4)${NC} Fly.io ${YELLOW}(Full stack, generous free tier)${NC}"
    echo -e "  ${CYAN}5)${NC} Manual Instructions"
    echo -e "  ${CYAN}6)${NC} Exit\n"
    
    read -p "Enter your choice (1-6): " choice
    
    case $choice in
        1)
            deploy_github_pages
            ;;
        2)
            deploy_railway
            ;;
        3)
            deploy_render
            ;;
        4)
            deploy_fly
            ;;
        5)
            show_manual_instructions
            ;;
        6)
            echo -e "${GREEN}Goodbye!${NC}"
            exit 0
            ;;
        *)
            echo -e "${RED}Invalid choice${NC}"
            exit 1
            ;;
    esac
}

# Manual instructions
show_manual_instructions() {
    echo -e "\n${BOLD}Manual Deployment Instructions:${NC}\n"
    
    echo -e "${CYAN}GitHub Pages (Frontend Only):${NC}"
    echo -e "1. Push to GitHub: git push origin main"
    echo -e "2. Enable GitHub Pages in repository settings"
    echo -e "3. Your site will be at: https://username.github.io/repo-name/\n"
    
    echo -e "${CYAN}Docker (Any Platform):${NC}"
    echo -e "1. Build: docker build -t socratic-parent ."
    echo -e "2. Run: docker run -e GEMINI_API_KEY=your_key -p 8000:8000 socratic-parent"
    echo -e "3. Access at: http://localhost:8000\n"
    
    echo -e "${CYAN}Any Cloud Platform with Docker:${NC}"
    echo -e "1. Push your code to GitHub"
    echo -e "2. Connect your cloud platform to GitHub"
    echo -e "3. Set GEMINI_API_KEY environment variable"
    echo -e "4. Deploy using Dockerfile\n"
    
    echo -e "${CYAN}Configuration Files Included:${NC}"
    echo -e "  • render.yaml - For Render.com"
    echo -e "  • railway.json - For Railway.app"
    echo -e "  • fly.toml - For Fly.io"
    echo -e "  • .github/workflows/pages.yml - For GitHub Pages\n"
}

# Run main
main
