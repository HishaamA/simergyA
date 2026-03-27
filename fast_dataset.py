import pandas as pd
import torch
from torch.utils.data import Dataset

IGNORE_INDEX = -100
MAX_LENGTH = 2048

class PreprocessedDataset(Dataset):
    def __init__(self, parquet_path):
        super().__init__()

        df = pd.read_parquet(parquet_path)

        print(f"Converting {len(df)} samples to tensors...")
        self.input_ids_tensors = [
            torch.tensor(ids, dtype=torch.long)
            for ids in df['input_ids'].tolist()
        ]
        print(f"Loaded {len(self.input_ids_tensors)} pre-tokenized samples from {parquet_path}")

    def __len__(self):
        return len(self.input_ids_tensors)

    def __getitem__(self, index):
        if not 0 <= index < len(self):
            raise IndexError("Index out of range")

        input_ids = self.input_ids_tensors[index]

        return dict(
            input_ids=input_ids,
            labels=input_ids.clone(),
            input_ids_lens=len(input_ids),
            labels_lens=len(input_ids),
        )