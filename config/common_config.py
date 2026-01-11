import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(override=True)
options = dict()

options["gemini_api_key"]=os.getenv("GEMINI_API_KEY")
options["groq_api_key"]=os.getenv("GROQ_API_KEY")

options["data_dir"] = Path(os.getcwd()) / "data"
if not os.path.exists(options["data_dir"]):
    os.mkdir(options["data_dir"])
options['workspace'] = options["data_dir"] / "workspace"
if not os.path.exists(options['workspace']):
    os.mkdir(options['workspace'])
options['working_dir'] = options["data_dir"] / "working_dir"
if not os.path.exists(options['working_dir']):
    os.mkdir(options['working_dir'])

options['need_log_file'] = False
if options['need_log_file']:
    options['log_file_path'] = os.getenv("LOG_FILE_PATH", None)
    if options['log_file_path'] is None:
        os.makedirs("./logs", exist_ok=True)
        options['log_file_path'] = "./logs/lightrag.log"

options['file_upload_dir'] = options["data_dir"] / "file_upload_dir"
if not os.path.exists(options['file_upload_dir']):
    os.mkdir(options['file_upload_dir'])

options['embedding_dimension'] = int(os.getenv("EMBEDDING_DIMENSION", 768))