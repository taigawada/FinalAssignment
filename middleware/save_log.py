import pandas as pd
import os

def jsonl_to_csv(jsonl_path: str, jsonl_save: bool):
    print(os.path.getsize(jsonl_path))
    if os.path.getsize(jsonl_path) > 0:
        df = pd.read_json(jsonl_path, orient='records', lines=True)
        save_dir = os.path.dirname(jsonl_path)
        file_name = os.path.splitext(os.path.basename(jsonl_path))[0] + '.csv'
        df.to_csv(os.path.join(save_dir, file_name))
        if not jsonl_save:
            os.remove(jsonl_path)
    else:
        os.remove(jsonl_path)
