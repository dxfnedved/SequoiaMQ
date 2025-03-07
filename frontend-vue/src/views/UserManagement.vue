<template>
  <div class="user-management-container">
    <div class="page-header">
      <h1>用户管理</h1>
      <el-button type="primary" @click="handleAddUser">添加用户</el-button>
    </div>

    <!-- 搜索和过滤 -->
    <div class="search-bar">
      <el-input
        v-model="searchQuery"
        placeholder="搜索用户名或手机号"
        clearable
        @clear="handleSearch"
        @keyup.enter="handleSearch"
      >
        <template #append>
          <el-button @click="handleSearch">
            <i class="el-icon-search"></i>
          </el-button>
        </template>
      </el-input>
    </div>

    <!-- 用户列表 -->
    <el-table
      v-loading="loading"
      :data="users"
      border
      style="width: 100%"
      @row-click="handleRowClick"
    >
      <el-table-column prop="id" label="ID" width="80"></el-table-column>
      <el-table-column prop="name" label="用户名称" min-width="120"></el-table-column>
      <el-table-column label="头像" width="100">
        <template #default="{ row }">
          <el-avatar :size="40" :src="row.avatar_url" v-if="row.avatar_url">
            {{ row.name.charAt(0).toUpperCase() }}
          </el-avatar>
          <el-avatar :size="40" v-else>{{ row.name.charAt(0).toUpperCase() }}</el-avatar>
        </template>
      </el-table-column>
      <el-table-column prop="mobile" label="手机号" min-width="120"></el-table-column>
      <el-table-column prop="energy_coin" label="能量币" width="100"></el-table-column>
      <el-table-column label="操作" width="200" fixed="right">
        <template #default="{ row }">
          <el-button type="primary" size="small" @click.stop="handleEditUser(row)">编辑</el-button>
          <el-button type="danger" size="small" @click.stop="handleDeleteUser(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 分页器 -->
    <div class="pagination-container">
      <el-pagination
        background
        layout="total, sizes, prev, pager, next, jumper"
        :total="total"
        :page-size="pageSize"
        :current-page="currentPage"
        :page-sizes="[10, 20, 50, 100]"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
      ></el-pagination>
    </div>

    <!-- 用户表单对话框 -->
    <el-dialog 
      :title="dialogTitle" 
      v-model="dialogVisible" 
      width="500px"
      @close="resetForm"
    >
      <el-form 
        ref="userFormRef" 
        :model="userForm" 
        :rules="rules" 
        label-width="100px"
      >
        <el-form-item label="用户名称" prop="name">
          <el-input v-model="userForm.name" placeholder="请输入用户名称"></el-input>
        </el-form-item>
        <el-form-item label="手机号" prop="mobile">
          <el-input v-model="userForm.mobile" placeholder="请输入手机号"></el-input>
        </el-form-item>
        <el-form-item label="头像URL" prop="avatar_url">
          <el-input v-model="userForm.avatar_url" placeholder="请输入头像URL"></el-input>
        </el-form-item>
        <el-form-item label="能量币" prop="energy_coin" v-if="dialogType === 'edit'">
          <el-input-number v-model="userForm.energy_coin" :min="0" :step="1"></el-input-number>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" @click="submitForm" :loading="submitLoading">确定</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { reactive, ref, computed, onMounted } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { usersApi } from '@/api';

