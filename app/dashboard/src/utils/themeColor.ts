import { ColorMode } from "@chakra-ui/react";

export const updateThemeColor = (colorMode: ColorMode) => {
  const el = document.querySelector('meta[name="theme-color"]');
  el?.setAttribute("content", colorMode === "dark" ? "#0B0F19" : "#F8FAFC");
};
