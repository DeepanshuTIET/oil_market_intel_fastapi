from apscheduler.schedulers.background import BackgroundScheduler


def start_scheduler():
    # Use n8n or external cron in production. This is optional in-process scheduling.
    scheduler = BackgroundScheduler(timezone='UTC')
    # Example: scheduler.add_job(lambda: ..., 'cron', hour=15, minute=45)
    scheduler.start()
    return scheduler
