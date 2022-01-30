import os
import time

from flask import jsonify, send_file

from celery import Celery

from project.machine_learning import app as machine_learning

celery = Celery(__name__)
celery.conf.broker_url = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379")
celery.conf.result_backend = os.environ.get("CELERY_RESULT_BACKEND", "redis://localhost:6379")


@celery.task(name="create_task")
def create_task(info):
    print(info)
    file = info['file']
    column = info['column']
    result = machine_learning.background_file_labeler(file, column)
    return result, 200

