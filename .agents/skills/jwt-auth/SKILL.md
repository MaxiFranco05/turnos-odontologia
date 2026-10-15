---
name: jwt-auth
description: "Implement JWT (JSON Web Token) authentication for secure API access."
---

# JWT Authentication

## Overview
JWT provides stateless authentication by embedding user claims in a signed token. This skill should be invoked when implementing API authentication, single sign-on, or stateless session management.

## Core Principles
- **Stateless**: No server-side session storage needed
- **Signed**: Use HMAC or RSA for token signing
- **Claims-Based**: Embed user info in token payload
- **Expiration**: Set appropriate token lifetimes

## Preparation Checklist
- [ ] Choose signing algorithm (HS256, RS256)
- [ ] Generate secret key or key pair
- [ ] Define token claims structure
- [ ] Plan token storage strategy

## Step-by-Step Process
1. **Generate**: Create JWT with user claims
2. **Sign**: Sign with secret or private key
3. **Issue**: Send token to client (cookie or header)
4. **Validate**: Implement middleware to verify tokens
5. **Refresh**: Handle token refresh logic
6. **Revocate**: Plan for token revocation

## Do's and Don'ts
- ✅ **Do** use httpOnly cookies for browser storage
- ✅ **Do** implement token refresh mechanism
- ✅ **Do** validate token expiration
- ❌ **Don't** store sensitive data in JWT payload
- ❌ **Don't** use weak secret keys
- ❌ **Don't** skip signature verification

## Anti-Patterns
- **Sensitive Data**: Storing passwords in JWT
- **No Expiration**: Tokens that never expire
- **Weak Keys**: Using simple secret keys
- **No Validation**: Skipping signature checks
