import os

log_dir = os.path.expanduser('~') + "/.larkin/logs/"
log_file = log_dir + "larkin.log"

# if directory doesn't exist, create it
if not os.path.isdir(log_dir):
    os.makedirs(log_dir)
# if log doesn't exist, create it
fp = open(log_file, "a")
fp.close()

config = {
    'version': 1,
    'formatters': {
        'simple': {
            'format': '%(asctime)s - %(levelname)s - %(message)s'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
            'level': 'INFO',
            'stream': 'ext://sys.stdout'
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'formatter': 'simple',
            'level': 'DEBUG',
            'filename': log_file,
            'maxBytes': 1024,
            'backupCount': 0  # grow indefinitely--can change to roll in future
        },
        'timed_file': {
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'formatter': 'simple',
            'level': 'DEBUG',
            'filename': log_file,
            'when': 'midnight',
            'utc': True,
            'interval': 1,
            'backupCount': 7
        }
    },
    'loggers': {
        'root': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False
        }
    }
}
