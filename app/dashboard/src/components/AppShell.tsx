import { Box, Flex } from "@chakra-ui/react";
import useGetUser from "hooks/useGetUser";
import { FC, PropsWithChildren } from "react";
import { CoreSettingsModal } from "./CoreSettingsModal";
import { Footer } from "./Footer";
import { Header } from "./Header";
import { HostsDialog } from "./HostsDialog";
import { NodesDialog } from "./NodesModal";
import { NodesUsage } from "./NodesUsage";

export const AppShell: FC<PropsWithChildren> = ({ children }) => {
  const { userData, getUserIsPending } = useGetUser();
  const isOwner = !getUserIsPending && (userData.is_sudo || userData.role === "OWNER");

  return (
    <>
      <Flex minH="100vh" align="stretch" direction={{ base: "column", lg: "row" }} className="operations-shell">
        <Header />
        <Flex
          as="main"
          minW={0}
          flex="1"
          direction="column"
          id="main-content"
          px={{ base: 4, md: 7, xl: 9 }}
          py={{ base: 5, md: 7 }}
        >
          <Box w="full" maxW="none" minW={0} flex="1">
            {children}
          </Box>
          <Footer mt={8} />
        </Flex>
      </Flex>

      {isOwner && (
        <>
          <HostsDialog />
          <NodesDialog />
          <NodesUsage />
          <CoreSettingsModal />
        </>
      )}
    </>
  );
};
