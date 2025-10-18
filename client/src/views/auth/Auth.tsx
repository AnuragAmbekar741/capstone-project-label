// Replace the imports at the top
import React from "react";
import { motion } from "framer-motion";
import { GoogleLogin } from "@react-oauth/google";
import { ArrowLeft, Mail, Shield, Zap, Moon, Sun, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { useTheme } from "@/hooks/usetheme";
import { useNavigate } from "@tanstack/react-router";
import { useAnimatedBackground } from "@/hooks/useAnimatedBackground";
import { toast } from "sonner";
import { useGoogleLogin } from "@/hooks/auth/useGoogleAuth";

const fadeInUp = {
  initial: { opacity: 0, y: 60 },
  animate: { opacity: 1, y: 0 },
  transition: { duration: 0.6, ease: "easeOut" },
};

const Auth: React.FC = () => {
  const { theme, setTheme } = useTheme();
  const navigate = useNavigate();
  const canvasRef = useAnimatedBackground();

  // Use the mutation hook
  const googleLoginMutation = useGoogleLogin();

  const toggleTheme = () => {
    setTheme(theme === "light" ? "dark" : "light");
  };

  const handleGoogleSuccess = async (credentialResponse: any) => {
    const credential = credentialResponse?.credential;
    if (!credential) {
      toast.error("No credential received from Google");
      return;
    }

    toast.loading("Authenticating with Google...", { id: "auth" });

    googleLoginMutation.mutate(
      { idToken: credential },
      {
        onSuccess: () => {
          toast.success("Successfully authenticated! Redirecting...", {
            id: "auth",
          });
          setTimeout(() => {
            navigate({ to: "/dashboard" });
          }, 500);
        },
        onError: (error) => {
          const errorMessage =
            error.response?.data?.detail ||
            error.message ||
            "Authentication failed";
          toast.error(errorMessage, {
            id: "auth",
            description:
              "Please try again or contact support if the issue persists.",
          });
        },
      }
    );
  };

  const handleGoogleError = () => {
    toast.error("Google authentication failed", {
      description: "Please try again or use a different account.",
    });
  };

  return (
    <div className="relative min-h-screen overflow-hidden flex items-center justify-center">
      {/* Animated Background */}
      <canvas ref={canvasRef} className="fixed inset-0 -z-10 opacity-20" />

      {/* Floating Icons Background */}
      <div className="absolute inset-0 -z-10 overflow-hidden">
        {[...Array(6)].map((_, i) => (
          <motion.div
            key={i}
            className="absolute opacity-10"
            animate={{
              y: [0, -80, 0],
              x: [0, 40, 0],
              rotate: [0, 180, 360],
            }}
            transition={{
              duration: 20 + i * 3,
              repeat: Infinity,
              ease: "linear",
            }}
            style={{
              left: `${10 + i * 15}%`,
              top: `${20 + (i % 3) * 25}%`,
            }}
          >
            {i % 3 === 0 ? (
              <Shield className="h-10 w-10 text-primary" />
            ) : i % 3 === 1 ? (
              <Mail className="h-10 w-10 text-primary" />
            ) : (
              <Zap className="h-10 w-10 text-primary" />
            )}
          </motion.div>
        ))}
      </div>

      {/* Navigation */}
      <motion.nav
        className="fixed top-0 left-0 right-0 z-50 px-6 py-4"
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
      >
        <div className="mx-auto flex max-w-7xl items-center justify-between">
          <Button
            variant="ghost"
            onClick={() => navigate({ to: "/landing" })}
            className="flex items-center gap-2"
          >
            <ArrowLeft className="h-4 w-4" />
            Back to Home
          </Button>

          <Button
            variant="ghost"
            size="icon"
            onClick={toggleTheme}
            className="h-9 w-9"
          >
            <Sun className="h-4 w-4 rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0" />
            <Moon className="absolute h-4 w-4 rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100" />
          </Button>
        </div>
      </motion.nav>

      {/* Auth Card */}
      <motion.div
        className="relative z-10 w-full max-w-md px-6"
        variants={fadeInUp}
        initial="initial"
        animate="animate"
      >
        <Card className="relative overflow-hidden border-border/50 bg-card/95 backdrop-blur-sm">
          <CardHeader className="space-y-3 text-center pb-6">
            <motion.div
              className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-primary/10"
              whileHover={{ scale: 1.1, rotate: 360 }}
              transition={{ duration: 0.3 }}
            >
              <Mail className="h-8 w-8 text-primary" />
            </motion.div>
            <CardTitle className="text-3xl font-bold tracking-tight">
              Welcome to LABEL
            </CardTitle>
            <CardDescription className="text-base">
              Sign in to revolutionize your inbox
            </CardDescription>
          </CardHeader>

          <CardContent className="space-y-6">
            {/* Loading State */}
            {googleLoginMutation.isPending && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="flex items-center justify-center gap-3 rounded-lg border border-primary/20 bg-primary/5 p-4"
              >
                <Loader2 className="h-5 w-5 animate-spin text-primary" />
                <p className="text-sm font-medium text-primary">
                  Authenticating...
                </p>
              </motion.div>
            )}

            {/* Google Login Button */}
            <div className="flex flex-col items-center space-y-4">
              <div className="w-full flex justify-center">
                <GoogleLogin
                  size="large"
                  width="100%"
                  type="standard"
                  theme={theme === "dark" ? "filled_black" : "outline"}
                  logo_alignment="center"
                  shape="rectangular"
                  onSuccess={handleGoogleSuccess}
                  onError={handleGoogleError}
                  ux_mode="popup"
                  disabled={googleLoginMutation.isPending}
                />
              </div>

              {/* Info Text */}
              <p className="text-center text-xs text-muted-foreground">
                By signing in, you agree to our Terms of Service and Privacy
                Policy
              </p>
            </div>

            {/* Features */}
            <div className="pt-4 space-y-3">
              <div className="flex items-start gap-3">
                <div className="rounded-full bg-primary/10 p-1.5 mt-0.5">
                  <Shield className="h-3.5 w-3.5 text-primary" />
                </div>
                <div className="flex-1">
                  <p className="text-sm font-medium">Secure Authentication</p>
                  <p className="text-xs text-muted-foreground">
                    Your data is protected with industry-standard encryption
                  </p>
                </div>
              </div>

              <div className="flex items-start gap-3">
                <div className="rounded-full bg-primary/10 p-1.5 mt-0.5">
                  <Zap className="h-3.5 w-3.5 text-primary" />
                </div>
                <div className="flex-1">
                  <p className="text-sm font-medium">Instant Access</p>
                  <p className="text-xs text-muted-foreground">
                    Start organizing your emails in seconds
                  </p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Bottom Info */}
        <motion.p
          className="mt-6 text-center text-sm text-muted-foreground"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.3 }}
        >
          Need help?{" "}
          <a href="#" className="text-primary hover:underline font-medium">
            Contact Support
          </a>
        </motion.p>
      </motion.div>
    </div>
  );
};

export default Auth;
