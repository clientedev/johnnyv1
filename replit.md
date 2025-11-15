# Sistema MRX - Gestão de Compra de Placas Eletrônicas

## Overview
The MRX System is a comprehensive solution for managing the procurement of electronic circuit boards, from purchase request to inventory receipt. It features lot-based tracking, quality classification, and supplier management. Key capabilities include AI-powered classification, geolocalized data capture, dynamic pricing, and a robust Role-Based Access Control (RBAC) system. The project aims to streamline procurement, enhance traceability, and provide detailed analytics for improved decision-making in the electronic board market.

## User Preferences
No specific user preferences were provided in the original document.

## System Architecture

### Stack Tecnológica
- **Backend:** Flask 3.0.0, SQLAlchemy
- **Banco de Dados:** PostgreSQL (Replit Database)
- **Autenticação:** JWT (Flask-JWT-Extended)
- **IA:** Google Gemini for automatic board classification
- **WebSocket:** Socket.IO for real-time notifications
- **Frontend:** HTML/CSS/JavaScript

### UI/UX Decisions
The system features a modernized frontend with a gradient design for intuitive user interaction. It includes native camera integration for board photo capture, visual star selection for quality classification, and real-time price calculation. Dashboards offer quick access cards and statistics.

### Technical Implementations
- **AI Integration:** Google Gemini classifies boards (1-5 stars) with textual justifications based on image analysis, allowing user acceptance or override.
- **Geolocation:** Captures GPS coordinates and supports manual address input.
- **Dynamic Pricing:** Configures prices per supplier, lot type, and star rating, with unique pricing per kg for each combination.
- **Excel Integration:** Provides import/export for lot types and prices, including auto-generation for 15 price points.
- **Automated Lot Type Codes:** Generates read-only codes (e.g., TL001) for lot types.
- **Workflow Automation:** Manages the full lifecycle from request creation, administrative approval, lot creation, to final inventory entry, with automatic generation of Service Orders (OS) upon Purchase Order (OC) approval.
- **Robust Validation:** Backend enforces validation rules, such as blocking zero values and mandatory configuration.
- **RBAC System:** Implements comprehensive Role-Based Access Control with 7 standard profiles.
- **Advanced JWT Authentication:** Uses access tokens (24-hour validity) and refresh tokens (30-day validity).
- **Auditing System:** Automatically logs all critical actions (creation, updates, deletions, login attempts) with IP, user agent, and detailed JSON data.
- **Purchase Order (OC) Module:** Manages the full workflow for generating purchase orders from approved requests with a strict 1:1 relationship, RBAC controls, and comprehensive audit trails including GPS/IP/device metadata.
- **Conference/Receipt Inspection Module:** Automated conference system that opens when drivers finalize service orders (OS). Features include weighing validation (with 10% divergence threshold), quality checks, photo evidence upload, automatic divergence detection, ADM approval workflow for divergences, and automatic lot creation upon approval. The system calculates expected weight as sum(peso_kg × quantidade) for all request items.
- **Data Models:** Key models include `TipoLote` (board types), `FornecedorTipoLotePreco` (price matrix), `Solicitacao` (purchase requests), `ItemSolicitacao` (request items), `OrdemCompra` (purchase orders), `AuditoriaOC` (OC audit trail), `ConferenciaRecebimento` (receipt inspections), `Lote` (item grouping), `EntradaEstoque` (inventory entries), `Perfil` (roles), `Veiculo`, `Motorista`, and `AuditoriaLog`.
- **API URL Handling:** `fetchAPI()` helper automatically prefixes endpoints with `/api`, requiring calls to pass endpoints without this prefix.

### Feature Specifications
- **Multi-item Requests:** Supports requests with multiple items, each with individual classification and details.
- **Configurable Star Ratings:** Administrative interface for configuring 1-5 star ratings per supplier and lot type.
- **Supplier Management:** Cadastro and editing of suppliers, with automatic data retrieval from sources like Receita Federal.
- **Vehicle and Driver Management:** Dedicated modules for managing vehicles and drivers.

## External Dependencies
- **Google Gemini API:** Used for AI-powered image analysis and classification.
- **Replit Database:** PostgreSQL database service.
- **Flask-JWT-Extended:** Library for JWT authentication.
- **Socket.IO:** Used for real-time notifications.