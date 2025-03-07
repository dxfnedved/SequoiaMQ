# Title
实现基础用户管理功能


# Introduction
创建基础的用户管理系统,包含用户的基本信息:唯一标识ID、用户名称、头像和手机号。这将作为整个应用的基础用户模型。


- User 
  - id, bigint, 主键, 自增
  - name, varchar(255), 用户名称
  - avatar_url, varchar(255), 头像URL
  - mobile, varchar(255), 手机号
  - energy_coin, bigint, 能量币，默认 0




# Tasks
- [ ] 设计并实现用户数据库架构
  - [ ] 创建用户表,包含字段:id、name、avatar_url、mobile。avatar_url 或者是直接外部链接，或者是 oss 的链接


- [ ] 实现用户CRUD接口
  - [ ] 创建用户接口(带字段验证)
  - [ ] 获取用户信息接口
  - [ ] 更新用户信息接口
  - [ ] 删除用户接口(软删除)
  - [ ] 用户列表接口(带分页)
