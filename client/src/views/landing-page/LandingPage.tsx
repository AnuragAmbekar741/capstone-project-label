import { motion } from "framer-motion";
import {
  ArrowRight,
  Check,
  Mail,
  Shield,
  Tag,
  Zap,
  Moon,
  Sun,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { useTheme } from "@/hooks/usetheme";
import { useNavigate } from "@tanstack/react-router";
import { useAnimatedBackground } from "@/hooks/useAnimatedBackground";

const fadeInUp = {
  initial: { opacity: 0, y: 60 },
  animate: { opacity: 1, y: 0 },
  transition: { duration: 0.6, ease: "easeOut" },
};

const stagger = {
  animate: {
    transition: {
      staggerChildren: 0.1,
    },
  },
};

export function LandingPage() {
  const { theme, setTheme } = useTheme();
  const navigate = useNavigate();
  const canvasRef = useAnimatedBackground();

  const toggleTheme = () => {
    setTheme(theme === "light" ? "dark" : "light");
  };

  return (
    <div className="relative min-h-screen overflow-hidden">
      {/* Animated Background */}
      <canvas ref={canvasRef} className="fixed inset-0 -z-10 opacity-20" />

      {/* Navigation */}
      <motion.nav
        className="relative z-50 px-6 py-4"
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
      >
        <div className="mx-auto flex max-w-7xl items-center justify-between">
          <motion.div
            className="flex items-center space-x-2"
            whileHover={{ scale: 1.05 }}
          >
            <Mail className="h-6 w-6 text-primary" />
            <span className="text-2xl font-bold tracking-tight">LABEL</span>
          </motion.div>

          <div className="flex items-center space-x-4">
            <Button
              variant="ghost"
              size="icon"
              onClick={toggleTheme}
              className="h-9 w-9"
            >
              <Sun className="h-4 w-4 rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0" />
              <Moon className="absolute h-4 w-4 rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100" />
            </Button>
            <Button
              variant="ghost"
              onClick={() => navigate({ to: "/auth" })}
              className="text-md font-medium"
            >
              Login
            </Button>
            <Button
              onClick={() => navigate({ to: "/auth" })}
              className="bg-primary text-primary-foreground hover:bg-primary/90"
            >
              Get Started
            </Button>
          </div>
        </div>
      </motion.nav>

      {/* Hero Section */}
      <section className="relative px-6 py-20 text-center">
        <motion.div
          className="mx-auto max-w-4xl"
          variants={stagger}
          initial="initial"
          animate="animate"
        >
          <motion.div variants={fadeInUp} className="mb-6">
            <span className="inline-flex items-center rounded-full bg-primary/10 px-4 py-2 text-sm font-medium text-primary">
              <Zap className="mr-2 h-4 w-4" />
              Email on Steroids
            </span>
          </motion.div>

          <motion.h1
            variants={fadeInUp}
            className="mb-6 text-5xl font-bold tracking-tight sm:text-7xl lg:text-8xl"
          >
            <span className="bg-gradient-to-r from-foreground via-foreground to-muted-foreground bg-clip-text text-transparent">
              Revolutionize Your Inbox
            </span>
          </motion.h1>

          <motion.p
            variants={fadeInUp}
            className="mx-auto mb-10 max-w-2xl text-xl text-muted-foreground leading-relaxed"
          >
            Transform chaos into clarity. Label, organize, and supercharge your
            email workflow with intelligent tagging and AI-powered organization.
          </motion.p>

          <motion.div
            variants={fadeInUp}
            className="flex flex-col sm:flex-row gap-4 justify-center items-center"
          >
            <Button
              size="lg"
              onClick={() => navigate({ to: "/auth" })}
              className="bg-primary text-primary-foreground hover:bg-primary/90 px-8 py-6 text-lg font-medium"
            >
              Start Organizing
              <ArrowRight className="ml-2 h-5 w-5" />
            </Button>
            <Button variant="outline" size="lg" className="px-8 py-6 text-lg">
              Watch Demo
            </Button>
          </motion.div>
        </motion.div>

        {/* Floating Icons */}
        <div className="absolute inset-0 -z-10 overflow-hidden">
          {[...Array(8)].map((_, i) => (
            <motion.div
              key={i}
              className="absolute opacity-20"
              animate={{
                y: [0, -100, 0],
                x: [0, 50, 0],
                rotate: [0, 180, 360],
              }}
              transition={{
                duration: 20 + i * 2,
                repeat: Infinity,
                ease: "linear",
              }}
              style={{
                left: `${5 + i * 12}%`,
                top: `${15 + (i % 3) * 20}%`,
              }}
            >
              {i % 3 === 0 ? (
                <Tag className="h-8 w-8 text-primary" />
              ) : i % 3 === 1 ? (
                <Mail className="h-8 w-8 text-primary" />
              ) : (
                <Zap className="h-8 w-8 text-primary" />
              )}
            </motion.div>
          ))}
        </div>
      </section>

      {/* Features Section */}
      <section className="px-6 py-20">
        <motion.div
          className="mx-auto max-w-7xl"
          variants={stagger}
          initial="initial"
          whileInView="animate"
          viewport={{ once: true }}
        >
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {[
              {
                icon: Tag,
                title: "Smart Labeling",
                description:
                  "AI-powered automatic tagging that learns your preferences and organizes emails intelligently.",
              },
              {
                icon: Zap,
                title: "Lightning Fast",
                description:
                  "Process thousands of emails in seconds with our optimized algorithms and intuitive interface.",
              },
              {
                icon: Shield,
                title: "Secure & Private",
                description:
                  "End-to-end encryption ensures your emails remain private while being perfectly organized.",
              },
            ].map((feature, index) => (
              <motion.div key={index} variants={fadeInUp}>
                <Card className="relative overflow-hidden border-border/50 bg-card/50 backdrop-blur-sm hover:bg-card/80 transition-all duration-300 h-full">
                  <CardContent className="p-8">
                    <motion.div
                      whileHover={{ scale: 1.1, rotate: 360 }}
                      transition={{ duration: 0.3 }}
                      className="inline-flex h-12 w-12 items-center justify-center rounded-lg bg-primary/10 mb-6"
                    >
                      <feature.icon className="h-6 w-6 text-primary" />
                    </motion.div>
                    <h3 className="text-xl font-semibold mb-3">
                      {feature.title}
                    </h3>
                    <p className="text-muted-foreground leading-relaxed">
                      {feature.description}
                    </p>
                  </CardContent>
                </Card>
              </motion.div>
            ))}
          </div>
        </motion.div>
      </section>

      {/* CTA Section */}
      <section className="px-6 py-20">
        <motion.div
          className="mx-auto max-w-4xl text-center"
          variants={fadeInUp}
          initial="initial"
          whileInView="animate"
          viewport={{ once: true }}
        >
          <Card className="relative overflow-hidden border-border/50 bg-gradient-to-br from-primary/5 to-primary/10">
            <CardContent className="p-12">
              <h2 className="text-4xl font-bold tracking-tight mb-4">
                Ready to transform your inbox?
              </h2>
              <p className="text-xl text-muted-foreground mb-8 max-w-2xl mx-auto">
                Join thousands of users who have revolutionized their email
                experience
              </p>
              <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
                <Button
                  size="lg"
                  onClick={() => navigate({ to: "/auth" })}
                  className="bg-primary text-primary-foreground hover:bg-primary/90 px-8 py-6 text-lg font-medium"
                >
                  Get Started Free
                  <ArrowRight className="ml-2 h-5 w-5" />
                </Button>
                <div className="flex items-center text-sm text-muted-foreground">
                  <Check className="mr-2 h-4 w-4 text-green-500" />
                  No credit card required
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </section>

      {/* Footer */}
      <footer className="border-t border-border/50 px-6 py-12">
        <div className="mx-auto max-w-7xl text-center text-muted-foreground">
          <div className="flex items-center justify-center space-x-2 mb-4">
            <Mail className="h-5 w-5" />
            <span className="text-lg font-semibold">LABEL</span>
          </div>
          <p>© 2024 LABEL. Email on steroids.</p>
        </div>
      </footer>
    </div>
  );
}
