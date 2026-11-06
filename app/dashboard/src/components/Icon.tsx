import { Box } from "@chakra-ui/react";
import { FC, PropsWithChildren } from "react";
export type IconType = { color: string };
export const Icon: FC<PropsWithChildren<IconType>> = ({ children }) => <Box display="grid" placeItems="center" boxSize="36px" flexShrink={0} bg="var(--panel-accent-soft)" color="var(--panel-accent)" border="1px solid var(--panel-accent-border)" borderRadius="10px" sx={{ "& svg": { color: "inherit" } }}>{children}</Box>;
