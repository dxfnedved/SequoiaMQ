import numpy as np
import torch
import torch.nn as nn
from sklearn.preprocessing import MinMaxScaler
import matplotlib.pyplot as plt
from torch.utils.data import Dataset, DataLoader

class StockDataset(Dataset):
    def __init__(self, X, y):
        self.X = torch.FloatTensor(X)
        self.y = torch.FloatTensor(y)
        
    def __len__(self):
        return len(self.X)
    
    def __getitem__(self, idx):
        return self.X[idx], self.y[idx]

class LSTMModel(nn.Module):
    def __init__(self, input_dim=6, hidden_dim=64, num_layers=2, output_dim=1, dropout=0.2):
        super(LSTMModel, self).__init__()
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers
        self.lstm = nn.LSTM(input_dim, hidden_dim, num_layers, batch_first=True, dropout=dropout)
        self.fc = nn.Sequential(
            nn.Linear(hidden_dim, 32),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(32, output_dim)
        )
    
    def forward(self, x):
        lstm_out, _ = self.lstm(x)
        return self.fc(lstm_out[:, -1, :])

class StockLSTM:
    def __init__(self, time_step=100, feature_dims=6):
        self.time_step = time_step
        self.feature_dims = feature_dims
        self.scalers = [MinMaxScaler(feature_range=(0, 1)) for _ in range(feature_dims)]
        self.model = None
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
    def create_dataset(self, data):
        """创建用于LSTM的数据集，支持多特征"""
        X, Y = [], []
        for i in range(len(data) - self.time_step - 1):
            # 使用所有特征作为输入
            X.append(data[i:(i + self.time_step), :])
            # 使用收盘价作为预测目标
            Y.append(data[i + self.time_step, 0])
        return np.array(X), np.array(Y)
    
    def build_model(self):
        """构建LSTM模型"""
        model = LSTMModel(input_dim=self.feature_dims)
        model = model.to(self.device)
        return model
    
    def prepare_data(self, data):
        """准备训练数据，支持多特征"""
        # 对每个特征进行归一化
        scaled_data = np.zeros_like(data)
        for i in range(self.feature_dims):
            scaled_data[:, i] = self.scalers[i].fit_transform(data[:, i].reshape(-1, 1)).ravel()
        
        X, Y = self.create_dataset(scaled_data)
        
        # 分割训练集和测试集
        train_size = int(len(X) * 0.65)
        X_train = X[0:train_size]
        Y_train = Y[0:train_size]
        X_test = X[train_size:len(X)]
        Y_test = Y[train_size:len(Y)]
        
        return X_train, Y_train, X_test, Y_test
    
    def train(self, X_train, Y_train, epochs=10, batch_size=32, verbose=1):
        """训练模型"""
        if self.model is None:
            self.model = self.build_model()
            
        train_dataset = StockDataset(X_train, Y_train)
        train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
        
        criterion = nn.MSELoss()
        optimizer = torch.optim.Adam(self.model.parameters(), lr=0.001)
        scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='min', factor=0.5, patience=5, verbose=True)
        
        self.model.train()
        for epoch in range(epochs):
            total_loss = 0
            for batch_X, batch_y in train_loader:
                batch_X = batch_X.to(self.device)
                batch_y = batch_y.to(self.device)
                
                optimizer.zero_grad()
                outputs = self.model(batch_X)
                loss = criterion(outputs.squeeze(), batch_y)
                loss.backward()
                
                # 梯度裁剪，防止梯度爆炸
                torch.nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=1.0)
                
                optimizer.step()
                total_loss += loss.item()
            
            avg_loss = total_loss / len(train_loader)
            scheduler.step(avg_loss)
            
            if verbose and (epoch + 1) % 5 == 0:
                print(f'Epoch [{epoch+1}/{epochs}], Loss: {avg_loss:.4f}')
    
    def predict(self, X):
        """进行预测"""
        self.model.eval()
        X = torch.FloatTensor(X).to(self.device)
        with torch.no_grad():
            predictions = self.model(X).cpu().numpy()
        return self.scalers[0].inverse_transform(predictions.reshape(-1, 1))
    
    def evaluate(self, X_test, Y_test):
        """评估模型性能"""
        self.model.eval()
        X_test = torch.FloatTensor(X_test).to(self.device)
        with torch.no_grad():
            test_predict = self.model(X_test).cpu().numpy()
        test_predict = self.scalers[0].inverse_transform(test_predict.reshape(-1, 1))
        Y_test_inv = self.scalers[0].inverse_transform(Y_test.reshape(-1, 1))
        
        from sklearn.metrics import mean_squared_error, mean_absolute_error
        import math
        
        # 计算各种评估指标
        mse = mean_squared_error(Y_test_inv, test_predict)
        rmse = math.sqrt(mse)
        mae = mean_absolute_error(Y_test_inv, test_predict)
        mape = np.mean(np.abs((Y_test_inv - test_predict) / Y_test_inv)) * 100
        
        return {
            'MSE': mse,
            'RMSE': rmse,
            'MAE': mae,
            'MAPE': mape
        }
    
    def plot_predictions(self, actual_data, train_predict, test_predict):
        """可视化预测结果"""
        plt.figure(figsize=(14, 8))
        plt.plot(actual_data, label='实际股价', alpha=0.6)
        
        # 绘制训练预测
        train_predict_plot = np.empty_like(actual_data)
        train_predict_plot[:] = np.nan
        train_predict_plot[self.time_step:len(train_predict)+self.time_step] = train_predict.flatten()
        
        # 绘制测试预测
        test_predict_plot = np.empty_like(actual_data)
        test_predict_plot[:] = np.nan
        test_predict_plot[len(train_predict)+self.time_step:] = test_predict.flatten()
        
        plt.plot(train_predict_plot, label='训练集预测', alpha=0.8)
        plt.plot(test_predict_plot, label='测试集预测', alpha=0.8)
        plt.legend()
        plt.xlabel('交易日')
        plt.ylabel('股价')
        plt.title('股票价格LSTM预测结果')
        plt.grid(True, alpha=0.3)
        plt.show() 