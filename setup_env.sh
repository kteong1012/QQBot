#!/bin/bash
echo "=== QQBot Environment Setup ==="
echo "This script will help you set up your .env file."
echo ""

if [ -f .env ]; then
    echo "Found existing .env file. We will update it."
else
    echo "Creating a new .env file."
fi

read -p "Enter your DeepSeek API Key: " deepseek_key
read -p "Enter your Zhipu GLM API Key: " glm_key

echo "DEEPSEEK_API_KEY=$deepseek_key" > .env
echo "GLM_API_KEY=$glm_key" >> .env

echo ""
echo "Done! .env file has been saved."
