import { Badge, Box, Flex, HStack, Text } from "@chakra-ui/react";
import useGetUser from "hooks/useGetUser";
import { FC, PropsWithChildren, useEffect } from "react";
import { useLocation } from "react-router-dom";
import { CoreSettingsModal } from "./CoreSettingsModal";
import { Footer } from "./Footer";
import { AlertCenter } from "./AlertCenter";
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
  const { pathname } = useLocation();
  const workspace = pathname.startsWith("/users") ? "کاربران" : pathname.startsWith("/admins") ? "ادمین‌ها و حسابداری" : pathname.startsWith("/plans") ? "پلن‌ها و دسترسی" : pathname.startsWith("/settings") ? "پیکربندی" : pathname.startsWith("/audit-logs") ? "تاریخچه فعالیت‌ها" : pathname.startsWith("/device-limits") ? "محدودیت دستگاه" : "نمای کلی";
  useEffect(() => { window.scrollTo({ top: 0, behavior: "auto" }); }, [pathname]);

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
    <AlertCenter>{({ trigger, summary }) => <>
      <a href="#main-content" className="console-skip-link" onClick={(event) => { event.preventDefault(); document.getElementById("main-content")?.focus(); }}>رفتن به محتوای اصلی</a>
      <Flex minH="100dvh" align="stretch" direction={{ base: "column", lg: "row" }} className="operations-shell">
        <Header />
        <Flex
          as="main"
          minW={0}
          flex="1"
          direction="column"
          id="main-content"
          tabIndex={-1}
          px={{ base: 4, md: 7, xl: 9 }}
          pt={{ base: 0, lg: 1 }}
          pb="max(24px, env(safe-area-inset-bottom))"
        >
          <Box w="full" maxW="1680px" mx="auto" minW={0} flex="1">
            <HStack className="console-workspace-bar" position="sticky" top={0} zIndex={20} bg="var(--panel-bg)" justify="space-between" flexWrap="wrap">
              <HStack spacing={2} fontSize="xs" color="var(--panel-text-muted)"><Text display={{ base: "none", sm: "block" }}>فضای مدیریت</Text><Text aria-hidden="true" display={{ base: "none", sm: "block" }} opacity={.5}>/</Text><Text color="var(--panel-text-body)" fontWeight="500">{workspace}</Text></HStack>
              <HStack spacing={2} minW={0} maxW="70%">{trigger}<Text dir="ltr" noOfLines={1} fontSize="xs" color="var(--panel-text-muted)">{userData.username}</Text><Badge bg="var(--panel-accent-soft)" color="var(--panel-accent)" fontSize="xs" flexShrink={0}>{isOwner ? "مالک" : "ادمین"}</Badge></HStack>
            </HStack>
            {summary}
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
    </>}</AlertCenter>
  );
};
