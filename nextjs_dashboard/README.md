# Personal AI Employee - Next.js Dashboard

Production-grade web dashboard for the Platinum Tier Personal AI Employee with NextAuth.js v5 authentication, role-based access control, and real-time approval workflow.

## Features

✨ **NextAuth.js v5 Authentication**
- Credentials provider with bcrypt password hashing
- JWT-based sessions (7-day expiry)
- Protected routes with middleware

🔐 **Role-Based Access Control**
- **Admin**: Full access (approve/reject, user management, settings)
- **Viewer**: Read-only access (view pending approvals, health status)

📋 **Approval Workflow**
- One-click approve/reject for pending items
- Support for multiple categories: Email, LinkedIn, WhatsApp, Odoo, Facebook, Instagram, Twitter
- File-based coordination with vault (atomic move operations)
- Real-time updates (5-second polling)

📊 **Dashboard Pages**
- `/dashboard` - Pending approvals with stats
- `/dashboard/status` - MCP server health monitoring
- `/dashboard/activity` - Recent action log
- `/dashboard/settings` - Admin-only user management

📱 **Mobile-Responsive**
- Tailwind CSS for responsive design
- ≥44px touch targets for mobile
- Dark mode support
- No horizontal scroll on small screens

## Tech Stack

- **Framework**: Next.js 16.1.6 (App Router)
- **Auth**: NextAuth.js v5.0.0-beta.30
- **Styling**: Tailwind CSS 4
- **UI Components**: Custom components (ApprovalCard, MCPStatusBadge, etc.)
- **Charts**: Recharts 2.12
- **Password**: bcrypt 5.1.1
- **Frontmatter**: gray-matter 4.0.3

## Quick Start

### Prerequisites

- Node.js 20+
- Vault directory at `../vault/`
- Users file at `../vault/Users/users.json`

### Installation

```bash
# Install dependencies
npm install

# Copy environment variables
cp .env.local.example .env.local

# Generate NextAuth secret
openssl rand -base64 32
# Add to .env.local: NEXTAUTH_SECRET=<generated-secret>

# Start development server
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

### Default Credentials

**Admin User:**
- Email: `muhammadqasim0326@gmail.com`
- Password: `123456`

## Project Structure

```
nextjs_dashboard/
├── app/
│   ├── api/
│   │   ├── auth/[...nextauth]/route.ts  # NextAuth handler
│   │   ├── approve/route.ts             # POST: Move to /Approved/
│   │   ├── reject/route.ts              # POST: Move to /Rejected/
│   │   ├── status/route.ts              # GET: Vault state
│   │   ├── health/route.ts              # GET: MCP server health
│   │   └── users/
│   │       ├── create/route.ts          # POST: Add user
│   │       └── update/route.ts          # POST: Update password/role
│   ├── dashboard/
│   │   ├── page.tsx                     # Main dashboard
│   │   ├── status/page.tsx              # MCP health
│   │   ├── activity/page.tsx            # Activity log
│   │   └── settings/page.tsx            # User management
│   ├── login/page.tsx                   # Login page
│   ├── layout.tsx                       # Root layout + SessionProvider
│   └── page.tsx                         # Home (redirects to /dashboard or /login)
├── components/
│   ├── ApprovalCard.tsx                 # Approval item with approve/reject
│   ├── UserRoleBadge.tsx                # Admin/Viewer badge
│   ├── MCPStatusBadge.tsx               # MCP server status
│   ├── StatsCards.tsx                   # Dashboard stats
│   └── ActivityTimeline.tsx             # Recent activity
├── lib/
│   └── vault.ts                         # Vault file operations
├── auth.ts                              # NextAuth config
├── middleware.ts                        # Protected routes + role checks
└── tailwind.config.js                   # Tailwind with dark mode
```

## API Routes

### Authentication
- `GET/POST /api/auth/[...nextauth]` - NextAuth.js handler

### Dashboard
- `GET /api/status` - Get pending approvals and vault counts
- `POST /api/approve` - Approve item (admin only)
- `POST /api/reject` - Reject item (admin only)
- `GET /api/health` - MCP server health status

### User Management (Admin Only)
- `POST /api/users/create` - Add new user
- `POST /api/users/update` - Change password or role

## User Roles

| Feature | Admin | Viewer |
|---------|-------|--------|
| View pending approvals | ✓ | ✓ |
| View MCP health | ✓ | ✓ |
| View activity log | ✓ | ✓ |
| Approve items | ✓ | ✗ |
| Reject items | ✓ | ✗ |
| User management | ✓ | ✗ |
| Access /dashboard/settings | ✓ | ✗ |

## Testing

See [docs/platinum/phase2-testing.md](../docs/platinum/phase2-testing.md) for comprehensive test cases.

## Production Deployment

```bash
# Build for production
npm run build

# Start production server
npm start
```

## License

MIT

---

**Built with ❤️ for the Personal AI Employee Hackathon 2026**
