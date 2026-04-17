@echo off
echo === QQBot Environment Setup ===
echo This script will help you set up your .env file.
echo.

if exist .env (
    echo Found existing .env file. We will update it.
) else (
    echo Creating a new .env file.
)

set /p deepseek_key="Enter your DeepSeek API Key: "
set /p glm_key="Enter your Zhipu GLM API Key: "

echo DEEPSEEK_API_KEY=%deepseek_key% > .env
echo GLM_API_KEY=%glm_key% >> .env

echo.
echo Done! .env file has been saved.
pause
