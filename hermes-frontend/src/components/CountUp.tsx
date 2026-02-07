import { useEffect } from "react";
import { motion, useSpring, useTransform } from "framer-motion";

export const CountUp = ({ value }: { value: string }) => {
  // Simple heuristic parsing
  const isPercent = value.includes("%");
  const numericValue = parseFloat(value.replace(/[^0-9.-]/g, ""));
  const suffix = isPercent ? "%" : "";

  const spring = useSpring(0, { bounce: 0, duration: 1000 });
  const displayValue = useTransform(
    spring,
    (current) => current.toFixed(2) + suffix,
  );

  useEffect(() => {
    spring.set(numericValue);
  }, [numericValue, spring]);

  return (
    <motion.p className="text-2xl font-bold mt-1 text-white">
      {isNaN(numericValue) ? value : displayValue}
    </motion.p>
  );
};
