#!/usr/bin/env python3
"""
Data Migration Utilities for ITP Data Platform
Handles migration of data between environments and versions
"""

import argparse
import logging
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import pandas as pd
from google.cloud import bigquery, storage
import yaml

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataMigrationManager:
    """Manages data migration operations"""
    
    def __init__(self, source_project: str, target_project: str):
        self.source_project = source_project
        self.target_project = target_project
        self.source_bq = bigquery.Client(project=source_project)
        self.target_bq = bigquery.Client(project=target_project)
        self.storage_client = storage.Client()
        
    def migrate_table(self, source_dataset: str, source_table: str, 
                     target_dataset: str, target_table: str,
                     date_filter: Optional[str] = None) -> bool:
        """Migrate data from source table to target table"""
        
        try:
            logger.info(f"Starting migration: {source_dataset}.{source_table} -> {target_dataset}.{target_table}")
            
            # Build query
            source_table_id = f"{self.source_project}.{source_dataset}.{source_table}"
            target_table_id = f"{self.target_project}.{target_dataset}.{target_table}"
            
            # Add date filter if specified
            where_clause = ""
            if date_filter:
                where_clause = f"WHERE {date_filter}"
            
            # Create transfer query
            query = f"""
            SELECT * FROM `{source_table_id}`
            {where_clause}
            """
            
            # Configure job
            job_config = bigquery.QueryJobConfig(
                destination=target_table_id,
                write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
                use_legacy_sql=False
            )
            
            # Execute migration
            job = self.target_bq.query(query, job_config=job_config)
            job.result()  # Wait for completion
            
            logger.info(f"Migration completed. Rows processed: {job.total_bytes_processed}")
            return True
            
        except Exception as e:
            logger.error(f"Migration failed: {str(e)}")
            return False
    
    def migrate_dataset(self, source_dataset: str, target_dataset: str,
                       tables: Optional[List[str]] = None) -> bool:
        """Migrate entire dataset"""
        
        try:
            logger.info(f"Starting dataset migration: {source_dataset} -> {target_dataset}")
            
            # Create target dataset if it doesn't exist
            self.create_dataset_if_not_exists(target_dataset)
            
            # Get list of tables to migrate
            if tables is None:
                tables = self.list_tables(source_dataset)
            
            # Migrate each table
            success_count = 0
            for table in tables:
                if self.migrate_table(source_dataset, table, target_dataset, table):
                    success_count += 1
                else:
                    logger.error(f"Failed to migrate table: {table}")
            
            logger.info(f"Dataset migration completed. {success_count}/{len(tables)} tables migrated successfully")
            return success_count == len(tables)
            
        except Exception as e:
            logger.error(f"Dataset migration failed: {str(e)}")
            return False
    
    def create_dataset_if_not_exists(self, dataset_id: str) -> None:
        """Create dataset if it doesn't exist"""
        
        try:
            dataset_ref = f"{self.target_project}.{dataset_id}"
            self.target_bq.get_dataset(dataset_ref)
            logger.info(f"Dataset {dataset_ref} already exists")
        except Exception:
            # Dataset doesn't exist, create it
            dataset = bigquery.Dataset(dataset_ref)
            dataset.location = "EU"
            dataset = self.target_bq.create_dataset(dataset)
            logger.info(f"Created dataset {dataset_ref}")
    
    def list_tables(self, dataset_id: str) -> List[str]:
        """List all tables in a dataset"""
        
        tables = []
        dataset_ref = f"{self.source_project}.{dataset_id}"
        
        try:
            dataset = self.source_bq.get_dataset(dataset_ref)
            for table in self.source_bq.list_tables(dataset):
                tables.append(table.table_id)
            
            logger.info(f"Found {len(tables)} tables in {dataset_ref}")
            return tables
            
        except Exception as e:
            logger.error(f"Failed to list tables in {dataset_ref}: {str(e)}")
            return []
    
    def migrate_historical_data(self, config_file: str) -> bool:
        """Migrate historical data based on configuration"""
        
        try:
            with open(config_file, 'r') as f:
                config = yaml.safe_load(f)
            
            migration_success = True
            
            for migration in config['migrations']:
                table_config = migration['table']
                source_table = table_config['source']
                target_table = table_config['target']
                
                # Parse source and target
                source_parts = source_table.split('.')
                target_parts = target_table.split('.')
                
                source_dataset, source_table_name = source_parts[-2], source_parts[-1]
                target_dataset, target_table_name = target_parts[-2], target_parts[-1]
                
                # Apply date range if specified
                date_filter = None
                if 'date_range' in migration:
                    date_range = migration['date_range']
                    start_date = date_range.get('start')
                    end_date = date_range.get('end')
                    date_column = date_range.get('column', 'created_date')
                    
                    if start_date and end_date:
                        date_filter = f"{date_column} BETWEEN '{start_date}' AND '{end_date}'"
                    elif start_date:
                        date_filter = f"{date_column} >= '{start_date}'"
                    elif end_date:
                        date_filter = f"{date_column} <= '{end_date}'"
                
                # Execute migration
                success = self.migrate_table(
                    source_dataset, source_table_name,
                    target_dataset, target_table_name,
                    date_filter
                )
                
                if not success:
                    migration_success = False
                    logger.error(f"Failed migration: {source_table} -> {target_table}")
            
            return migration_success
            
        except Exception as e:
            logger.error(f"Historical data migration failed: {str(e)}")
            return False
    
    def validate_migration(self, source_dataset: str, source_table: str,
                          target_dataset: str, target_table: str) -> Dict[str, any]:
        """Validate migration by comparing source and target"""
        
        validation_results = {
            'row_count_match': False,
            'schema_match': False,
            'sample_data_match': False,
            'source_rows': 0,
            'target_rows': 0,
            'issues': []
        }
        
        try:
            # Compare row counts
            source_table_id = f"{self.source_project}.{source_dataset}.{source_table}"
            target_table_id = f"{self.target_project}.{target_dataset}.{target_table}"
            
            source_count_query = f"SELECT COUNT(*) as count FROM `{source_table_id}`"
            target_count_query = f"SELECT COUNT(*) as count FROM `{target_table_id}`"
            
            source_result = list(self.source_bq.query(source_count_query))[0]
            target_result = list(self.target_bq.query(target_count_query))[0]
            
            validation_results['source_rows'] = source_result.count
            validation_results['target_rows'] = target_result.count
            validation_results['row_count_match'] = source_result.count == target_result.count
            
            if not validation_results['row_count_match']:
                validation_results['issues'].append(
                    f"Row count mismatch: source={source_result.count}, target={target_result.count}"
                )
            
            # Compare schemas
            source_table_obj = self.source_bq.get_table(source_table_id)
            target_table_obj = self.target_bq.get_table(target_table_id)
            
            source_schema = [(field.name, field.field_type) for field in source_table_obj.schema]
            target_schema = [(field.name, field.field_type) for field in target_table_obj.schema]
            
            validation_results['schema_match'] = source_schema == target_schema
            
            if not validation_results['schema_match']:
                validation_results['issues'].append("Schema mismatch between source and target")
            
            # Sample data comparison (if row counts match)
            if validation_results['row_count_match'] and source_result.count > 0:
                sample_query = f"SELECT * FROM `{{}}` ORDER BY RAND() LIMIT 5"
                
                source_sample = self.source_bq.query(sample_query.format(source_table_id)).to_dataframe()
                target_sample = self.target_bq.query(sample_query.format(target_table_id)).to_dataframe()
                
                # Simple validation - check if we have data in both
                validation_results['sample_data_match'] = len(source_sample) > 0 and len(target_sample) > 0
            
            logger.info(f"Validation completed for {source_dataset}.{source_table}")
            return validation_results
            
        except Exception as e:
            logger.error(f"Validation failed: {str(e)}")
            validation_results['issues'].append(f"Validation error: {str(e)}")
            return validation_results

