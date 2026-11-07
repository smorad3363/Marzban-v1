import { ColorMode } from "@chakra-ui/react";

export const updateThemeColor = (colorMode: ColorMode) => {
  const el = document.querySelector('meta[name="theme-color"]');
  el?.setAttribute("content", colorMode === "dark" ? "#0b100e" : "#f4f6f3");
};
