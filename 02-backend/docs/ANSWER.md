# 后端题 —— Spring Boot 3.2.0 + Spring Security：受保护的 `HelloWorld` 与登录接口

**技术栈：** Java 17 · Spring Boot 3.2.0 · Spring Security 6.2 · JJWT 0.12.3 · Maven
**代码：** `code/`（`mvn spring-boot:run` 启动，默认端口 8080）

---

## 1. 一表对照交付要求

| 题目要求 | 实现 |
|---|---|
| Spring Boot **3.2.0** | `pom.xml` → parent `spring-boot-starter-parent:3.2.0` |
| `GET` 接口返回 `"Hello World"` | `GET /api/hello`，`HelloController.hello()` |
| ……且**必须经过 SpringSecurity 认证** | `anyRequest().authenticated()` + JWT 过滤器；未认证调用返回 **401** |
| 用户名密码登录接口 | `POST /api/auth/login`，账号 `test` / `123456` |
| 加分：端到端真的能跑 | 5 个集成测试（`mvn test`）+ 下方真实的 `curl` 输出 |

## 2. 接口契约

### `POST /api/auth/login` —— 公开

```bash
curl -X POST http://localhost:8080/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"123456"}'
```

```json
{
  "accessToken": "eyJhbGciOiJIUzI1NiJ9.eyJ...",
  "tokenType": "Bearer",
  "expiresIn": 3600,
  "username": "test"
}
```

账号或密码错误 → `401 {"status":401,"message":"Invalid username or password",...}`

### `GET /api/hello` —— 需要 Bearer Token

```bash
curl -i http://localhost:8080/api/hello \
  -H "Authorization: Bearer $TOKEN"
```

```
HTTP/1.1 200
Content-Type: text/plain;charset=UTF-8

Hello World
```

不带请求头时：

```
HTTP/1.1 401
{"status":401,"message":"Authentication required: send 'Authorization: Bearer <token>'"}
```

### `GET /api/me` —— 额外接口，用来证明 SecurityContext 真的被填进去了

```json
{"username":"test","authenticated":true,"authorities":["ROLE_USER"]}
```

## 3. 设计取舍（以及为什么）

**用 JWT，不用 session。** 这套 API 是无状态的：`SessionCreationPolicy.STATELESS`，
CSRF 和 form-login 全部关闭，`Authorization: Bearer` 是唯一的凭证载体。如果换成 session cookie，
就必须处理 CSRF token（因为浏览器会自动带上 cookie），并且在负载均衡后面还需要粘性会话或
Redis 会话存储 —— 对一个只有两个接口的服务来说，这是纯成本、没有收益。

**过滤器链顺序。** `JwtAuthenticationFilter` 注册在 `UsernamePasswordAuthenticationFilter`
**之前**。这个过滤器从不抛异常：token 非法就保持匿名，随后由 `anyRequest().authenticated()`
统一拒绝。把「要不要放行」集中在一处，意味着**新增接口默认是受保护的** —— 想开放某个路径，
必须显式写一行 `permitAll()`，这是一次看得见、可评审的动作。

**密码存储。** 用 `BCryptPasswordEncoder`，演示账号的密码在启动时哈希 —— 从不做明文比对，
也从不打印到日志。角色来自 `app.demo.user.roles` 配置。

**错误也返回 JSON。** 无状态 API 不能返回默认的 HTML 错误页，所以配了
`AuthenticationEntryPoint` 负责 401，配了 `@RestControllerAdvice` 处理 `AuthenticationException`
和参数校验失败。结果是：每一种失败形态对客户端来说都是稳定的结构。

**配置优先于硬编码。** 账号和签名密钥放在 `application.yml`，可用 `APP_JWT_SECRET` 覆盖；
`JwtService` 在密钥短于 32 字节时**直接启动失败**（HS256 的硬性要求），而不是悄悄签出弱签名。

## 4. 测试覆盖（`mvn test`）

```
Tests run: 5, Failures: 0, Errors: 0, Skipped: 0
```

| 测试 | 断言 |
|---|---|
| `helloWithoutTokenIsRejected` | 401 + JSON 响应体 |
| `loginReturnsToken` | 200、`tokenType=Bearer`、token 非空 |
| `loginThenCallProtectedApi` | 登录 → 带 Bearer → `200 "Hello World"` → `/api/me` 返回 `test` |
| `wrongPasswordIsRejected` | 401 |
| `tamperedTokenIsRejected` | 401（`Bearer not-a-real-jwt`） |

测试跑在真实的过滤器链上（`@SpringBootTest` + `MockMvc`），所以一旦有人不小心把
`/api/hello` 放开，测试会立刻失败。

## 5. 工程结构

```
code/
├── pom.xml
└── src/
    ├── main/java/com/example/securitydemo/
    │   ├── SecurityDemoApplication.java
    │   ├── config/      SecurityConfig, AppProperties
    │   ├── security/    JwtService, JwtAuthenticationFilter
    │   ├── controller/  AuthController, HelloController
    │   ├── dto/         LoginRequest, LoginResponse
    │   └── web/         GlobalExceptionHandler
    ├── main/resources/application.yml
    └── test/java/.../SecurityIntegrationTest.java
```

## 6. 距离生产还差什么（刻意的范围控制）

| 缺口 | 后果 | 补法 |
|---|---|---|
| 内存里只有一个用户 | 没有注册、没有持久化 | 用 `users` 表实现 `UserDetailsService` |
| 没有 refresh token | 60 分钟后必须重新登录 | 增加 `/api/auth/refresh` + 轮换式 refresh token |
| 没有吊销名单 | 被盗的 token 在过期前一直有效 | 缩短 TTL + Redis 里维护 `jti` 黑名单 |
| 没有限流 | 登录接口可被暴力破解 | Bucket4j / 网关限流 + 失败锁定 |
| 密钥有默认值 | 默认值是公开的 | 非 dev profile 下缺少 `APP_JWT_SECRET` 时直接启动失败 |
