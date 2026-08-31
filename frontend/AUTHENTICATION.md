# GreenSynth Analytics — Frontend Authentication Architecture (Phase 6)

## 1. Overview
The GreenSynth frontend uses JWT-based authentication coupled with server-side multi-tenant authorization and project isolation.

```
                      ┌──────────────────────┐
                      │    Login / Register  │
                      └──────────┬───────────┘
                                 │
                                 ▼
                     ┌────────────────────────┐
                     │    POST /auth/login    │
                     └───────────┬────────────┘
                                 │
                                 ▼
                      ┌──────────────────────┐
                      │    JWT Access Token  │
                      └──────────┬───────────┘
                                 │
                                 ▼
                       ┌────────────────────┐
                       │    AuthContext     │
                       └─────────┬──────────┘
                                 │
                                 ▼
                        ┌──────────────────┐
                        │ Axios Interceptor│
                        └────────┬─────────┘
                                 │
                                 ▼
                 ┌─────────────────────────────────┐
                 │ Authorization: Bearer <token>   │
                 └───────────────┬─────────────────┘
                                 │
                                 ▼
                  ┌──────────────────────────────┐
                  │ Server-Side Authorization    │
                  │ (Project & Group Scoped Data)│
                  └──────────────────────────────┘
```

## 2. Authentication Flow

### A. Group Leader Registration (`/register`)
1. Student registers personal leader details, establishes research group name, and selects an assigned project (P1–P8).
2. Leader inputs details (name, email, department, roll number, phone) for 3 remaining group members.
3. Backend atomically creates Leader account, Research Group, active Leader Membership, and dispatches 3 onboarding invitations.
4. Returns JWT token, automatically establishing authenticated session.

### B. Member Invitation Acceptance (`/accept-invitation?token=...`)
1. Student receives invitation link with secure token.
2. Frontend pre-validates token against `GET /auth/invitations/validate`.
3. Displays assigned group & project context.
4. Student creates their account password and submits to `POST /auth/invitations/accept`.
5. Backend activates member account, joins group, and returns JWT token.

### C. Standard Login (`/login`)
1. Student / Leader enters institutional email and password.
2. Backend verifies hash, asserts account active status, and returns signed JWT access token.
3. `AuthContext` stores token in `localStorage` (`greensynth_token`), calls `GET /auth/me`, and populates `user` state.

### D. Logout
1. User clicks "Sign Out" in the sidebar footer.
2. `AuthContext.logout()` clears `greensynth_token` from `localStorage` and resets in-memory user state.
3. Redirects user to `/login`.

## 3. Core Modules

| Module | Location | Purpose |
| :--- | :--- | :--- |
| **`auth.ts`** | `src/types/auth.ts` | Strongly typed interfaces matching FastAPI auth models (`UserProfile`, `TokenResponse`, `LoginRequest`). |
| **`api.ts`** | `src/services/api.ts` | Axios instance with Bearer token injection and 401/403 response normalization. |
| **`authService.ts`** | `src/services/authService.ts` | Centralized auth API calls (`login`, `registerLeader`, `acceptInvitation`, `getCurrentUser`). |
| **`AuthContext.tsx`** | `src/context/AuthContext.tsx` | Central state management, session restoration, and user context. |
| **`ProtectedRoute.tsx`**| `src/components/ProtectedRoute.tsx` | Route guard that redirects unauthenticated users and prevents flash of protected content. |
| **`Login.tsx`** | `src/pages/Login.tsx` | Accessible, scientific sign-in UI with validation and error alerts. |
| **`Register.tsx`** | `src/pages/Register.tsx` | 4-step wizard for group leader registration and member onboarding. |
| **`AcceptInvitation.tsx`**| `src/pages/AcceptInvitation.tsx`| Invitation validation and member password creation. |

## 4. Error Handling: 401 vs 403

- **`401 Unauthorized`**: Indicates expired or invalid authentication token. Handled by removing `greensynth_token`, resetting `AuthContext`, and redirecting to `/login`.
- **`403 Forbidden`**: Indicates authenticated session with insufficient permissions or cross-project access attempt. Handled gracefully without terminating user session.
