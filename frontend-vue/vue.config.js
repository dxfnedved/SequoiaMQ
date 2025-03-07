/**
 * Vue项目配置文件
 * 包含开发服务器配置、构建配置等
 */
const { defineConfig } = require('@vue/cli-service')

module.exports = defineConfig({
  // 禁用生产环境的source map以减小包大小
  productionSourceMap: false,
  
  // 开发服务器配置
  devServer: {
    // 开发服务器端口
    port: 8080,
    // 自动打开浏览器
    open: true,
    // 代理配置，用于连接后端API
    proxy: {
      '/api': {
        // 目标API地址
        target: 'http://localhost:8002',
        // 是否更改请求的origin
        changeOrigin: true,
        // 路径重写
        pathRewrite: {
          '^/api': ''
        },
        // 添加详细日志
        logLevel: 'debug',
        // 代理错误处理
        onError: (err, req, res) => {
          console.error('API代理错误:', err);
        },
        // 代理响应处理
        onProxyRes: (proxyRes, req, res) => {
          console.log(`请求: ${req.method} ${req.path} -> 状态: ${proxyRes.statusCode}`);
        }
      }
    },
    client: {
      overlay: {
        warnings: false,
        errors: true
      }
    }
  },
  
  // 全局CSS配置 
  css: {
    loaderOptions: {
      sass: {
        // 全局引入变量和混合
        additionalData: `
          @import "@/assets/styles/variables.scss";
        `
      }
    }
  },

  configureWebpack: {
    resolve: {
      fallback: {
        path: false,
        fs: false,
        crypto: false,
        stream: false,
        os: false
      }
    }
  },

  chainWebpack: config => {
    config.optimization.minimizer('terser').tap(args => {
      args[0].terserOptions.output = {
        ...args[0].terserOptions.output,
        comments: false
      }
      return args
    })
  }
}) 