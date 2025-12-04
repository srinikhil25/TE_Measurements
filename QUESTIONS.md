# Clarification Questions

## Before Implementation

Please provide answers to these questions to ensure we build the system correctly:

### 1. Workbook/Sample Structure
- **Q**: What metadata should we store for each workbook/sample?
  - Sample name (required)
  - Description (optional)
  - Material type?
  - Sample ID/code?
  - Date received?
  - Other properties? --> i think these are good for now

### 2. Admin Access
- **Q**: Should admins be able to:
  - View all researchers' workbooks and data? (for oversight) -> yes, because generally the admin is the professor 
  - Or only manage users without seeing their data? (privacy-focused) => No, because generally the admin is the professor 

### 3. Workbook Sharing
- **Q**: Can researchers share workbooks with other researchers? = they can export and share by themselves... not from our system
  - Or is each workbook strictly private to its creator? => strictly private to its creator

### 4. Measurement Data Storage
- **Q**: How should we store measurement data?
  - In database (for small datasets) - we will use hybrid approach
  - In files (CSV/JSON) with database references (for large datasets) = we will use hybrid approach
  - Hybrid approach? - we will use hybrid approach 

### 5. Data Export
- **Q**: When exporting data, should it be:
  - Per measurement session? -> both options should available 
  - Per workbook (all measurements)? -> both options should available 
  - Both options available? -> both options should available 

### 6. Authentication Details
- **Q**: For the initial admin user:
  - Should we create a default admin account? -> yes default admin account for now, and we delete it in production
  - Or require manual database setup?
  - What should be the default admin credentials? -> admin, admin

### 7. Session Management
- **Q**: Can a researcher have multiple measurement sessions running simultaneously? -> only one for V1.0
  - Or one active session at a time? -> yes active session at a time

### 8. Post-Login Flow
- **Q**: After login, should researchers see:
  - Dashboard with list of their workbooks? -> yes
  - Option to create new workbook immediately? -> if there are no exisiting workbooks then we need to show option to creaet a new workbook immediately
  - Recent measurements summary? -> only if there is any available

  PS: once user creating a new work book, the next screen should have 3 options -> seebeck measurement, electrical conductivity measurement, resistance conductivity measuremtn. and each have thier own templates.. we will discuss them detailly later.

---

**Note**: We'll proceed with authentication system implementation, and you can provide these details as we build. The architecture is flexible enough to accommodate changes.

