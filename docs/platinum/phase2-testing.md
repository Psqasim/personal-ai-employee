# Phase 2 Testing Guide: Next.js Dashboard with NextAuth.js

**Feature**: 003-platinum-tier | **Phase**: Phase 2 - Next.js Dashboard
**Date**: 2026-02-15 | **Status**: Implementation Complete

## Overview

This document provides comprehensive testing procedures for the Next.js Dashboard with NextAuth.js v5 authentication, role-based access control, and approval workflow.

## Prerequisites

- Next.js 16+ installed
- Node.js 20+
- Vault directory accessible at `../vault/`
- Users file created at `../vault/Users/users.json`

## Initial Setup

### 1. Install Dependencies

```bash
cd nextjs_dashboard
npm install
```

### 2. Configure Environment

```bash
cp .env.local.example .env.local
# Edit .env.local and set NEXTAUTH_SECRET (use: openssl rand -base64 32)
```

### 3. Verify Vault Structure

```bash
ls -la ../vault/Users/users.json  # Should exist with admin user
ls -la ../vault/Pending_Approval/  # Should have category subdirectories
ls -la ../vault/Approved/  # Should exist
ls -la ../vault/Rejected/  # Should exist
```

## Test Cases

### TC1: Authentication Testing

#### TC1.1: Admin Login
**Objective**: Verify admin user can log in successfully

**Steps**:
1. Start development server: `npm run dev`
2. Navigate to `http://localhost:3000`
3. Should redirect to `/login`
4. Enter credentials:
   - Email: `muhammadqasim0326@gmail.com`
   - Password: `123456`
5. Click "Sign in"

**Expected Result**:
- ✓ Redirects to `/dashboard`
- ✓ Shows "Personal AI Employee Dashboard" header
- ✓ Shows user name "Muhammad Qasim"
- ✓ Shows "Admin" role badge (👑 Admin)
- ✓ "Settings" link visible in navigation

#### TC1.2: Invalid Credentials
**Objective**: Verify proper error handling for invalid login

**Steps**:
1. Navigate to `/login`
2. Enter invalid credentials
3. Click "Sign in"

**Expected Result**:
- ✓ Stays on `/login` page
- ✓ Shows error message: "Invalid email or password"
- ✓ Form fields cleared of password

#### TC1.3: Protected Route Access
**Objective**: Verify unauthenticated users cannot access dashboard

**Steps**:
1. Open incognito/private browser window
2. Navigate directly to `http://localhost:3000/dashboard`

**Expected Result**:
- ✓ Redirects to `/login?callbackUrl=/dashboard`
- ✓ After login, redirects back to `/dashboard`

### TC2: Role-Based Access Control

#### TC2.1: Viewer User Creation
**Objective**: Create a viewer user for testing read-only access

**Steps**:
1. Log in as admin
2. Navigate to `/dashboard/settings`
3. Click "Manage Users" tab
4. Fill in form:
   - Email: `viewer@test.com`
   - Name: `Test Viewer`
   - Password: `viewer123`
   - Role: `Viewer (Read-only)`
5. Click "Add User"

**Expected Result**:
- ✓ Success message: "User viewer@test.com created successfully"
- ✓ Form fields cleared
- ✓ User added to `../vault/Users/users.json`

#### TC2.2: Viewer Login and Limitations
**Objective**: Verify viewer role has read-only access

**Steps**:
1. Sign out
2. Log in as viewer (`viewer@test.com` / `viewer123`)
3. Navigate to `/dashboard`

**Expected Result**:
- ✓ Shows "Viewer" role badge (👁️ Viewer)
- ✓ "Settings" link NOT visible in navigation
- ✓ Approval cards show "Read-only access - contact admin to approve" message
- ✓ Approve/Reject buttons NOT visible

#### TC2.3: Viewer Settings Access Restriction
**Objective**: Verify viewer cannot access admin-only pages

**Steps**:
1. As viewer, try to navigate to `/dashboard/settings`

**Expected Result**:
- ✓ Redirects to `/dashboard`
- ✓ Cannot access settings page

### TC3: Approval Workflow

#### TC3.1: Create Test Approval (Email)
**Objective**: Verify dashboard displays pending email approvals

**Setup**:
```bash
# Create test email approval
mkdir -p ../vault/Pending_Approval/Email
cat > ../vault/Pending_Approval/Email/TEST_EMAIL_001.md << 'EOF'
---
title: "Test Email Draft"
subject: "Re: Meeting Request"
from: "assistant@ai.com"
to: "john@example.com"
timestamp: "2026-02-15T10:00:00Z"
---

Hi John,

Thanks for reaching out! I'd be happy to meet next week.

How about Tuesday at 2 PM?

Best regards,
AI Assistant
EOF
```

**Steps**:
1. Refresh dashboard at `/dashboard`
2. Verify approval appears

