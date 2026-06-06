from django.core.management.base import BaseCommand
from houses.models import House
from .service import model_service
from .versioning import version_manager
import pandas as pd
import numpy as np
from datetime import datetime


class Command(BaseCommand):
    help = 'Save current model with versioning'

    def add_arguments(self, parser):
        parser.add_argument(
            '--version',
            type=str,
            help='Version description or metadata'
        )
        parser.add_argument(
            '--force-save',
            action='store_true',
            help='Force save even if no model is loaded'
        )

    def handle(self, *args, **options):
        try:
            # Check if model is loaded
            if model_service._model is None and not options['force_save']:
                self.stdout.write(
                    self.style.ERROR('No model loaded. Train a model first.')
                )
                return

            # Prepare metadata
            metadata = {
                "description": options.get('version', 'Model saved'),
                "timestamp": datetime.now().isoformat(),
                "training_records": House.objects.count(),
                "model_type": "XGBoost"
            }

            # Save model with versioning
            version = version_manager.save_model_with_version(
                model_service._model,
                metadata=metadata
            )

            self.stdout.write(
                self.style.SUCCESS(f'Model saved successfully with version: v{version}')
            )

            # Display version info
            current_version = version_manager.get_current_version()
            if current_version:
                self.stdout.write(
                    f' - Version: {current_version["version"]}'
                )
                self.stdout.write(
                    f' - Hash: {current_version["model_hash"][:16]}...'
                )
                self.stdout.write(
                    f' - Saved at: {current_version["timestamp"]}'
                )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Failed to save model: {str(e)}')
            )