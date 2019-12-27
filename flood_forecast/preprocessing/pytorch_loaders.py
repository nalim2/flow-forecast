from torch.utils.data import Dataset
import pandas as pd
import torch
from typing import Type, List


class CSVDataLoader(Dataset):
    def __init__(self, file_path:str, history_length:int, forecast_length:int, target_col:List, 
                 relevant_cols:List, scaling=None, start_stamp:int=0, end_stamp:int=None):
        """
        A data loader that takes a CSV file and properly batches for use in training/eval a PyTorch model
        :param file_path: The path to the CSV file you wish to use. 
        :param history_length: This is the length of the historical time series data you wish to utilize for forecasting
        :param forecast_length: The number of time steps to forecast ahead (for transformer this must equal history_length)
        :param relevant_cols: Supply column names you wish to predict in the forecast (others will not be used)
        :param target_col: The target column or columns you to predict. If you only have one still use a list ['cfs']
        :param scaling: (highly reccomended) If provided should be a subclass of sklearn.base.BaseEstimator 
        and sklearn.base.TransformerMixin) i.e StandardScaler,  MaxAbsScaler, MinMaxScaler, etc) Note without 
        a scaler the loss is likely to explode and cause infinite loss which will corrupt weights
        :param start_stamp int: Optional if you want to only use part of a CSV for training, validation or testing supply these
        "param end_stamp int: Optional if you want to only use part of a CSV for training, validation, or testing supply these
        """
        super().__init__()
        self.forecast_history = history_length
        self.forecast_length = forecast_length 
        self.df = pd.read_csv(file_path)[relevant_cols]
        self.scale = None
        if start_stamp !=0:
            self.df = self.df[start_stamp:]
        if end_stamp != None: 
            self.df = self.df[:end_stamp]
        if scaling is not None:
            self.scale = scaling
            temp_df = self.scale.fit_transform(self.df)
            # We define a second scaler to scale the end output 
            # back to normal as models might not necessarily predict
            # other present time series values.
            self.targ_scaler = self.scale
            self.targ_scaler.fit_transform(self.df[target_col[0]].values.reshape(-1,1))
            self.df = pd.DataFrame(temp_df, index=self.df.index, columns=self.df.columns)
        if (len(self.df) - self.df.count()).max()!= 0:
            raise "Error nan values detected in data. Please run interpolate ffill or bfill on data"
        self.targ_col = target_col
        
    def __getitem__(self, idx):
        rows = self.df.iloc[idx:self.forecast_history+idx]
        targs_idx_start = self.forecast_history+idx
        targ_rows = self.df.iloc[targs_idx_start:self.forecast_length+targs_idx_start]
        src_data = rows.to_numpy()
        src_data = torch.from_numpy(src_data).float()
        trg_dat = targ_rows.to_numpy()
        trg_dat = torch.from_numpy(trg_dat).float()
        return src_data, trg_dat
    
    def __len__(self):
        return len(self.df.index)-self.forecast_history-self.forecast_length-1
    
    def inverse_scale(self, result_data):
        result_data_np = result_data.numpy()
        return self.targ_scaler.inverse_transform(result_data_np)
        
        

        
        
        
    
        
