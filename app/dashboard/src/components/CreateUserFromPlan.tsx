import { Alert, AlertIcon, Button, FormControl, FormLabel, Input, Modal, ModalBody, ModalCloseButton, ModalContent, ModalFooter, ModalHeader, ModalOverlay, Select, Stack, Text, useToast } from "@chakra-ui/react";
import { useEffect, useRef, useState } from "react";
import { useMutation, useQuery } from "react-query";
import { useDashboard } from "contexts/DashboardContext";
import { fetch } from "service/http";
import { AccessGroup } from "types/Admin";
import { localizedApiError } from "utils/apiError";
import { queryClient } from "utils/react-query";

type AvailableUserPlan = {
  id: number;
  name: string;
  data_limit: number;
  duration_days: number;
  price_toman: number;
  concurrent_user_limit: number | null;
};

export const CreateUserFromPlan = ({ isOpen, onClose }: { isOpen: boolean; onClose: () => void }) => {
  const [username, setUsername] = useState("");
  const [planId, setPlanId] = useState("");
  const [groupId, setGroupId] = useState("");
  const request = useRef<string | null>(null);
  const toast = useToast();
  const plans = useQuery<AvailableUserPlan[]>("available-user-plans", () => fetch("/available-user-plans"), { enabled: isOpen });
  const groups = useQuery<AccessGroup[]>("access-groups", () => fetch("/access-groups"), { enabled: isOpen });
  useEffect(() => { if (isOpen) { setUsername(""); setPlanId(""); setGroupId(""); request.current = null; } }, [isOpen]);
  const create = useMutation(() => {
    request.current ||= `create-${crypto.randomUUID()}`;
    return fetch("/users/from-plan", { method: "POST", body: { username: username.trim(), plan_id: Number(planId), access_group_id: Number(groupId), status: "active", idempotency_key: request.current } });
  }, {
    onSuccess: () => { useDashboard.getState().refetchUsers(); queryClient.invalidateQueries("account-summary"); toast({ title: "User created", status: "success" }); onClose(); },
    onError: (error) => { toast({ title: "User creation failed", description: localizedApiError(error), status: "error" }); },
  });
  const plan = plans.data?.find((item) => item.id === Number(planId));
  return <Modal isOpen={isOpen} onClose={create.isLoading ? () => undefined : onClose} isCentered><ModalOverlay /><ModalContent mx={3} as="form" onSubmit={(event) => { event.preventDefault(); if (plan && groupId && username.trim() && !create.isLoading) create.mutate(); }}>
    <ModalHeader>Create user from Plan</ModalHeader><ModalCloseButton isDisabled={create.isLoading} />
    <ModalBody><Stack spacing={4}>
      {(plans.isError || groups.isError) && <Alert status="error"><AlertIcon />Options could not load.<Button onClick={() => { plans.refetch(); groups.refetch(); }}>Retry</Button></Alert>}
      <FormControl isRequired><FormLabel>Username</FormLabel><Input dir="ltr" autoComplete="off" value={username} isDisabled={create.isLoading || !!request.current} onChange={(event) => setUsername(event.target.value)} /></FormControl>
      <FormControl isRequired><FormLabel>Plan</FormLabel><Select value={planId} isDisabled={plans.isLoading || create.isLoading || !!request.current} onChange={(event) => setPlanId(event.target.value)}><option value="">{plans.isLoading ? "Loading…" : "Select Plan"}</option>{plans.data?.map((item) => <option key={item.id} value={item.id}>{item.name} · {item.price_toman.toLocaleString()} Toman</option>)}</Select></FormControl>
      {!plans.isLoading && !plans.isError && !plans.data?.length && <Text role="status">No Plans available. Contact the Owner.</Text>}
      <FormControl isRequired><FormLabel>Access Group</FormLabel><Select value={groupId} isDisabled={groups.isLoading || create.isLoading || !!request.current} onChange={(event) => setGroupId(event.target.value)}><option value="">Select network access</option>{groups.data?.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</Select></FormControl>
      {!groups.isLoading && !groups.isError && !groups.data?.length && <Alert status="warning"><AlertIcon />No Access Group is available. Ask the Owner to create one.</Alert>}
      {plan && <Text role="status">{plan.duration_days} days · {plan.data_limit / 1024 ** 3} GiB · Price {plan.price_toman.toLocaleString()} Toman. Charging follows your account policy.</Text>}
    </Stack></ModalBody><ModalFooter gap={2}><Button minH="44px" onClick={onClose} isDisabled={create.isLoading}>Cancel</Button><Button minH="44px" type="submit" colorScheme="primary" isLoading={create.isLoading} isDisabled={!plan || !groupId || !username.trim() || plans.isError || groups.isError || groups.isLoading}>Create user</Button></ModalFooter>
  </ModalContent></Modal>;
};
