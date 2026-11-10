package com.example.securitydemo.controller;

import java.util.Map;

import org.springframework.http.MediaType;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

/**
 * The protected resource required by the assignment.
 */
@RestController
@RequestMapping("/api")
public class HelloController {

    /**
     * Protected endpoint: without a valid Bearer token the request never reaches this method,
     * because {@code anyRequest().authenticated()} in SecurityConfig rejects it with 401.
     */
    @GetMapping(value = "/hello", produces = MediaType.TEXT_PLAIN_VALUE)
    public String hello() {
        return "Hello World";
    }

    /** Extra endpoint proving the SecurityContext is really populated (not just a header check). */
    @GetMapping(value = "/me", produces = MediaType.APPLICATION_JSON_VALUE)
    public Map<String, Object> me(Authentication authentication) {
        return Map.of(
                "username", authentication.getName(),
                "authenticated", authentication.isAuthenticated(),
                "authorities", authentication.getAuthorities().stream()
                        .map(Object::toString)
                        .toList());
    }
}