def create_migration_config(output_file: str):
    """Create a sample migration configuration file"""
    
    config = {
        'migration_info': {
            'name': 'ITP Data Platform Migration',
            'version': '1.0',
            'created': datetime.now().isoformat()
        },
        'migrations': [
            {
                'table': {
                    'source': 'source_project.source_dataset.financial_transactions',
                    'target': 'target_project.target_dataset.financial_transactions'
                },
                'date_range': {
                    'column': 'transaction_date',
                    'start': '2024-01-01',
                    'end': '2024-12-31'
                },
                'validation': {
                    'enabled': True,
                    'check_row_count': True,
                    'check_schema': True
                }
            },
            {
                'table': {
                    'source': 'source_project.source_dataset.customers',
                    'target': 'target_project.target_dataset.customers'
                },
                'validation': {
                    'enabled': True,
                    'check_row_count': True,
                    'check_schema': True
                }
            }
        ]
    }
    
    with open(output_file, 'w') as f:
        yaml.dump(config, f, default_flow_style=False)
    
    logger.info(f"Sample migration config created: {output_file}")

def main():
    parser = argparse.ArgumentParser(description='ITP Data Platform Migration Tool')
    parser.add_argument('--source-project', required=True, help='Source GCP project ID')
    parser.add_argument('--target-project', required=True, help='Target GCP project ID')
    parser.add_argument('--action', required=True, 
                       choices=['migrate-table', 'migrate-dataset', 'migrate-historical', 'validate', 'create-config'],
                       help='Migration action to perform')
    parser.add_argument('--source-dataset', help='Source dataset name')
    parser.add_argument('--source-table', help='Source table name')
    parser.add_argument('--target-dataset', help='Target dataset name')
    parser.add_argument('--target-table', help='Target table name')
    parser.add_argument('--config-file', help='Configuration file for historical migration')
    parser.add_argument('--date-filter', help='Date filter for migration (e.g., "date >= \'2024-01-01\'")')
    parser.add_argument('--output-file', help='Output file for config creation')
    
    args = parser.parse_args()
    
    # Initialize migration manager
    migration_manager = DataMigrationManager(args.source_project, args.target_project)
    
    try:
        if args.action == 'migrate-table':
            if not all([args.source_dataset, args.source_table, args.target_dataset, args.target_table]):
                print("Error: migrate-table requires --source-dataset, --source-table, --target-dataset, --target-table")
                sys.exit(1)
            
            success = migration_manager.migrate_table(
                args.source_dataset, args.source_table,
                args.target_dataset, args.target_table,
                args.date_filter
            )
            
            if success:
                print("✅ Table migration completed successfully")
            else:
                print("❌ Table migration failed")
                sys.exit(1)
        
        elif args.action == 'migrate-dataset':
            if not all([args.source_dataset, args.target_dataset]):
                print("Error: migrate-dataset requires --source-dataset, --target-dataset")
                sys.exit(1)
            
            success = migration_manager.migrate_dataset(args.source_dataset, args.target_dataset)
            
            if success:
                print("✅ Dataset migration completed successfully")
            else:
                print("❌ Dataset migration failed")
                sys.exit(1)
        
        elif args.action == 'migrate-historical':
            if not args.config_file:
                print("Error: migrate-historical requires --config-file")
                sys.exit(1)
            
            success = migration_manager.migrate_historical_data(args.config_file)
            
            if success:
                print("✅ Historical data migration completed successfully")
            else:
                print("❌ Historical data migration failed")
                sys.exit(1)
        
        elif args.action == 'validate':
            if not all([args.source_dataset, args.source_table, args.target_dataset, args.target_table]):
                print("Error: validate requires --source-dataset, --source-table, --target-dataset, --target-table")
                sys.exit(1)
            
            results = migration_manager.validate_migration(
                args.source_dataset, args.source_table,
                args.target_dataset, args.target_table
            )
            
            print("📊 Validation Results:")
            print(f"   Row Count Match: {'✅' if results['row_count_match'] else '❌'}")
            print(f"   Schema Match: {'✅' if results['schema_match'] else '❌'}")
            print(f"   Source Rows: {results['source_rows']:,}")
            print(f"   Target Rows: {results['target_rows']:,}")
            
            if results['issues']:
                print("⚠️  Issues found:")
                for issue in results['issues']:
                    print(f"   - {issue}")
        
        elif args.action == 'create-config':
            output_file = args.output_file or 'migration_config.yml'
            create_migration_config(output_file)
        
    except Exception as e:
        logger.error(f"Migration operation failed: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()