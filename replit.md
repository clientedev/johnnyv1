# Sistema MRX - Gestão de Compra de Placas Eletrônicas

## Overview
The MRX System is a comprehensive solution for managing the procurement of electronic circuit boards. It features lot-based tracking, quality classification (star ratings), supplier management, and an automated workflow from purchase request to inventory receipt. Key capabilities include AI-powered classification, geolocalized data capture, dynamic pricing, and a robust Role-Based Access Control (RBAC) system. The project aims to streamline the procurement process, enhance traceability, and provide detailed analytics for better decision-making in the electronic board market.

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