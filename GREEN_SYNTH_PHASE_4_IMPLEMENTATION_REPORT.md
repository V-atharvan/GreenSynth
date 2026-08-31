# GreenSynth Analytics Platform — Phase 4 Implementation Report
## Research Group Registration, Member Invitation & Member Onboarding Lifecycle

**Document Status:** Complete & Verified  
**Date:** August 30, 2026  
**Phase:** 4 of 10  
**Backend Test Suite Status:** 247 Passed, 1 Skipped, 0 Failed  
**Frontend Test Suite Status:** 13 Passed (100%), TypeScript 0 Errors, Build Successful  

---

## 1. Executive Summary

Phase 4 of the GreenSynth Analytics Platform implementation establishes the complete multi-member research group registration, invitation dispatch, and student onboarding architecture. 

Building directly upon the database foundation created in Phase 2 and the core authentication primitives created in Phase 3, Phase 4 fulfills the project requirement that:
1. **1 Research Group = 1 Synthesis Project (P1 through P8)**
2. **1 Group = 1 Leader + 3 Invited Members (4 total members, configurable via `MAX_GROUP_MEMBERS`)**
3. **No Unauthenticated or Orphaned Group Members**
4. **All Secret Invitation Tokens are Securely Hashed (SHA-256 in DB, raw tokens only in URL links/emails)**
5. **Clean Separation of Concerns with Zero Impact on Scientific, ML, or Optimization Calculations**

---

## 2. Completed Architecture & Workflow Implementation

```
                                      +------------------------------------+
                                      |     Group Leader Registration      |
                                      |   (Name, Dept, Roll, Email, Pass)  |
                                      +-----------------+------------------+
                                                        |
                                                        v
                                      +------------------------------------+
                                      |   Select Synthesis Project (P1-P8) |
                                      |       Enter 3 Member Details       |
                                      +-----------------+------------------+
                                                        |
                                                        v (POST /api/v1/groups/register)
+-------------------------------------------------------------------------------------------------------------+
|                                    ATOMIC DATABASE TRANSACTION                                              |
|                                                                                                             |
|  1. Insert User (Leader, is_active=True, role='RESEARCHER')                                                |
|  2. Insert ResearchGroup (name, project_id=SelectedProject.id, leader_user_id=Leader.id)                    |
|  3. Insert GroupMembership (group_id=Group.id, user_id=Leader.id, is_leader=True, status='ACTIVE')           |
|  4. Generate 3 URL-safe random tokens; Insert 3 Invitation records with token_hash = SHA256(raw_token)       |
|  5. Dispatch Onboarding Emails via EmailService (Console logging in Dev, SMTP in Prod)                      |
|  6. COMMIT TRANSACTION                                                                                      |
+-------------------------------------------------------------------------------------------------------------+
                                                        |
                                                        v
                                      +------------------------------------+
                                      | Return JWT + Invitation Summaries  |
                                      +------------------------------------+
                                                        |
                                                        v
+-------------------------------------------------------------------------------------------------------------+
|                                      MEMBER ONBOARDING LIFECYCLE                                            |
|                                                                                                             |
|  Student clicks Email Link: /accept-invitation?token=<raw_token>                                            |
|    1. GET /api/v1/auth/invitations/validate?token=<raw_token>                                               |
|       - Hashes token -> matches record in DB                                                                |
|       - Validates status == 'PENDING', expiration > now(), and group capacity < MAX_GROUP_MEMBERS           |
|       - Returns safe group name, project code/name, leader name, and invited student details                |
|    2. Student inputs Password & Confirm Password                                                            |
|    3. POST /api/v1/auth/invitations/accept                                                                  |
|       - Hashes password via NIST-compliant PBKDF2-SHA256                                                    |
|       - Inserts/activates User record with invited student details                                          |
|       - Inserts GroupMembership (group_id=Group.id, user_id=User.id, is_leader=False, status='ACTIVE')       |
|       - Updates Invitation (status='ACCEPTED', accepted_at=NOW())                                           |
|       - Issues and returns authenticated JWT access token                                                   |
+-------------------------------------------------------------------------------------------------------------+
```

---

## 3. Key Backend Components & API Endpoints

