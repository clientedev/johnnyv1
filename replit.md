# MRX System - Gestão de Compras de Sucata Eletrônica

### Overview
The MRX System is a comprehensive platform for managing electronic scrap purchases. Its core functionalities include a star-based pricing system (1★, 2★, 3★), price authorization workflows for negotiations exceeding standard rates, and geolocation tracking for suppliers. The system aims to streamline the procurement process for electronic scrap, enhance pricing control, and improve supplier management.

### Recent Changes
-   **Automatic OC Generation Fix (November 24, 2025)**: Fixed critical bug where Purchase Orders (OC - Ordem de Compra) and inventory lots were not being created automatically when a purchase request was auto-approved (price within table limits). Created `_criar_oc_e_lotes()` helper function to centralize OC/lot creation logic, used by both automatic approval flow and manual admin approval. This ensures consistent behavior: when a request is approved (either automatically or manually), the corresponding OC and lots are immediately generated in the same transaction.

### User Preferences
I want iterative development.
I prefer detailed explanations.
Ask before making major changes.
Do not make changes to the folder `Z`.
Do not make changes to the file `Y`.

### System Architecture

#### UI/UX Decisions
The frontend utilizes Vanilla JavaScript and Tailwind CSS for a modern and responsive user interface, with Service Workers enabling PWA capabilities. The design emphasizes clarity and efficiency for managing materials, prices, and authorizations.

#### Technical Implementations
The system is built with a Flask backend (Python 3.12) using SQLAlchemy for ORM and PostgreSQL (Neon-backed) as the database. Real-time notifications are handled via Socket.IO, and authentication is managed using JWT.

#### Feature Specifications
-   **Material Management**: Supports over 50 types of electronic scrap, including detailed classification and descriptions.
-   **Star-Based Pricing**: Three fixed price tables (1★, 2★, 3★) correspond to supplier quality/reliability. Each material has a specific price per table (R$/kg).
-   **Price Authorization Workflow**: Automatically triggers a request when a negotiated price exceeds the supplier's star-level price table. This workflow includes status tracking (pending, approved, rejected), percentage difference calculation, and the ability to promote suppliers to higher star levels upon approval.
-   **Supplier Geolocalization**: Stores latitude/longitude for suppliers, with new suppliers defaulting to 1★.
-   **Supplier Tax ID Flexibility**: Suppliers can be registered with either CPF (individual) or CNPJ (business) tax IDs. The system includes radio button selection in the registration form, backend validation to ensure the correct document type is provided, and proper storage of the document type alongside the tax ID value. (Implemented November 18, 2025)
-   **Freight Modality**: Purchase requests now include a freight modality field (FOB or CIF) to specify shipping responsibility and cost allocation. The field is required during purchase creation and displayed in request details. (Implemented November 18, 2025)
-   **Excel Import/Export**: Functionality for mass import and export of materials and price tables.
-   **Purchase Wizard**: A multi-step wizard for new purchases, handling supplier selection/registration, collection/delivery details, item scanning, value input, and final confirmation. It integrates with material and pricing data and triggers authorization requests when necessary.
-   **WMS (Warehouse Management System)**: Comprehensive inventory lot management with optimized performance. Features include lot details viewing with eager loading to prevent N+1 queries, direct lot number search with indexed lookup, null-safe user validations across all operations (blocking, reserving, moving inventory), and real-time status tracking. The lot detail modal displays Material and Fornecedor (Supplier) information correctly with robust serialization that handles both eager-loaded and lazy-loaded relationships. Action buttons (Movimentar/Move, Reservar/Reserve, Bloquear/Block, Desbloquear/Unblock, Liberar Reserva/Release Reserve) are fully functional with proper API endpoint routing. (Performance optimizations implemented November 22, 2025; modal display and action button fixes implemented November 22, 2025)
-   **CEP (Postal Code) Lookup Integration**: Automatic address population using ViaCEP API (free Brazilian postal code service). Features include: (1) CEP search field in supplier registration form positioned below CPF field that auto-populates address fields (rua, número, cidade, estado, bairro, complemento); (2) Automatic loading of supplier location data when selecting supplier in solicitation form with all fields remaining editable; (3) Manual CEP search capability in solicitation form for address editing; (4) Robust error handling to prevent DOM failures from breaking price/material loading functionality; (5) Isolated try-catch blocks ensuring address filling failures don't interrupt critical business logic. (Implemented November 23, 2025)

#### System Design Choices
-   **Database Models**: Key models include `MaterialBase`, `TabelaPreco`, `TabelaPrecoItem`, `SolicitacaoAutorizacaoPreco`, and an extended `Fornecedor` model (with `tipo_documento`, `cpf`, and `cnpj` fields) to link suppliers to price tables, responsible buyers, and geolocation. The `Solicitacao` model includes `modalidade_frete` to track shipping terms.
-   **API Endpoints**: Structured RESTful APIs for managing materials (`/api/materiais-base`), price tables (`/api/tabelas-preco`), price authorizations (`/api/autorizacoes-preco`), and suppliers (`/api/fornecedores`) including support for CRUD operations, bulk updates, and Excel integrations. A dedicated endpoint for purchase creation (`/api/compras`) handles complex transaction logic. CEP lookup is available via `/api/fornecedores/buscar-cep/<cep>` endpoint that integrates with ViaCEP API for Brazilian postal code validation and address retrieval.
-   **Security**: Implements JWT for authentication (`@jwt_required`), role-based authorization (`@admin_required`), robust input validation (e.g., non-negative prices, positive weights, negotiated price vs. table price, CPF/CNPJ format and uniqueness validation), and database integrity checks (UNIQUE constraints, foreign keys).
-   **Seed Data**: An idempotent seed script (`seed_modulo_comprador.py`) initializes essential data like price tables, base materials, and initial pricing.
-   **Database Migrations**: Migration scripts handle schema changes safely, including `add_tipo_documento_fornecedor.py` (adds CPF/CNPJ support) and `add_modalidade_frete.py` (adds freight modality tracking).

### External Dependencies

#### Backend
-   Flask 3.0.0
-   Flask-SQLAlchemy
-   Flask-JWT-Extended
-   Flask-SocketIO
-   psycopg2-binary (for PostgreSQL connectivity)
-   pandas (for data manipulation, likely in Excel operations)
-   openpyxl (for Excel file handling)

#### Frontend
-   Tailwind CSS
-   Chart.js (for data visualization, likely in dashboards)
-   Socket.IO Client (for real-time communication)