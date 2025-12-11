"""
Celery tasks for core app.
"""
from celery import shared_task
import logging

logger = logging.getLogger(__name__)


@shared_task
def sample_task():
    """Sample periodic task."""
    logger.info("Sample task executed")
    return "Task completed"


@shared_task
def rebuild_tree_task(app_name: str):
    """
    Task to rebuild MPTT tree structure.
    
    Args:
        app_name: Either 'limitless' or 'boostyfi'
    """
    if app_name == 'limitless':
        from apps.limitless.models import LimitlessUser
        LimitlessUser.objects.rebuild()
        logger.info("Limitless tree rebuilt successfully")
    elif app_name == 'boostyfi':
        from apps.boostyfi.models import BoostyFiUser
        BoostyFiUser.objects.rebuild()
        logger.info("BoostyFi tree rebuilt successfully")
    else:
        logger.error(f"Unknown app: {app_name}")
        raise ValueError(f"Unknown app: {app_name}")
    
    return f"{app_name} tree rebuilt"
