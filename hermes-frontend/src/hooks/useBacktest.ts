import { useMutation } from "@tanstack/react-query";
import { api } from "../services/api";
import type { BacktestRequest } from "../types";

export const useBacktest = () => {
  return useMutation({
    mutationFn: (req: BacktestRequest) => api.runBacktest(req),
  });
};
