# Sistema MRX - Gestão de Compra de Placas Eletrônicas

## Overview
The MRX System is a comprehensive solution for managing the procurement of electronic circuit boards. It features lot-based tracking, quality classification (star ratings), supplier management, and an automated workflow from purchase request to inventory receipt. Key capabilities include AI-powered classification, geolocalized data capture, dynamic pricing, and a robust Role-Based Access Control (RBAC) system. The project aims to streamline the procurement process, enhance traceability, and provide detailed analytics for better decision-making in the electronic board market.

## Recent Changes

### November 15, 2025 - Feature: Automatic OS Generation on OC Approval
**Feature:** When approving Purchase Orders (Ordens de Compra), the system now automatically generates a Service Order (Ordem de Serviço - OS) to streamline the workflow.

**Implementation:** Modified `app/routes/ordens_compra.py` to:
1. **Automatic OS Creation:** After approving an OC, the system automatically creates an OS with:
   - Type: 'COLETA' (Collection)
   - Status: 'PENDENTE' (Pending)
   - Unique OS number: `OS-YYYYMMDD-XXXXXX` format
   - Snapshot of supplier data at creation time
   - Comprehensive audit trail

2. **Idempotency:** The system checks if an OS already exists for the OC before creating a new one, preventing duplicates

3. **Error Handling:** Implemented robust try/except within nested transaction with automatic rollback if OS creation fails

4. **Detailed Logging:** Added comprehensive debug logs for troubleshooting and monitoring

**Testing:** End-to-end test confirmed:
- ✅ OC #2 (R$ 60.50) approved successfully
- ✅ OS #1 (OS-20251115-E64F56) created automatically with status PENDENTE
- ✅ OS linked correctly to OC #2
- ✅ Audit trail registered
- ✅ Response includes OS information

**Architect Recommendations for Future Improvements:**
1. Extract duplicated helper functions (`gerar_numero_os`, `criar_snapshot_fornecedor`, `registrar_auditoria_os`) to shared module (`app/services/os_helpers.py`) to prevent code divergence
2. Add unique constraint on `OrdemServico.oc_id` to prevent race conditions in simultaneous approvals
3. Add automated tests for OS creation workflow

**Impact:** The complete workflow is now: Solicitação → OC → OS (all automated). Users only need to approve the Solicitação and then the OC, and the OS is generated automatically.

### November 14, 2025 - Critical Fix: Automatic OC Generation on Approval
**Problem:** When approving purchase requests (Solicitações), the system was only updating the status to "approved" but NOT creating the corresponding Purchase Order (Ordem de Compra), lots, audit records, or notifications.

**Root Cause:** The system had duplicate approval endpoints:
- `solicitacoes.py` (legacy, not in use): contained full OC creation logic
- `solicitacoes_new.py` (active): only changed status without creating OC

Additionally, the approval endpoint was failing with "400 Bad Request" when the frontend sent requests without a JSON body.

**Solution:**
1. **Consolidated approval logic:** Replaced the simplified approval function in `solicitacoes_new.py` with the complete version that:
   - Creates Purchase Order (OC) automatically with status "em_analise"
   - Generates lots grouped by type and star rating
   - Registers comprehensive audit trail
   - Creates notifications for employees and finance team
   - Emits real-time WebSocket events

2. **Fixed 400 Bad Request error:** Changed `request.get_json()` to `request.get_json(silent=True)` to handle empty request bodies gracefully.

3. **Retroactive data correction:** Created missing OC #3 (R$ 1,221.00) for previously approved request #2.

**Testing:** End-to-end approval test confirmed:
- ✅ OC #4 created successfully (R$ 9,768.00) for request #3
- ✅ Lot created and linked (94670294-6F88-43AA-8DAC-78DC9594BFEC)
- ✅ Audit records registered
- ✅ Notifications created (3 total)
- ✅ WebSocket events emitted
- ✅ All data persisted correctly

**Impact:** The complete approval workflow is now fully operational. Approving any purchase request will automatically trigger the entire OC creation pipeline.

### November 13, 2025 - Critical Bug Fix: API URL Duplication
**Problem:** Solicitações de Compra and Ordens de Compra tables were displaying "Erro ao carregar solicitações" and "Erro ao carregar ordens de compra" instead of loading data.

**Root Cause:** The `fetchAPI()` helper function in `app.js` and `layout.js` already prefixes all endpoints with `/api`. However, templates were passing URLs like `/api/solicitacoes` to `fetchAPI()`, resulting in duplicated URLs like `/api/api/solicitacoes` which returned 404 Not Found errors.

**Solution:** Systematically removed the redundant `/api` prefix from all `fetchAPI()` calls across the codebase:
- **solicitacoes.html:** Updated `/api/solicitacoes` → `/solicitacoes` and `/api/ordens-compra` → `/ordens-compra`
- **dashboard.html:** Updated `/api/fornecedores` → `/fornecedores` and `/api/lotes/analisar` → `/lotes/analisar`
- **funcionario.html:** Updated 5 endpoints to remove `/api` prefix
- **app.js:** Updated `/api/fornecedores` → `/fornecedores`

