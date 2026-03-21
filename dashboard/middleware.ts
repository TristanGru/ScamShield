import { withMiddlewareAuthRequired } from "@auth0/nextjs-auth0/edge";

// Enforce Auth0 session on all /dashboard/* routes
export default withMiddlewareAuthRequired();

export const config = {
  matcher: ["/dashboard/:path*", "/api/events/:path*", "/api/status/:path*"],
};
