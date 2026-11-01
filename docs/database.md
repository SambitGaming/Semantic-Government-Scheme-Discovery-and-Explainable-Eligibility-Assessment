# Day 19 — Database Integration

## 1. Database Technology

The project uses SQLite as the database management system.

SQLite was selected because it is lightweight, serverless,
portable and suitable for the research prototype.

## 2. Database File

The database is stored at:

data/government_schemes.db

## 3. Database Tables

### 3.1 schemes

The `schemes` table stores government scheme information.

Important fields include:

- scheme_id
- scheme_name
- ministry
- category
- status
- target_group
- description
- eligibility
- benefits
- required_documents
- application_mode
- keywords
- official_url
- source
- verification_date
- rule_version

### 3.2 eligibility_rules

The `eligibility_rules` table stores deterministic
eligibility rules used by the eligibility engine.

Important fields include:

- rule_id
- scheme_id
- rule_type
- field
- operator
- value
- explanation
- version
- source_url

### 3.3 rule_versions

The `rule_versions` table provides version tracking
for eligibility rules.

Important fields include:

- version_id
- scheme_id
- version
- effective_date
- source_url
- notes

## 4. Relationships

A scheme can have multiple eligibility rules.

A scheme can also have multiple rule versions.

The relationship is:

Scheme
|
|-- Eligibility Rules
|
|-- Rule Versions

## 5. Traceability

Eligibility rules contain source information and version
information.

This allows an eligibility decision to be associated
with the corresponding rule and official source.

## 6. Data Flow

The database receives data from the project's frozen
scheme and eligibility-rule datasets.

The architecture is:

Frozen Scheme Dataset
        |
        v
     SQLite
        |
        +---- Schemes
        |
        +---- Eligibility Rules
        |
        +---- Rule Versions
        |
        v
   Backend Integration
        |
        v
 Eligibility Engine
        |
        v
 Explainable Result

## 7. Testing

The database was tested using:

- Scheme count verification
- Rule count verification
- Scheme retrieval
- Scheme rule retrieval
- Retrieval of all schemes

## 8. Purpose

The database provides centralized persistent storage for
scheme information and eligibility rules.

It will be used by the backend integration developed
in Day 20.