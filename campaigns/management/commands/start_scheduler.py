from django.core.management.base import BaseCommand
import subprocess


class Command(BaseCommand):
    help = "Start Celery worker and beat scheduler"

    def handle(self, *args, **options):
        try:
            self.stdout.write("Ensuring Redis is running...")

            # Celery worker
            self.stdout.write("Starting Celery worker...")
            worker = subprocess.Popen(
                ["celery", "-A", "core", "worker", "--loglevel=info"]
            )

            # Celery beat
            self.stdout.write("Starting Celery beat...")
            beat = subprocess.Popen(["celery", "-A", "core", "beat", "--loglevel=info"])

            # Start Flower for monitoring
            self.stdout.write("Starting Flower monitoring...")
            flower = subprocess.Popen(["celery", "-A", "core", "flower"])

            self.stdout.write("All services started. Press CTRL+C to stop.")

            # Wait for processes
            worker.wait()
            beat.wait()
            flower.wait()

        except KeyboardInterrupt:
            self.stdout.write("Stopping services...")
