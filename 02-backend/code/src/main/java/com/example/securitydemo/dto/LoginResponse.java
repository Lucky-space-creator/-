package com.example.securitydemo.dto;

public record LoginResponse(
        String accessToken,
        String tokenType,
        long expiresIn,
        String username) {

    public static LoginResponse bearer(String token, long expiresIn, String username) {
        return new LoginResponse(token, "Bearer", expiresIn, username);
    }
}