**Expected Result**:
- ✓ Pending count increases by 1
- ✓ Approval card displays with:
  - Blue "Email" badge
  - Title: "Test Email Draft"
  - Preview of email body
  - Timestamp shown
  - "Approve" and "Reject" buttons (admin only)

#### TC3.2: Approve Item
**Objective**: Verify approval workflow moves file correctly

**Steps**:
1. As admin, click "✓ Approve" on test email
2. Wait for processing

**Expected Result**:
- ✓ Button shows "Processing..." during action
- ✓ Approval card removed from list
- ✓ Pending count decreases by 1
- ✓ File moved from `Pending_Approval/Email/` to `Approved/Email/`
- ✓ File structure preserved

**Verify**:
```bash
ls -la ../vault/Approved/Email/TEST_EMAIL_001.md  # Should exist
```

#### TC3.3: Reject Item
**Objective**: Verify rejection workflow with reason

**Setup**:
```bash
# Create another test approval
cat > ../vault/Pending_Approval/Email/TEST_EMAIL_002.md << 'EOF'
---
title: "Another Test Email"
subject: "Re: Follow-up"
timestamp: "2026-02-15T11:00:00Z"
---

Test email content for rejection testing.
EOF
```

**Steps**:
1. Refresh dashboard
2. Click "✗ Reject" on test email
3. Modal appears
4. Enter rejection reason: "Incorrect tone"
5. Click "Confirm Reject"

**Expected Result**:
- ✓ Modal displays with textarea for reason
- ✓ Button shows "Processing..." during action
- ✓ Approval card removed from list
- ✓ File moved to `Rejected/Email/`
- ✓ File frontmatter updated with:
  - `rejection_reason: "Incorrect tone"`
  - `rejected_at: "<timestamp>"`

**Verify**:
```bash
cat ../vault/Rejected/Email/TEST_EMAIL_002.md | head -15  # Check frontmatter
```

### TC4: Multiple Approval Categories

#### TC4.1: LinkedIn Approval
**Objective**: Verify dashboard handles multiple approval types

**Setup**:
```bash
mkdir -p ../vault/Pending_Approval/LinkedIn
cat > ../vault/Pending_Approval/LinkedIn/LINKEDIN_POST_001.md << 'EOF'
---
title: "Product Launch Announcement"
timestamp: "2026-02-15T12:00:00Z"
---

🚀 Excited to announce our new Personal AI Employee platform!

After months of development, we're launching Platinum Tier with:
- 24/7 cloud agent monitoring
- Dual-agent Git sync
- One-click approval dashboard

#AI #Automation #Productivity
EOF
```

**Steps**:
1. Refresh dashboard
2. Verify LinkedIn approval displays

**Expected Result**:
- ✓ Approval card shows:
  - Indigo "LinkedIn" badge
  - Title: "Product Launch Announcement"
  - Post preview
  - Proper formatting maintained

### TC5: MCP Health Monitoring

#### TC5.1: Health Status Display
**Objective**: Verify MCP server health monitoring

**Steps**:
1. Navigate to `/dashboard/status`
2. Observe MCP server grid

**Expected Result**:
- ✓ Grid shows all 7 MCP servers:
  - Email, WhatsApp, LinkedIn, Facebook, Instagram, Twitter, Odoo
- ✓ Each shows status badge (online/offline/unknown)
- ✓ "Last call" time displayed
- ✓ Summary shows: "X online, Y offline"

### TC6: Activity Log

#### TC6.1: Recent Activity Display
**Objective**: Verify activity timeline

**Steps**:
1. Navigate to `/dashboard/activity`
2. View recent activity

**Expected Result**:
- ✓ Activity timeline shows recent actions
- ✓ Agent icons displayed (☁️ Cloud, 💻 Local)
- ✓ Actions color-coded by agent
- ✓ Timestamps shown for each activity

### TC7: Settings Management

#### TC7.1: Password Change
**Objective**: Verify admin can change own password

**Steps**:
1. As admin, navigate to `/dashboard/settings`
2. Click "Change Password" tab
3. Enter:
   - New Password: `newpass123`
   - Confirm Password: `newpass123`
4. Click "Update Password"

**Expected Result**:
- ✓ Success message: "Password updated successfully"
- ✓ Form fields cleared
- ✓ Password hash updated in `users.json`

**Verify**:
1. Sign out
2. Log in with new password: `newpass123`
3. Should succeed

#### TC7.2: Password Mismatch Validation
**Objective**: Verify password confirmation validation

**Steps**:
1. Navigate to settings
2. Enter mismatched passwords:
   - New Password: `test123`
   - Confirm Password: `test456`
3. Click "Update Password"

**Expected Result**:
- ✓ Error message: "Passwords do not match"
- ✓ Form not submitted

