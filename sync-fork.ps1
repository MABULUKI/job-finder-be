# Change directory to your local repo
Set-Location -Path "D:\DEPLOYMENT\GROUP 13 SE\job-recommender-backend"

# Fetch updates from the upstream remote
git fetch upstream

# Checkout the main branch
git checkout main

# Merge upstream main branch into your local main
git merge upstream/main

# Push the updated main branch to your origin remote (your fork)
git push origin main

Set-ExecutionPolicy Bypass -Scope Process
.\sync-fork.ps1

