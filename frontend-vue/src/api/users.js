/**
 * 用户管理API
 */
import { get, post, put, delete as del } from './request';

/**
 * 获取用户列表
 * @param {Object} params - 查询参数
 * @param {number} params.page - 页码
 * @param {number} params.page_size - 每页数量
 * @param {string} params.search - 搜索关键词
 * @returns {Promise} - 返回用户列表数据
 */
export function getUsers(params = {}) {
  return request({
    url: '/users',
    method: 'get',
    params
  });
}

/**
 * 获取单个用户信息
 * @param {number} userId - 用户ID
 * @returns {Promise} - 返回用户信息
 */
export function getUser(userId) {
  return request({
    url: `/users/${userId}`,
    method: 'get'
  });
}

/**
 * 创建用户
 * @param {Object} data - 用户数据
 * @param {string} data.name - 用户名称
 * @param {string} data.avatar_url - 头像URL
 * @param {string} data.mobile - 手机号
 * @returns {Promise} - 返回创建的用户数据
 */
export function createUser(data) {
  return request({
    url: '/users',
    method: 'post',
    data
  });
}

/**
 * 更新用户信息
 * @param {number} userId - 用户ID
 * @param {Object} data - 更新的用户数据
 * @returns {Promise} - 返回更新后的用户数据
 */
export function updateUser(userId, data) {
  return request({
    url: `/users/${userId}`,
    method: 'put',
    data
  });
}

/**
 * 删除用户
 * @param {number} userId - 用户ID
 * @returns {Promise} - 返回删除结果
 */
export function deleteUser(userId) {
  return request({
    url: `/users/${userId}`,
    method: 'delete'
  });
}

export default {
  getUsers,
  getUser,
  createUser,
  updateUser,
  deleteUser
}; 
