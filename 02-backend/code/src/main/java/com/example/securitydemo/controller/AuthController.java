package com.example.securitydemo.controller;

import org.springframework.http.ResponseEntity;
import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import com.example.securitydemo.dto.LoginRequest;
import com.example.securitydemo.dto.LoginResponse;
import com.example.securitydemo.security.JwtService;

import jakarta.validation.Valid;

/**
 * Username/password login endpoint. This is the only publicly reachable API.
 */
@RestController
@RequestMapping("/api/auth")
public class AuthController {

    private final AuthenticationManager authenticationManager;
    private final JwtService jwtService;

    public AuthController(AuthenticationManager authenticationManager, JwtService jwtService) {
        this.authenticationManager = authenticationManager;
        this.jwtService = jwtService;
    }

    @PostMapping("/login")
    public ResponseEntity<LoginResponse> login(@Valid @RequestBody LoginRequest request) {
        // Delegates to UserDetailsService + PasswordEncoder(BCrypt); throws
        // BadCredentialsException on a wrong pair, which GlobalExceptionHandler maps to 401.
        Authentication authentication = authenticationManager.authenticate(
                new UsernamePasswordAuthenticationToken(request.username(), request.password()));

        String token = jwtService.generateToken(authentication.getName());
        return ResponseEntity.ok(LoginResponse.bearer(token, jwtService.getExpirationSeconds(), authentication.getName()));
    }
}