**Testing:** Both APIs confirmed working correctly:
- GET `/api/solicitacoes` returns 200 OK with 5 solicitações
- GET `/api/ordens-compra` returns 200 OK with 2 ordens de compra

**Convention Established:** All `fetchAPI()` calls should pass endpoints WITHOUT the `/api` prefix. The helper automatically adds it. Direct `fetch()` calls that need absolute paths should either bypass `fetchAPI()` or include the full prefix intentionally.

## User Preferences
No specific user preferences were provided in the original document.

## System Architecture

### Stack Tecnológica
- **Backend:** Flask 3.0.0, SQLAlchemy
- **Banco de Dados:** PostgreSQL (Replit Database)
- **Autenticação:** JWT (Flask-JWT-Extended) with numeric ID
- **IA:** Google Gemini for automatic board classification
- **WebSocket:** Socket.IO for real-time notifications
- **Frontend:** HTML/CSS/JavaScript with a modern gradient design

### UI/UX Decisions
- Modernized frontend with gradient design for intuitive user interaction.
- Native camera integration for capturing board photos.
- Visual star selection for quality classification.
- Real-time price calculation on the frontend.
- Intuitive interfaces for supplier price matrix configuration.
- Dashboard with quick access cards and statistics.

### Technical Implementations
- **AI Integration:** Google Gemini provides 1-5 star classification with detailed textual justifications based on image analysis (percentage green). Users can accept or override AI suggestions.
- **Geolocation:** Captures GPS coordinates (latitude/longitude) and allows manual address input for requests.
- **Dynamic Pricing:** Prices are configured per supplier, lot type, and star rating, with each combination having a unique price per kg.
- **Excel Integration:** Comprehensive import/export functionality for lot types and prices, including an auto-generation model for 15 price points (3 classifications × 5 stars).
- **Automated Lot Type Codes:** System automatically generates read-only codes (e.g., TL001) for lot types.
- **Workflow Automation:** Full lifecycle management from request creation, administrative approval, lot creation, and final inventory entry.
- **Robust Validation:** Backend enforces validation rules, such as blocking zero values and mandatory configuration before creating requests.
- **RBAC System:** Implements a comprehensive Role-Based Access Control with 7 standard profiles (Administrator, Buyer, Inspector/Stock, Separation, Driver, Finance, Audit/BI).
- **Advanced JWT Authentication:** Features access tokens (24-hour validity) and refresh tokens (30-day validity) with a refresh endpoint.
- **Auditing System:** Automatically logs all critical actions, including creation, updates, deletions, and login attempts (success/failure), capturing IP, user agent, and detailed JSON data.
- **Purchase Order (Ordem de Compra - OC) Module:** Complete workflow for generating purchase orders from approved requests with strict 1:1 relationship enforcement, RBAC controls, and comprehensive audit trails including GPS/IP/device metadata capture.
- **Data Models:**
    - `TipoLote`: Configurable board types (up to 150), with name, code, description, unit of measure, and active status.
    - `FornecedorTipoLotePreco`: Price matrix (up to 750 points per supplier) defining price per kg for supplier/lot type/star combinations.
    - `Solicitacao`: Purchase requests including employee, supplier, pickup type, status, observations, and timestamps.
    - `ItemSolicitacao`: Individual request items detailing lot type, weight, AI-suggested stars, final stars, calculated value, image URL, and observations.
    - `OrdemCompra`: Purchase orders generated from approved requests with 1:1 relationship to Solicitacao, tracking status (em_analise/aprovada/rejeitada/cancelada), approver, total value, and telemetry metadata (IP, GPS coordinates, device info).
    - `AuditoriaOC`: Comprehensive audit trail for purchase orders, logging all status changes, approvals, rejections, cancellations with full metadata capture (user, timestamps, before/after status, IP, GPS, user agent).
    - `Lote`: Grouping of items by supplier/type/stars with unique tracking number, total weight/value, quantity, average stars, and status.
    - `EntradaEstoque`: Final inventory entries linked to lots, with status, entry/processing dates, and admin details.
    - `Perfil (Role)`: Defines system roles with configurable JSON permissions.
    - `Veiculo`: Vehicle registration (plate, RENAVAM, type, capacity, make, model).
    - `Motorista`: Driver registration (CPF, CNH, phone) linked to vehicles.
    - `AuditoriaLog`: Comprehensive log of critical actions with user, action, entity, IP, user agent, and timestamp.

### Feature Specifications
- **Multi-item Requests:** Support for creating requests with multiple items, each with individual classification and details.
- **Configurable Star Ratings:** Administrative interface for configuring star ratings (1-5) per supplier and lot type, including light/medium/heavy classifications.
- **Supplier Management:** Cadastro and editing of suppliers, with automatic data retrieval (e.g., from Receita Federal via CNPJ/CPF).
- **Vehicle and Driver Management:** Dedicated modules for managing vehicles and drivers.

## External Dependencies
- **Google Gemini API:** Utilized for AI-powered image analysis and classification of electronic boards.
- **Replit Database:** PostgreSQL database service provided by Replit.
- **Flask-JWT-Extended:** Library for JSON Web Token implementation for authentication.
- **Socket.IO:** Used for real-time notifications and communication.