import logging
import time
import requests
from celery import shared_task
from django.conf import settings

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=5,
    time_limit=60,
    soft_time_limit=45
)
def validate_answer_task(self, interaction_id, question_id, user_answer):
    from .models import InteractionRecord

    try:
        interaction = InteractionRecord.objects.get(id=interaction_id)
    except InteractionRecord.DoesNotExist:
        logger.error(f"Interaction {interaction_id} not found")
        return

    start_time = time.time()

    try:
        response = requests.post(
            f"{settings.ML_SERVICE_URL}/validate",
            json={
                'question_id': str(question_id),
                'user_answer': user_answer
            },
            timeout=35
        )

        response_time = time.time() - start_time

        if response.status_code == 200:
            result = response.json()
            interaction.is_correct = result.get('result') == 1
            interaction.ml_service_success = True
            interaction.response_time = response_time
            interaction.save()

            logger.info(f"Validation complete for {interaction_id}: correct={interaction.is_correct}")

        elif response.status_code == 503:
            interaction.is_correct = None
            interaction.ml_service_success = False
            interaction.response_time = response_time
            interaction.save()

            logger.warning(f"ML service unavailable for {interaction_id}")

        else:
            raise Exception(f"Unexpected status code: {response.status_code}")

    except requests.exceptions.Timeout:
        logger.error(f"Timeout validating {interaction_id}")
        interaction.is_correct = None
        interaction.ml_service_success = False
        interaction.response_time = time.time() - start_time
        interaction.save()

    except requests.exceptions.RequestException as exc:
        logger.error(f"Request failed for {interaction_id}: {exc}")
        interaction.is_correct = None
        interaction.ml_service_success = False
        interaction.response_time = time.time() - start_time
        interaction.save()

        try:
            self.retry(exc=exc)
        except self.MaxRetriesExceededError:
            logger.error(f"Max retries exceeded for {interaction_id}")

    except Exception as exc:
        logger.error(f"Unexpected error for {interaction_id}: {exc}")
        interaction.is_correct = None
        interaction.ml_service_success = False
        interaction.save()


@shared_task
def record_timeout_answer(interaction_id):
    from .models import InteractionRecord

    try:
        interaction = InteractionRecord.objects.get(id=interaction_id)
        if not interaction.user_answer:
            interaction.is_correct = False
            interaction.ml_service_success = False
            interaction.save()
            logger.info(f"Recorded timeout answer for {interaction_id}")
    except InteractionRecord.DoesNotExist:
        logger.error(f"Interaction {interaction_id} not found for timeout")
