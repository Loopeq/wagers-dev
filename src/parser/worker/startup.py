from celery.signals import worker_ready


@worker_ready.connect
def at_start(sender, **kwargs):
    with sender.app.connection() as conn:
        sender.app.send_task("run_collect_heads", connection=conn)
        sender.app.send_task("run_collect_content", connection=conn)
