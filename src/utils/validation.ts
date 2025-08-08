import type { Asset } from "~/types/portfolio";

export const validateSymbol = (value: string, assets: Asset[]): string | undefined => {
  if (!value.trim()) return "Symbol is required";
  if (value.length > 10) return "Symbol must be 10 characters or less";
  if (assets.some((asset) => asset.symbol.toUpperCase() === value.toUpperCase())) {
    return "Asset already exists in portfolio";
  }
  return undefined;
};

export const validateName = (value: string): string | undefined => {
  if (!value.trim()) return "Name is required";
  if (value.length > 100) return "Name must be 100 characters or less";
  return undefined;
};

export const validateExpectedReturn = (value: string): string | undefined => {
  const expectedReturn = parseFloat(value);
  if (!value.trim() || Number.isNaN(expectedReturn)) return "Expected return is required and must be a number";
  if (expectedReturn < -100 || expectedReturn > 1000) return "Expected return must be between -100% and 1000%";
  return undefined;
};

export const validateVolatility = (value: string): string | undefined => {
  const volatility = parseFloat(value);
  if (!value.trim() || Number.isNaN(volatility)) return "Volatility is required and must be a number";
  if (volatility < 0 || volatility > 1000) return "Volatility must be between 0% and 1000%";
  return undefined;
};

export const validateAllocation = (value: string): string | undefined => {
  const allocation = parseFloat(value);
  if (!value.trim() || Number.isNaN(allocation)) return "Allocation is required and must be a number";
  if (allocation < 0 || allocation > 100) return "Allocation must be between 0% and 100%";
  return undefined;
};