### TC8: Mobile Responsiveness

#### TC8.1: Mobile Layout (375px)
**Objective**: Verify mobile-responsive design

**Steps**:
1. Open DevTools (F12)
2. Toggle device toolbar (Ctrl+Shift+M)
3. Set dimensions to 375x667 (iPhone SE)
4. Navigate through dashboard pages

**Expected Result**:
- ✓ Stats cards stack vertically
- ✓ Approval cards stack vertically
- ✓ Navigation menu readable
- ✓ Buttons ≥44px touch target (tap-friendly)
- ✓ No horizontal scroll
- ✓ Text readable without zoom

### TC9: Real-Time Updates

#### TC9.1: Auto-Refresh (5s Polling)
**Objective**: Verify dashboard auto-updates

**Setup**:
```bash
# While dashboard is open, add new approval
cat > ../vault/Pending_Approval/Email/REALTIME_TEST.md << 'EOF'
---
title: "Real-time Update Test"
timestamp: "2026-02-15T13:00:00Z"
---
Testing auto-refresh functionality.
EOF
```

**Steps**:
1. Keep dashboard open at `/dashboard`
2. Wait up to 5 seconds

**Expected Result**:
- ✓ New approval appears automatically
- ✓ Pending count updates
- ✓ No page reload needed
- ✓ Smooth UI update (no flicker)

### TC10: Dark Mode Support

#### TC10.1: Dark Mode Rendering
**Objective**: Verify dark mode styling

**Steps**:
1. Add `dark` class to `<html>` element via DevTools
2. Observe dashboard appearance

**Expected Result**:
- ✓ Background: Dark gray (#1e1e1e)
- ✓ Cards: Darker gray (#2d2d2d)
- ✓ Text: Light colors (#e0e0e0)
- ✓ Buttons maintain contrast
- ✓ Badges readable in dark mode
- ✓ All components support dark mode

## Performance Testing

### PT1: Dashboard Load Time
**Objective**: Verify dashboard loads quickly

**Test**:
1. Open DevTools Network tab
2. Navigate to `/dashboard`
3. Check "DOMContentLoaded" time

**Acceptance Criteria**:
- ✓ Initial page load: <2 seconds
- ✓ Lighthouse Performance score: >90

### PT2: API Response Time
**Objective**: Verify API endpoints respond quickly

**Test**:
1. Monitor `/api/status` in Network tab
2. Observe response time

**Acceptance Criteria**:
- ✓ `/api/status`: <500ms
- ✓ `/api/approve`: <2s (includes file move)
- ✓ `/api/health`: <500ms

## Security Testing

### ST1: Session Expiry
**Objective**: Verify sessions expire correctly

**Test**:
1. Log in
2. Wait 7 days (or modify `maxAge` in `auth.ts` to 60s for testing)
3. Try to access dashboard

**Expected Result**:
- ✓ Redirects to `/login`
- ✓ Session cookie expired

### ST2: CSRF Protection
**Objective**: Verify NextAuth.js CSRF protection

**Test**:
1. Attempt POST to `/api/approve` without valid session

**Expected Result**:
- ✓ Returns 401 Unauthorized

### ST3: Password Storage
**Objective**: Verify passwords are hashed

**Test**:
```bash
cat ../vault/Users/users.json | jq '.users[0].password'
```

**Expected Result**:
- ✓ Password starts with `$2b$` (bcrypt hash)
- ✓ Not plain text

## Integration Testing

### IT1: Full Approval Workflow
**Objective**: End-to-end approval process

**Scenario**:
1. Cloud Agent creates draft → `Pending_Approval/Email/`
2. User opens dashboard → sees draft
3. User approves → file moves to `Approved/Email/`
4. Local Agent monitors `Approved/` → triggers Email MCP send

**Test**:
1. Create draft in `Pending_Approval/Email/`
2. Approve via dashboard
3. Verify file in `Approved/Email/`
4. (Future: Verify Local Agent sends email)

## Cleanup

After testing:

```bash
# Remove test approvals
rm -rf ../vault/Pending_Approval/Email/TEST_*
rm -rf ../vault/Pending_Approval/Email/REALTIME_*
rm -rf ../vault/Pending_Approval/LinkedIn/LINKEDIN_*
rm -rf ../vault/Approved/Email/TEST_*
rm -rf ../vault/Rejected/Email/TEST_*

# Optional: Remove test viewer user
# Edit ../vault/Users/users.json and remove viewer@test.com entry
```

## Known Issues

None currently. Report any issues to the project repository.

## Next Steps

- Implement API usage monitoring (Phase 7)
- Add WhatsApp notifications integration (Phase 8)
- Deploy to production with PM2 (Phase 10)
- Create demo video following test scenarios

---

**Testing Status**: ✓ All test cases defined and ready for execution
**Last Updated**: 2026-02-15
