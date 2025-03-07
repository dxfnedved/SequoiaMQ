<template>
  <div class="watchlist-container">
    <div class="watchlist-header">
      <h3>自选股列表</h3>
      <el-button v-if="watchlistStore.stockCount > 0" size="small" type="danger" @click="confirmClear">清空</el-button>
    </div>
    
    <el-empty v-if="watchlistStore.stockCount === 0" description="暂无自选股" />
    
    <el-table v-else :data="watchlistStore.stocks" style="width: 100%" stripe>
      <el-table-column prop="code" label="代码" width="100" />
      <el-table-column prop="name" label="名称" width="120" />
      <el-table-column label="操作" width="80">
        <template #default="scope">
          <el-button size="small" type="danger" @click="removeStock(scope.row.code)">
            <el-icon><Delete /></el-icon>
          </el-button>
        </template>
      </el-table-column>
    </el-table>
    
    <el-dialog
      v-model="dialogVisible"
      title="确认清空"
      width="30%"
    >
      <span>确定要清空所有自选股吗？此操作不可恢复。</span>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="danger" @click="clearWatchlist">确定</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import { Delete } from '@element-plus/icons-vue'
import { useWatchlistStore } from '@/stores/watchlist'
import { ElMessage } from 'element-plus'

export default {
  name: 'Watchlist',
  components: {
    Delete
  },
  setup() {
    const watchlistStore = useWatchlistStore()
    const dialogVisible = ref(false)
    
    onMounted(() => {
      watchlistStore.loadWatchlist()
    })
    
    const removeStock = (code) => {
      watchlistStore.removeStock(code)
      ElMessage({
        type: 'success',
        message: '已从自选股移除'
      })
    }
    
    const confirmClear = () => {
      dialogVisible.value = true
    }
    
    const clearWatchlist = () => {
      watchlistStore.clearWatchlist()
      dialogVisible.value = false
      ElMessage({
        type: 'success',
        message: '已清空自选股列表'
      })
    }
    
    return {
      watchlistStore,
      dialogVisible,
      removeStock,
      confirmClear,
      clearWatchlist
    }
  }
}
</script>

<style scoped>
.watchlist-container {
  padding: 16px;
}

.watchlist-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.watchlist-header h3 {
  margin: 0;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}
</style> 