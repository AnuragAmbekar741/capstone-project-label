import { GoogleOAuthProvider } from "@react-oauth/google";
import { RouterProvider, createRouter } from "@tanstack/react-router";
import { ThemeProvider } from "@/context/ThemeContext";

import { routeTree } from "./routeTree.gen";

const router = createRouter({ routeTree });

declare module "@tanstack/react-router" {
  interface Register {
    router: typeof router;
  }
}

function App() {
  return (
    <ThemeProvider defaultTheme="system" storageKey="ui-theme">
      <GoogleOAuthProvider clientId={import.meta.env.VITE_GOOGLE_CLIENT_ID}>
        <RouterProvider router={router} />
      </GoogleOAuthProvider>
    </ThemeProvider>
  );
}

export default App;
