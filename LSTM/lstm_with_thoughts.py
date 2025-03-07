import torch
import torch.nn as nn
import numpy as np
from sklearn.preprocessing import MinMaxScaler
import matplotlib.pyplot as plt
from torch.utils.data import Dataset, DataLoader
from model import StockDataset

class LSTMWithThoughts(nn.Module):
    """
    思维增强LSTM模型
    
    通过引入"思维"机制来增强LSTM的预测能力，为输入序列的每一个时间步生成一种抽象的表征，
    并将这些"思想"融合在一起，与LSTM的输出相结合，以实现更为精准的预测。
    """
    def __init__(self, input_dim=6, hidden_dim=64, thought_dim=32, num_thoughts=5, output_dim=1, dropout=0.2, num_heads=4):
        super(LSTMWithThoughts, self).__init__()
        # LSTM编码器：处理输入序列，为每个时间步生成隐藏状态
        self.encoder = nn.LSTM(input_dim, hidden_dim, batch_first=True, dropout=dropout)
        
        # 思维生成器：为每个隐藏状态创建多层次思维向量
        self.thought_generator = nn.Linear(hidden_dim, num_thoughts * thought_dim)
        
        # 短期思维生成器：捕捉短期波动模式
        self.short_term_thought = nn.Linear(hidden_dim, thought_dim)
        
        # 长期思维生成器：捕捉长期趋势
        self.long_term_thought = nn.Linear(hidden_dim, thought_dim)
        
        # 多头注意力机制：更精细地关注不同时间步的重要性
        self.num_heads = num_heads
        self.multihead_attn = nn.MultiheadAttention(hidden_dim, num_heads, dropout=dropout)
        
        # 注意力机制：对不同时间步的思维进行加权
        self.attention = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim),
            nn.Tanh(),
            nn.Linear(hidden_dim, 1)
        )
        
        # 思维组合器：将所有思维向量合并为单一的综合思维表征
        self.mlp_combine_thoughts = nn.Sequential(
            nn.Linear(num_thoughts * thought_dim + 2 * thought_dim, thought_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(thought_dim, thought_dim)
        )
        
        # 输出层：将最终的LSTM隐藏状态与综合思维相结合，做出最终预测
        self.output_layer = nn.Linear(hidden_dim + thought_dim, output_dim)
        
        # 门控机制：动态调整短期和长期思维的权重
        self.gate = nn.Sequential(
            nn.Linear(hidden_dim, 2),
            nn.Softmax(dim=1)
        )
        
        # 残差连接层：帮助梯度流动和信息传递
        self.residual_fc = nn.Linear(input_dim, hidden_dim)
        
        # 层归一化：提高训练稳定性
        self.layer_norm1 = nn.LayerNorm(hidden_dim)
        self.layer_norm2 = nn.LayerNorm(thought_dim)
    
    def forward(self, x):
        # 残差连接的输入
        residual = self.residual_fc(x[:, -1, :])
        
        # LSTM编码
        lstm_out, (h_enc, _) = self.encoder(x)
        h_last = h_enc[-1]
        
        # 应用层归一化
        h_last = self.layer_norm1(h_last + residual)  # 残差连接
        
        # 多头注意力机制
        # 将lstm_out转换为注意力机制所需的形状 [seq_len, batch, hidden_dim]
        attn_input = lstm_out.transpose(0, 1)
        attn_output, _ = self.multihead_attn(
            query=h_last.unsqueeze(0),
            key=attn_input,
            value=attn_input
        )
        attn_output = attn_output.squeeze(0)  # [batch, hidden_dim]
        
        # 生成基础思维
        thoughts = self.thought_generator(h_last)
        
        # 生成短期和长期思维
        short_term = self.short_term_thought(lstm_out[:, -5:, :].mean(dim=1))  # 最近5个时间步的平均
        long_term = self.long_term_thought(lstm_out.mean(dim=1))  # 全序列平均
        
        # 计算注意力权重
        attention_weights = torch.softmax(self.attention(lstm_out).squeeze(-1), dim=1)
        
        # 应用注意力机制
        context = torch.bmm(attention_weights.unsqueeze(1), lstm_out).squeeze(1)
        
        # 计算门控权重
        gate_weights = self.gate(h_last)
        
        # 加权组合短期和长期思维
        weighted_thoughts = torch.cat([
            thoughts,
            gate_weights[:, 0].unsqueeze(1) * short_term,
            gate_weights[:, 1].unsqueeze(1) * long_term
        ], dim=1)
        
        # 应用MLP合并思维
        combined_thoughts = self.mlp_combine_thoughts(weighted_thoughts)
        
        # 应用层归一化
        combined_thoughts = self.layer_norm2(combined_thoughts)
        
        # 将组合思想与多头注意力输出和最终的LSTM隐藏状态合并
        # 使用加权平均而不是简单拼接，减少维度爆炸
        combined_rep = torch.cat((combined_thoughts, attn_output), dim=-1)
        
        # 得出最终预测结果
        prediction = self.output_layer(combined_rep)
        return prediction

class StockLSTMWithThoughts:
    """
    股票预测的思维增强LSTM模型封装类
    
    提供了数据准备、模型训练、预测和评估的完整功能。
    """
    def __init__(self, time_step=100, feature_dims=6, thought_dim=32, num_thoughts=5, num_heads=4):
        self.time_step = time_step
        self.feature_dims = feature_dims
        self.thought_dim = thought_dim
        self.num_thoughts = num_thoughts
        self.num_heads = num_heads
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
        """构建思维增强LSTM模型"""
        model = LSTMWithThoughts(
            input_dim=self.feature_dims,
            hidden_dim=64,
            thought_dim=self.thought_dim,
            num_thoughts=self.num_thoughts,
            output_dim=1,
            dropout=0.2,
            num_heads=self.num_heads
        )
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
        optimizer = torch.optim.Adam(self.model.parameters(), lr=0.001, weight_decay=1e-5)  # 添加L2正则化
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
        plt.title('思维增强LSTM股票价格预测结果')
        plt.grid(True, alpha=0.3)
        plt.show() 