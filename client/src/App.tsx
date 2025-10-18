import { GoogleOAuthProvider } from "@react-oauth/google";
import { RouterProvider, createRouter } from "@tanstack/react-router";
import { ThemeProvider } from "@/context/ThemeContext";
import { QueryProvider } from "@/context/QueryClient";
import { Toaster } from "@/components/ui/sonner";
import { routeTree } from "./routeTree.gen";

const router = createRouter({ routeTree });

declare module "@tanstack/react-router" {
  interface Register {
    router: typeof router;
  }
}

function App() {
  return (
    <QueryProvider>
      <ThemeProvider defaultTheme="system" storageKey="ui-theme">
        <GoogleOAuthProvider clientId={import.meta.env.VITE_GOOGLE_CLIENT_ID}>
          <RouterProvider router={router} />
          <Toaster />
        </GoogleOAuthProvider>
      </ThemeProvider>
    </QueryProvider>
  );
}

export default App;
