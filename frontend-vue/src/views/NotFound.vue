<!-- 404页面 -->
<template>
  <div class="not-found-container">
    <div class="not-found-content">
      <img src="@/assets/404.png" alt="页面未找到" class="error-image">
      <h1>404</h1>
      <h2>抱歉，您访问的页面不存在</h2>
      <p>可能的原因：</p>
      <ul>
        <li>页面地址输入错误</li>
        <li>页面已被移除或重命名</li>
        <li>您没有访问该页面的权限</li>
      </ul>
      <div class="actions">
        <router-link to="/" class="home-button">返回首页</router-link>
        <button class="back-button" @click="goBack">返回上一页</button>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'NotFound',
  methods: {
    goBack() {
      this.$router.go(-1);
    }
  }
}
</script>

<style scoped>
.not-found-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
  background-color: #f8f9fa;
}

.not-found-content {
  text-align: center;
  max-width: 600px;
  padding: 2rem;
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.error-image {
  max-width: 200px;
  margin-bottom: 1rem;
}

h1 {
  font-size: 4rem;
  margin: 0;
  color: #f56c6c;
}

h2 {
  font-size: 1.5rem;
  margin: 1rem 0;
  color: #333;
}

p {
  margin: 1rem 0 0.5rem;
  font-weight: bold;
}

ul {
  text-align: left;
  margin: 0 auto;
  width: fit-content;
  padding-left: 1.5rem;
}

li {
  margin-bottom: 0.5rem;
  color: #606266;
}

.actions {
  margin-top: 2rem;
  display: flex;
  justify-content: center;
  gap: 1rem;
}

.home-button, .back-button {
  padding: 0.75rem 1.5rem;
  border-radius: 4px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
}

.home-button {
  background-color: #409eff;
  color: white;
  border: none;
  text-decoration: none;
}

.home-button:hover {
  background-color: #66b1ff;
}

.back-button {
  background-color: white;
  color: #606266;
  border: 1px solid #dcdfe6;
}

.back-button:hover {
  border-color: #409eff;
  color: #409eff;
}
</style> 