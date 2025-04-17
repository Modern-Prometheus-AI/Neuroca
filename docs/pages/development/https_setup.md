# Setting Up HTTPS for docs.neuroca.dev

This document outlines the steps to set up HTTPS for the docs.neuroca.dev custom domain with GitHub Pages.

## Steps Completed

1. **CNAME File Added**:
   - Created a CNAME file at `docs/pages/CNAME` containing "docs.neuroca.dev"
   - This file will be copied to the root of the deployed site when the GitHub Pages site is built
   - This tells GitHub Pages that the site should respond to the custom domain

## Steps To Complete

1. **DNS Configuration**:
   - Log in to your domain registrar or DNS provider
   - Add a CNAME record for "docs" subdomain:
     ```
     Type: CNAME
     Host: docs
     Value: Modern-Prometheus-AI.github.io  (replace with actual GitHub organization/username)
     TTL: 3600 (or as recommended by your provider)
     ```

2. **GitHub Repository Settings**:
   - Go to the GitHub repository → Settings → Pages
   - Under "Custom domain," enter "docs.neuroca.dev"
   - Check the "Enforce HTTPS" checkbox
   - Save the changes

3. **Wait for DNS Propagation and Certificate Issuance**:
   - DNS changes may take up to 24-48 hours to propagate worldwide
   - GitHub's certificate issuance typically takes about 1 hour
   - You can check the status in the repository's Pages settings

## Verification

After completing the steps and waiting for propagation and certificate issuance:

1. Visit https://docs.neuroca.dev and ensure it loads properly with a secure connection
2. Check for the lock icon in your browser's address bar
3. Verify that the certificate is valid and issued by GitHub's certificate authority (Let's Encrypt)

## Troubleshooting

If HTTPS is not working after several hours:

1. **Check DNS Propagation**:
   - Use a tool like [dnschecker.org](https://dnschecker.org/) to verify the CNAME record is properly set
   - Ensure the CNAME points to the correct GitHub Pages domain

2. **Verify GitHub Pages Settings**:
   - Check that the custom domain is correctly entered in GitHub Pages settings
   - Ensure "Enforce HTTPS" is checked

3. **Inspect Repository**:
   - Verify the CNAME file exists at the root of the gh-pages branch
   - Check that its content is exactly "docs.neuroca.dev" (no extra spaces or characters)

4. **GitHub Status**:
   - Check [GitHub Status](https://www.githubstatus.com/) for any ongoing issues with GitHub Pages or certificate issuance

## Notes

- Once HTTPS is enabled, HTTP requests will automatically redirect to HTTPS
- If you change your custom domain in the future, a new certificate will need to be issued
- GitHub Pages uses Let's Encrypt for certificate issuance, which has automatic renewal