export default {
  name: 'UserManagement',
  setup() {
    // 状态定义
    const loading = ref(false);
    const submitLoading = ref(false);
    const users = ref([]);
    const total = ref(0);
    const currentPage = ref(1);
    const pageSize = ref(10);
    const searchQuery = ref('');
    
    // 对话框相关状态
    const dialogVisible = ref(false);
    const dialogType = ref('add'); // 'add' 或 'edit'
    const dialogTitle = computed(() => dialogType.value === 'add' ? '添加用户' : '编辑用户');
    const userFormRef = ref(null);
    
    // 表单数据和验证规则
    const userForm = reactive({
      id: null,
      name: '',
      mobile: '',
      avatar_url: '',
      energy_coin: 0
    });
    
    const rules = {
      name: [
        { required: true, message: '请输入用户名称', trigger: 'blur' },
        { min: 2, max: 20, message: '长度在 2 到 20 个字符', trigger: 'blur' }
      ],
      mobile: [
        { required: true, message: '请输入手机号', trigger: 'blur' },
        { pattern: /^1[3-9]\d{9}$/, message: '请输入正确的手机号', trigger: 'blur' }
      ]
    };
    
    // 获取用户列表
    const fetchUsers = async () => {
      loading.value = true;
      try {
        const params = {
          page: currentPage.value,
          page_size: pageSize.value
        };
        
        if (searchQuery.value) {
          params.search = searchQuery.value;
        }
        
        const response = await usersApi.getUsers(params);
        if (response.code === 200) {
          users.value = response.data.items;
          total.value = response.data.total;
        } else {
          ElMessage.error(response.message || '获取用户列表失败');
        }
      } catch (error) {
        console.error('获取用户列表失败:', error);
        ElMessage.error('获取用户列表失败');
      } finally {
        loading.value = false;
      }
    };
    
    // 添加用户
    const handleAddUser = () => {
      dialogType.value = 'add';
      dialogVisible.value = true;
    };
    
    // 编辑用户
    const handleEditUser = (row) => {
      dialogType.value = 'edit';
      Object.assign(userForm, row);
      dialogVisible.value = true;
    };
    
    // 行点击事件
    const handleRowClick = (row) => {
      console.log('查看用户详情:', row);
      // 可以在这里实现查看用户详情的功能
    };
    
    // 删除用户
    const handleDeleteUser = (row) => {
      ElMessageBox.confirm(
        `确定要删除用户 "${row.name}" 吗？`,
        '警告',
        {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        }
      ).then(async () => {
        try {
          const response = await usersApi.deleteUser(row.id);
          if (response.code === 200) {
            ElMessage.success('删除成功');
            fetchUsers();
          } else {
            ElMessage.error(response.message || '删除失败');
          }
        } catch (error) {
          console.error('删除用户失败:', error);
          ElMessage.error('删除用户失败');
        }
      }).catch(() => {
        // 取消删除
      });
    };
    
    // 提交表单
    const submitForm = async () => {
      if (!userFormRef.value) return;
      
      await userFormRef.value.validate(async (valid) => {
        if (!valid) return;
        
        submitLoading.value = true;
        
        try {
          let response;
          
          if (dialogType.value === 'add') {
            // 创建用户
            const { name, mobile, avatar_url } = userForm;
            response = await usersApi.createUser({ name, mobile, avatar_url });
          } else {
            // 更新用户
            const { id, name, mobile, avatar_url, energy_coin } = userForm;
            response = await usersApi.updateUser(id, { name, mobile, avatar_url, energy_coin });
          }
          
          if (response.code === 200 || response.code === 201) {
            ElMessage.success(dialogType.value === 'add' ? '添加成功' : '更新成功');
            dialogVisible.value = false;
            fetchUsers();
          } else {
            ElMessage.error(response.message || (dialogType.value === 'add' ? '添加失败' : '更新失败'));
          }
        } catch (error) {
          console.error(dialogType.value === 'add' ? '添加用户失败:' : '更新用户失败:', error);
          ElMessage.error(dialogType.value === 'add' ? '添加用户失败' : '更新用户失败');
        } finally {
          submitLoading.value = false;
        }
      });
    };
    
    // 重置表单
    const resetForm = () => {
      if (userFormRef.value) {
        userFormRef.value.resetFields();
      }
      
      Object.assign(userForm, {
        id: null,
        name: '',
        mobile: '',
        avatar_url: '',
        energy_coin: 0
      });
    };
    
    // 搜索
    const handleSearch = () => {
      currentPage.value = 1;
      fetchUsers();
    };
    
    // 分页器事件处理
    const handleSizeChange = (val) => {
      pageSize.value = val;
      fetchUsers();
    };
    
    const handleCurrentChange = (val) => {
      currentPage.value = val;
      fetchUsers();
    };
    
    // 初始化
    onMounted(() => {
      fetchUsers();
    });
    
    return {
      // 数据
      loading,
      submitLoading,
      users,
      total,
      currentPage,
      pageSize,
      searchQuery,
      dialogVisible,
      dialogType,
      dialogTitle,
      userForm,
      userFormRef,
      rules,
      
      // 方法
      fetchUsers,
      handleAddUser,
      handleEditUser,
      handleDeleteUser,
      handleRowClick,
      submitForm,
      resetForm,
      handleSearch,
      handleSizeChange,
      handleCurrentChange
    };
  }
};
</script>

<style scoped>
.user-management-container {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.search-bar {
  margin-bottom: 20px;
  width: 350px;
}

.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}
</style> 