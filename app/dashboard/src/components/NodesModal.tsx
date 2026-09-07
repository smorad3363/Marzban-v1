import {
  HStack,
  Modal,
  ModalBody,
  ModalCloseButton,
  ModalContent,
  ModalHeader,
  ModalOverlay,
  Text,
} from "@chakra-ui/react";
import { SquaresPlusIcon } from "@heroicons/react/24/outline";
import { useDashboard } from "contexts/DashboardContext";
import { FC } from "react";
import { DeleteNodeModal } from "./DeleteNodeModal";
import { Icon } from "./Icon";
import { NodesManagementWorkspace } from "./NodesManagementWorkspace";

export const NodesDialog: FC = () => {
  const { isEditingNodes, onEditingNodes } = useDashboard();

  const onClose = () => onEditingNodes(false);

  return (
    <>
      <Modal
        isOpen={isEditingNodes}
        onClose={onClose}
        scrollBehavior="inside"
        size="full"
      >
        <ModalOverlay bg="blackAlpha.400" backdropFilter="blur(10px)" />
        <ModalContent
          mx={{ base: 2, md: 4 }}
          my={{ base: 2, md: 4 }}
          w={{ base: "calc(100% - 16px)", md: "calc(100% - 32px)" }}
          maxW="7xl"
          h={{ base: "calc(100vh - 16px)", md: "calc(100vh - 32px)" }}
          maxH={{ base: "calc(100vh - 16px)", md: "calc(100vh - 32px)" }}
          borderWidth="1px"
          borderColor="var(--panel-border)"
          borderRadius={{ base: "12px", md: "16px" }}
          bg="var(--panel-surface)"
          overflow="hidden"
        >
          <ModalHeader
            px={{ base: 4, md: 5 }}
            py={4}
            borderBottomWidth="1px"
            borderColor="var(--panel-border)"
          >
            <HStack spacing={3}>
              <Icon color="primary">
                <SquaresPlusIcon width="20px" />
              </Icon>
              <Text fontSize="lg" fontWeight="900">
                مدیریت گره‌ها
              </Text>
            </HStack>
          </ModalHeader>
          <ModalCloseButton mt={2} />
          <ModalBody px={{ base: 3, md: 4 }} py={4}>
            <NodesManagementWorkspace />
          </ModalBody>
        </ModalContent>
      </Modal>
      <DeleteNodeModal />
    </>
  );
};
