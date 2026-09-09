import { Box, Flex } from "@chakra-ui/react";
import useGetUser from "hooks/useGetUser";
import { FC, PropsWithChildren, useEffect } from "react";
import { CoreSettingsModal } from "./CoreSettingsModal";
import { Footer } from "./Footer";
import { Header } from "./Header";
import { HostsDialog } from "./HostsDialog";
import { NodesDialog } from "./NodesModal";

const suppressCredentialAutofill = (element: Element) => {
  if (!(element instanceof HTMLInputElement || element instanceof HTMLTextAreaElement)) return;
  if (element instanceof HTMLInputElement && element.type === "hidden") return;

  const autocomplete = element instanceof HTMLInputElement && element.type === "password" ? "new-password" : "off";
  element.setAttribute("autocomplete", autocomplete);
  element.setAttribute("data-lpignore", "true");
  element.setAttribute("data-1p-ignore", "true");
  element.setAttribute("data-bwignore", "true");
};

const suppressCredentialAutofillIn = (root: ParentNode) => {
  if (root instanceof Element) suppressCredentialAutofill(root);
  root.querySelectorAll("input, textarea").forEach(suppressCredentialAutofill);
};

export const AppShell: FC<PropsWithChildren> = ({ children }) => {
  const { userData, getUserIsPending } = useGetUser();
  const isOwner = !getUserIsPending && (userData.is_sudo || userData.role === "OWNER");

  useEffect(() => {
    suppressCredentialAutofillIn(document);

    const observer = new MutationObserver((mutations) => {
      for (const mutation of mutations) {
        mutation.addedNodes.forEach((node) => {
          if (node instanceof Element) suppressCredentialAutofillIn(node);
        });
      }
    });

    observer.observe(document.body, { childList: true, subtree: true });
    return () => observer.disconnect();
  }, []);

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
          <CoreSettingsModal />
        </>
      )}
    </>
  );
};
