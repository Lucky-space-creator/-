# Back-end Task — Spring Boot 3.2.0 + Spring Security: protected `HelloWorld` + login API

**Stack:** Java 17 · Spring Boot 3.2.0 · Spring Security 6.2 · JJWT 0.12.3 · Maven
**Code:** `code/` (run `mvn spring-boot:run`, default port 8080)

---

## 1. Deliverable in one table

| Requirement | Implementation |
|---|---|
| Spring Boot **3.2.0** | `pom.xml` → parent `spring-boot-starter-parent:3.2.0` |
| `GET` HelloWorld API returning `"Hello World"` | `GET /api/hello`, `HelloController.hello()` |
| …that **requires SpringSecurity authentication** | `anyRequest().authenticated()` + JWT filter; unauthenticated call returns **401** |
| Username-password login API | `POST /api/auth/login`, credentials `test` / `123456` |
| Bonus: it actually works end-to-end | 5 integration tests (`mvn test`) + real `curl` transcript below |

## 2. API contract

### `POST /api/auth/login` — public

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

Wrong credentials → `401 {"status":401,"message":"Invalid username or password",...}`

### `GET /api/hello` — requires a Bearer token

```bash
curl -i http://localhost:8080/api/hello \
  -H "Authorization: Bearer $TOKEN"
```

```
HTTP/1.1 200
Content-Type: text/plain;charset=UTF-8

Hello World
```

Without the header:

```
HTTP/1.1 401
{"status":401,"message":"Authentication required: send 'Authorization: Bearer <token>'"}
```

### `GET /api/me` — extra, proves the SecurityContext is populated

```json
{"username":"test","authenticated":true,"authorities":["ROLE_USER"]}
```

## 3. Design decisions (and why)

**JWT, not session.** The API is stateless: `SessionCreationPolicy.STATELESS`, CSRF and form-login
disabled, `Authorization: Bearer` as the only credential carrier. A session cookie version would
need CSRF tokens (because the browser sends cookies automatically) and sticky sessions or a Redis
session store behind a load balancer — cost with no benefit for a two-endpoint API.

**Filter chain order.** `JwtAuthenticationFilter` is registered *before*
`UsernamePasswordAuthenticationFilter`. It never throws: an invalid token just leaves the request
anonymous, and `anyRequest().authenticated()` then rejects it. Putting the decision in one place
means a new endpoint is protected by default — a new `permitAll()` line is an explicit, reviewable
act.

**Password storage.** `BCryptPasswordEncoder`, and the demo password is hashed at startup — never
compared as plain text, and never logged. Roles come from `app.demo.user.roles`.

**Errors as JSON.** A stateless API must not return the default HTML error page, so there is an
`AuthenticationEntryPoint` for 401 and a `@RestControllerAdvice` for `AuthenticationException` /
validation failures. Outcome: every failure mode has a stable shape for the client.

**Config over hard-coding.** Credentials and the signing secret live in `application.yml` and can
be overridden by `APP_JWT_SECRET`; `JwtService` refuses to start if the secret is shorter than 32
bytes (HS256 requirement) instead of silently generating weak signatures.

## 4. What the tests cover (`mvn test`)

```
Tests run: 5, Failures: 0, Errors: 0, Skipped: 0
```

| Test | Assertion |
|---|---|
| `helloWithoutTokenIsRejected` | 401 + JSON body |
| `loginReturnsToken` | 200, `tokenType=Bearer`, non-empty token |
| `loginThenCallProtectedApi` | login → `Bearer` → `200 "Hello World"` → `/api/me` shows `test` |
| `wrongPasswordIsRejected` | 401 |
| `tamperedTokenIsRejected` | 401 (`Bearer not-a-real-jwt`) |

Tests run against the real filter chain (`@SpringBootTest` + `MockMvc`), so they fail if someone
accidentally opens up `/api/hello`.

## 5. Project layout

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

## 6. Not production-ready, and why (deliberate scope)

| Gap | Consequence | Fix |
|---|---|---|
| Single in-memory user | no registration, no persistence | `UserDetailsService` backed by a `users` table |
| No refresh token | re-login after 60 min | add `/api/auth/refresh` + rotating refresh token |
| No revocation list | a stolen token is valid until expiry | short TTL + `jti` blacklist in Redis |
| No rate limiting | login endpoint is brute-forceable | Bucket4j / gateway rate limit + lockout |
| Secret from env with a default | the default is public | fail fast when `APP_JWT_SECRET` is absent in a non-dev profile |
