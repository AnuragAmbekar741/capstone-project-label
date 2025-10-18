import { useEffect, useRef } from "react";

export const useAnimatedBackground = () => {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    // Set canvas size
    const resize = () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
    };
    resize();
    window.addEventListener("resize", resize);

    // Grid settings
    const gridSize = 50;
    const squares: Array<{
      x: number;
      y: number;
      opacity: number;
      fadeDirection: number;
    }> = [];

    // Create grid of squares
    for (let x = 0; x < canvas.width; x += gridSize) {
      for (let y = 0; y < canvas.height; y += gridSize) {
        if (Math.random() > 0.7) {
          squares.push({
            x,
            y,
            opacity: Math.random() * 0.3,
            fadeDirection: Math.random() > 0.5 ? 1 : -1,
          });
        }
      }
    }

    // Animation loop
    const animate = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      squares.forEach((square) => {
        // Update opacity
        square.opacity += square.fadeDirection * 0.002;
        if (square.opacity >= 0.3 || square.opacity <= 0) {
          square.fadeDirection *= -1;
        }

        // Draw square
        ctx.strokeStyle = `rgba(120, 120, 120, ${square.opacity})`;
        ctx.lineWidth = 1;
        ctx.strokeRect(square.x, square.y, gridSize, gridSize);
      });

      requestAnimationFrame(animate);
    };

    animate();

    return () => {
      window.removeEventListener("resize", resize);
    };
  }, []);

  return canvasRef;
};
