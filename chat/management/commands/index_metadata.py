import yaml
import os
from django.core.management.base import BaseCommand
from chat.models import MetadataVector
from sentence_transformers import SentenceTransformer

class Command(BaseCommand):
    help = 'Index metadata from schema_metadata.yaml into MetadataVector'

    def handle(self, *args, **options):
        self.stdout.write("Loading schema_metadata.yaml...")
        metadata_path = os.path.join(os.getcwd(), 'schema_metadata.yaml')
        with open(metadata_path, 'r') as f:
            metadata = yaml.safe_load(f)

        self.stdout.write("Loading embedding model (all-MiniLM-L6-v2)...")
        model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

        self.stdout.write("Clearing existing metadata vectors...")
        MetadataVector.objects.all().delete()

        tables = metadata.get('tables', {})
        for table_name, table_info in tables.items():
            if not table_info.get('queryable', True):
                continue

            # Index table description
            table_desc = table_info.get('description', '')
            aliases = ", ".join(table_info.get('aliases', []))
            content = f"Table: {table_name}. Description: {table_desc}. Aliases: {aliases}"
            
            self.stdout.write(f"Indexing table: {table_name}")
            embedding = model.encode(content).tolist()
            MetadataVector.objects.create(
                content=content,
                metadata_key=table_name,
                embedding=embedding
            )

            # Index column descriptions
            columns = table_info.get('columns', {})
            for col_name, col_info in columns.items():
                col_desc = col_info.get('description', '')
                content = f"Column: {col_name} in table {table_name}. Description: {col_desc}"
                
                self.stdout.write(f"  Indexing column: {col_name}")
                embedding = model.encode(content).tolist()
                MetadataVector.objects.create(
                    content=content,
                    metadata_key=f"{table_name}.{col_name}",
                    embedding=embedding
                )

        self.stdout.write(self.style.SUCCESS("Successfully indexed metadata."))
