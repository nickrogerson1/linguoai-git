import os
from celery import Celery
import ssl

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "linguoai.settings")
app = Celery("linguoai")
app.config_from_object("django.conf:settings", namespace="CELERY")


# app.conf.update(
    # broker_use_ssl = True
                # broker_use_ssl = {
                #     'ssl_keyfile': '/Users/nickrogerson/Desktop/LinguoAI/Linguo-ai/LinguoAI/linguoai/rab_conf/tls-gen/basic/client_myhost.local/key.pem',
                #     'ssl_certfile': '/Users/nickrogerson/Desktop/LinguoAI/Linguo-ai/LinguoAI/linguoai/rab_conf/tls-gen/basic/client_myhost.local/cert.pem',
                #     'ssl_ca_certs': '/Users/nickrogerson/Desktop/LinguoAI/Linguo-ai/LinguoAI/linguoai/rab_conf/tls-gen/basic/server_myhost.local/cert.pem',
                #     'ssl_cert_reqs': ssl.CERT_REQUIRED
                #     },
#                 redis_backend_use_ssl = {
#                     'ssl_keyfile': '/Users/nickrogerson/Desktop/LinguoAI/Linguo-ai/LinguoAI/linguoai/conf_new/domain.key',
#                     'ssl_certfile': '/Users/nickrogerson/Desktop/LinguoAI/Linguo-ai/LinguoAI/linguoai/conf_new/domain.crt',
#                     'ssl_ca_certs': '/Users/nickrogerson/Desktop/LinguoAI/Linguo-ai/LinguoAI/linguoai/conf_new/rootCA.crt',
#                     'ssl_cert_reqs': ssl.CERT_REQUIRED
#                 }
            # )

app.autodiscover_tasks()

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')