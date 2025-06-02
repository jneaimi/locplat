-- Field Mapping Tables for LocPlat
-- Run this SQL to create the required tables

-- Create field_configs table
CREATE TABLE field_configs (
    id SERIAL PRIMARY KEY,
    client_id VARCHAR(255) NOT NULL,
    collection_name VARCHAR(255) NOT NULL,
    field_paths JSON NOT NULL DEFAULT '[]',
    field_types JSON DEFAULT '{}',
    is_translation_collection BOOLEAN DEFAULT FALSE,
    primary_collection VARCHAR(255),
    directus_translation_pattern VARCHAR(50) DEFAULT 'collection_translations',
    rtl_field_mapping JSON DEFAULT '{}',
    language_field_overrides JSON DEFAULT '{}',
    batch_processing BOOLEAN DEFAULT FALSE,
    preserve_html_structure BOOLEAN DEFAULT TRUE,
    content_sanitization BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_used_at TIMESTAMP WITH TIME ZONE,
    custom_transformations JSON DEFAULT '{}',
    validation_rules JSON DEFAULT '{}'
);

-- Create index for faster lookups
CREATE INDEX idx_field_configs_client_collection ON field_configs(client_id, collection_name);

-- Create field_processing_logs table
CREATE TABLE field_processing_logs (
    id SERIAL PRIMARY KEY,
    client_id VARCHAR(255) NOT NULL,
    collection_name VARCHAR(255) NOT NULL,
    field_config_id INTEGER,
    operation_type VARCHAR(50) NOT NULL,
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT,
    processing_time_ms INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create index for logs
CREATE INDEX idx_field_processing_logs_client ON field_processing_logs(client_id);
CREATE INDEX idx_field_processing_logs_created_at ON field_processing_logs(created_at);

-- Show created tables
\dt