### 3.1 Configuration & Security Extensions
- **[config.py](file:///c:/Users/Atharva/OneDrive/Documents/Atharva/CRTD/backend/app/core/config.py)**:
  - `max_group_members: int = 4` (Configurable capacity)
  - `invitation_expiry_hours: int = 72` (72-hour token validity window)
  - `frontend_base_url: str = "http://localhost:5173"` (Invitation link builder)
  - `email_mode: str = "console"` (Safe development console mode / production SMTP)
  - `smtp_host`, `smtp_port`, `smtp_username`, `smtp_password`, `email_from`
- **[security.py](file:///c:/Users/Atharva/OneDrive/Documents/Atharva/CRTD/backend/app/core/security.py)**:
  - `generate_secure_invitation_token() -> str` (`secrets.token_urlsafe(32)`)
  - `hash_invitation_token(raw_token: str) -> str` (`hashlib.sha256(raw_token).hexdigest()`)

### 3.2 Service Layer Implementations
- **[EmailService](file:///c:/Users/Atharva/OneDrive/Documents/Atharva/CRTD/backend/app/services/email_service.py)**:
  - Pluggable transactional email dispatcher.
  - Formats HTML & plaintext invitation emails with secure token URLs, project metadata, and expiration notices.
  - Safe error handling ensuring SMTP network errors never abort or roll back database transactions.
- **[GroupService](file:///c:/Users/Atharva/OneDrive/Documents/Atharva/CRTD/backend/app/services/group_service.py)**:
  - `register_group_with_members(payload)`: Single atomic transaction registering leader, group, leader membership, and 3 member invitations.
  - `get_my_group(current_user)`: Resolves active research group metadata, leader details, active member counts, and project details.
  - `get_my_group_members(current_user)`: Lists all active students in the research group.
  - `get_my_group_invitations(current_user)`: Lists all pending/accepted/expired invitations for the group.
  - `invite_member_to_my_group(current_user, payload)`: Allows leader to invite additional member if `< MAX_GROUP_MEMBERS`.
- **[InvitationService](file:///c:/Users/Atharva/OneDrive/Documents/Atharva/CRTD/backend/app/services/invitation_service.py)**:
  - `validate_invitation(raw_token)`: Sanitized token verification pre-check.
  - `accept_invitation(payload)`: Onboarding acceptance, password setting, account activation, group membership assignment, and token issuance.
  - `resend_invitation(invitation_id, current_user)`: Leader-restricted invitation re-issuance with new cryptographic token.

### 3.3 Registered API Routes
| Method | Route Path | Access Control | Description |
|---|---|---|---|
| `POST` | `/api/v1/groups/register` | Public | Atomic Leader + Group + Member Invitations registration |
| `GET` | `/api/v1/groups/me` | Authenticated | Retrieve user's active research group & project |
| `GET` | `/api/v1/groups/me/members` | Authenticated | List all active group members |
| `GET` | `/api/v1/groups/me/invitations` | Authenticated | List group invitation records and statuses |
| `POST` | `/api/v1/groups/me/invitations` | Group Leader | Invite additional member (capacity bounded) |
| `GET` | `/api/v1/auth/invitations/validate` | Public | Validate raw invitation token from URL |
| `POST` | `/api/v1/auth/invitations/accept` | Public | Accept invitation, set password, onboard student |
| `POST` | `/api/v1/auth/invitations/{id}/resend` | Group Leader | Re-issue invitation token & dispatch email |

---

## 4. Frontend Pages & Components

### 4.1 Group Registration Wizard (`Register.tsx`)
- **Step 1 (Leader Account):** Full Name, Department, Roll Number, Phone Number, Email, Password, Confirm Password.
- **Step 2 (Group & Project Selection):** Research Group Name input and interactive P1–P8 synthesis project card selector displaying synthesis method, precursor material, and solvent.
- **Step 3 (Member Details):** 3 structured member cards capturing Full Name, Department, Roll Number, Phone Number, and Email.
- **Step 4 (Review & Submit):** Complete summary view of leader, project, and members with data isolation warning banner and submission button.
- **Step 5 (Success View):** Displays group confirmation, project assignment, and invitation status cards with a direct dashboard transition button.

### 4.2 Member Onboarding (`AcceptInvitation.tsx`)
- Reads raw `token` from URL search parameters (`?token=...`).
- Pre-validates token against `/api/v1/auth/invitations/validate`.
- Displays contextual banner showing Group Name, Project Code, Project Name, Leader Name, and Student Profile.
- Secure Password and Confirm Password inputs.
- Activates account, joins research group, saves JWT to `localStorage`, and transitions to dashboard.

### 4.3 API Client & Interceptors (`api.ts`, `groupService.ts`, `invitationService.ts`)
- Configured Axios request interceptor automatically attaching Bearer JWT tokens from `localStorage`.
- Typed API service modules exposing clean async promises.

---

## 5. Security & Verification Summary

### 5.1 Security Controls
- **Cryptographic Randomness:** Raw invitation tokens generated via Python `secrets.token_urlsafe(32)`.
- **One-Way Token Hashing:** Only SHA-256 hashes stored in the database. Raw tokens are never logged or stored.
- **Zero Information Leakage:** Password hashes and raw tokens excluded from all API response schemas.
- **Strict Capacity Enforcement:** Atomic checks prevent groups from exceeding 4 active members.
- **Strict Leader Access Control:** Non-leaders cannot invite new members or re-issue existing invitations.
- **Zero Emojis:** Verified zero emojis across all Phase 4 frontend and backend files.

### 5.2 Test Verification Results

#### Backend Test Suite
```
tests/unit/test_group_service.py ......................... PASSED
tests/unit/test_invitation_service.py .................... PASSED
tests/integration/test_group_endpoints.py ................ PASSED
Full Regression Suite: 247 Passed, 1 Skipped, 0 Failed in 20.46s
```

#### Frontend Test Suite & Build
```
src/__tests__/Register.test.tsx .......................... PASSED
src/__tests__/AcceptInvitation.test.tsx ................... PASSED
src/__tests__/App.test.tsx ............................... PASSED
Total: 13/13 Vitest Tests Passed (100%)
TypeScript Compiler: npx tsc --noEmit (0 errors)
Production Vite Build: 1936 modules transformed in 6.59s (dist/ generated cleanly)
```

---

## 6. Scope Compliance & Phase 5 Readiness

Phase 4 strictly complied with all phase boundaries:
- Zero modifications to scientific calculations, ML models, or optimization routines.
- Zero modifications to the database schema established in Phase 2.
- Fully operational Group Leader registration and Member onboarding workflows.
- System is 100% prepared for **Phase 5: Backend Project-Level Authorization & Route Isolation**.
