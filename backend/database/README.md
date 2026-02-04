# Enterprise Database Schema

This directory contains the enterprise database schema and seed data for the AI-Powered Business Intelligence Analyst application.

## Files

- **`enterprise_schema.sql`** - Complete DDL for 40+ tables with realistic enterprise relationships
- **`enterprise_seed_data.sql`** - Comprehensive seed data for all tables
- **`DDL_DOCUMENTATION.md`** - Detailed documentation for generating schemas externally
- **`DATABASE_MIGRATION_GUIDE.md`** - Guide for configuring and using multiple database types
- **`init.sql`** - Original simple schema (4 tables)
- **`seed_data.sql`** - Original simple seed data

## Quick Start

### Using Enterprise Schema (Recommended)

1. **Configure your database** in `.env`:
   ```bash
   DATABASE_TYPE=postgresql
   POSTGRES_HOST=localhost
   POSTGRES_PORT=5432
   POSTGRES_USER=postgres
   POSTGRES_PASSWORD=your_password
   POSTGRES_DB=ai_bi_db
   ```

2. **Create database** (if needed):
   ```bash
   createdb -U postgres ai_bi_db
   ```

3. **Run schema**:
   ```bash
   psql -U postgres -d ai_bi_db -f database/enterprise_schema.sql
   ```

4. **Seed data** (optional):
   ```bash
   psql -U postgres -d ai_bi_db -f database/enterprise_seed_data.sql
   ```

5. **Start application** - schema introspection will run automatically!

## Schema Overview

The enterprise schema includes:

### HR Management (7 tables)
- Departments, job positions, employees
- Employee skills, attendance, leave requests
- Performance reviews

### Finance (7 tables)
- Chart of accounts, financial periods
- General ledger, invoices, payments
- Budgets

### Sales & CRM (8 tables)
- Customers, leads, opportunities
- Sales orders, quotes with line items

### Inventory & Supply Chain (9 tables)
- Product categories, products
- Suppliers, warehouses, inventory
- Purchase orders, inventory movements

### Projects & Tasks (4 tables)
- Projects, project tasks
- Time entries

### Customer Support (3 tables)
- Support tickets, ticket comments
- Knowledge base articles

### Marketing (4 tables)
- Marketing campaigns, campaign leads
- Events, event attendees

**Total: 42 tables** with comprehensive relationships

## Database Support

The application now supports:
- ✅ **PostgreSQL** (recommended)
- ✅ **MySQL/MariaDB**
- ✅ **SQLite** (development only)

See `DATABASE_MIGRATION_GUIDE.md` for configuration details.

## Key Features

- **Realistic Relationships**: Proper foreign keys and referential integrity
- **Hierarchical Structures**: Self-referencing tables for departments, accounts, categories, tasks
- **Audit Trails**: created_at/updated_at timestamps
- **Soft Deletes**: Status fields instead of hard deletes
- **Performance**: Indexes on foreign keys and frequently queried columns
- **Multi-Module**: Covers all major enterprise functions

## Generating Schema Externally

If you want to generate the schema using Claude or ChatGPT:

1. See `DDL_DOCUMENTATION.md` for detailed specifications
2. Use the provided prompt template
3. Specify your target database (PostgreSQL, MySQL, or SQLite)
4. Execute the generated DDL

## Notes

- The schema is PostgreSQL-specific by default
- For MySQL/SQLite, you may need to adjust syntax (see DDL_DOCUMENTATION.md)
- All monetary values use DECIMAL for precision
- The schema supports future ETL integration
- Vector embeddings work with PostgreSQL (pgvector extension)

## Next Steps

1. Choose your database type
2. Configure environment variables
3. Run schema initialization
4. Start querying with natural language!

The application will automatically introspect your schema and generate embeddings for intelligent query understanding.

