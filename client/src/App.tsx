import { GoogleOAuthProvider } from "@react-oauth/google";
import Auth from "./views/auth/Auth";

function App() {
  return (
    <GoogleOAuthProvider clientId={import.meta.env.VITE_GOOGLE_CLIENT_ID}>
      <div className="App">
        <Auth />
      </div>
    </GoogleOAuthProvider>
  );
}

export default App;
