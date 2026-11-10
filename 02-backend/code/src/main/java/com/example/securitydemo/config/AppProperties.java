package com.example.securitydemo.config;

import org.springframework.boot.context.properties.ConfigurationProperties;

/**
 * Type-safe binding for the {@code app.*} namespace in application.yml.
 */
@ConfigurationProperties(prefix = "app")
public class AppProperties {

    private final Jwt jwt = new Jwt();
    private final Demo demo = new Demo();

    public Jwt getJwt() {
        return jwt;
    }

    public Demo getDemo() {
        return demo;
    }

    public static class Jwt {
        /** HMAC-SHA256 secret. Must be at least 32 bytes. Override via APP_JWT_SECRET. */
        private String secret = "change-me-please-this-is-a-32-byte-demo-secret";
        /** Token time-to-live in minutes. */
        private long expirationMinutes = 60;

        public String getSecret() {
            return secret;
        }

        public void setSecret(String secret) {
            this.secret = secret;
        }

        public long getExpirationMinutes() {
            return expirationMinutes;
        }

        public void setExpirationMinutes(long expirationMinutes) {
            this.expirationMinutes = expirationMinutes;
        }
    }

    public static class Demo {
        private final User user = new User();

        public User getUser() {
            return user;
        }
    }

    public static class User {
        private String username = "test";
        private String password = "123456";
        private String roles = "USER";

        public String getUsername() {
            return username;
        }

        public void setUsername(String username) {
            this.username = username;
        }

        public String getPassword() {
            return password;
        }

        public void setPassword(String password) {
            this.password = password;
        }

        public String getRoles() {
            return roles;
        }

        public void setRoles(String roles) {
            this.roles = roles;
        }
    }
}
