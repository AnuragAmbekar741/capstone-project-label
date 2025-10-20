title OAuth Authentication & Token Refresh Flow

Client->Google: 1. Initiate Google Login
Google->Client: 2. Return ID Token
Client->API: 3. POST /auth/google\n{id_token}
API->Google: 4. Verify ID Token
Google->API: 5. Return User Info\n(email, name, google_id)
API->DB: 6. Check if user exists\n(get_user_by_google_id)
DB->API: 7. Return user or null
API->DB: 8. Create user if new\n(create_user)
API->JWT: 9. Create Access Token (3min)
JWT->API: 10. Return access_token
API->JWT: 11. Create Refresh Token (7days)
JWT->API: 12. Return refresh_token
API->Client: 13. Return tokens\n{access_token, refresh_token}
Client->Client: 14. Store tokens in cookies
Client->Client: 15. Redirect to /dashboard

note over Client,DB: _2. Protected Route Access_

Client->Client: 16. Check route guard\n(requireAuth)
Client->API: 17. GET /auth/me\nAuthorization: Bearer <token>
API->JWT: 18. Verify access token
JWT->API: 19. Return decoded payload
API->DB: 20. Get user by ID
DB->API: 21. Return user data
API->Client: 22. Return user profile

note over Client,DB: _3. Proactive Token Refresh (before expiry)_

Client->Client: 23. Request Interceptor:\nDetect token expires < 60s
Client->API: 24. POST /auth/refresh\n{refresh_token}
API->JWT: 25. Verify refresh token\n(check type, expiry)
JWT->API: 26. Return decoded payload
API->DB: 27. Verify user exists
DB->API: 28. Return user
API->JWT: 29. Create new Access Token
JWT->API: 30. Return new access_token
API->JWT: 31. Create new Refresh Token
JWT->API: 32. Return new refresh_token
API->Client: 33. Return new tokens
Client->Client: 34. Update cookies\n35. Continue with original request

note over Client,DB: _4. Token Expired (Fallback)_

Client->API: 36. Request with expired token
API->JWT: 37. Verify token
JWT->API: 38. Token expired!
API->Client: 39. 401 Unauthorized
Client->Client: 40. Response Interceptor:\nClear tokens & redirect to /auth
