import logging
import threading
import time
from django.utils import timezone
from lessons.models import InteractionRecord, LessonSession

logger = logging.getLogger(__name__)


class TimeoutHandler:
    def __init__(self):
        self._running = False
        self._thread = None

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._check_timeouts, daemon=True)
        self._thread.start()
        logger.info("Timeout handler started")

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("Timeout handler stopped")

    def _check_timeouts(self):
        while self._running:
            try:
                cutoff = timezone.now() - timezone.timedelta(seconds=35)
                pending_interactions = InteractionRecord.objects.filter(
                    user_answer='',
                    is_correct__isnull=True,
                    answered_at__lt=cutoff
                )

                for interaction in pending_interactions:
                    interaction.is_correct = False
                    interaction.ml_service_success = False
                    interaction.save()
                    logger.info(f"Marked timeout for interaction {interaction.id}")

            except Exception as e:
                logger.error(f"Error in timeout handler: {e}")

            time.sleep(10)


timeout_handler = TimeoutHandler()
