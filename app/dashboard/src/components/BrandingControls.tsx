import { HStack, IconButton, Input, Text, Tooltip, useToast } from "@chakra-ui/react";
import { ArrowUpTrayIcon, TrashIcon } from "@heroicons/react/24/outline";
import { ChangeEvent, FC, useRef } from "react";
import { useMutation, useQueryClient } from "react-query";
import { fetch } from "service/http";
import { BrandingResponse } from "types/Admin";
import { CurrentAdminQueryKey } from "hooks/useGetUser";
import { localizedApiError } from "utils/apiError";

type Props = { hasLogo: boolean };

export const BrandingControls: FC<Props> = ({ hasLogo }) => {
  const fileRef = useRef<HTMLInputElement>(null);
  const toast = useToast();
  const queryClient = useQueryClient();
  const refresh = (data: BrandingResponse) => {
    queryClient.setQueryData(CurrentAdminQueryKey, (current: any) => ({ ...current, ...data }));
  };
  const logoMutation = useMutation(
    (body: FormData) => fetch<BrandingResponse>("/branding/logo", { method: "POST", body }),
    { onSuccess: refresh, onError: (error) => { toast({ title: "لوگو ذخیره نشد", description: localizedApiError(error), status: "error" }); } }
  );
  const removeMutation = useMutation(
    () => fetch<BrandingResponse>("/branding/logo", { method: "DELETE" }),
    { onSuccess: refresh, onError: (error) => { toast({ title: "لوگو حذف نشد", description: localizedApiError(error), status: "error" }); } }
  );
  const upload = (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;
    const body = new FormData();
    body.append("logo", file);
    logoMutation.mutate(body);
    event.target.value = "";
  };

  return (
    <HStack px={2} spacing={1.5} justify="flex-start">
      <Text fontSize="xs" color="var(--panel-text-muted)">لوگو</Text>
      <Input ref={fileRef} display="none" type="file" accept="image/png,image/jpeg,image/webp" onChange={upload} />
      <Tooltip label="انتخاب لوگو (PNG، JPG یا WebP)">
        <IconButton color="var(--panel-text-body)" aria-label="انتخاب لوگو" size="xs" variant="ghost" isLoading={logoMutation.isLoading} icon={<ArrowUpTrayIcon width={15} />} onClick={() => fileRef.current?.click()} />
      </Tooltip>
      {hasLogo && <Tooltip label="بازگشت به لوگوی پیش‌فرض"><IconButton aria-label="حذف لوگوی سفارشی" size="xs" variant="ghost" colorScheme="red" isLoading={removeMutation.isLoading} icon={<TrashIcon width={15} />} onClick={() => removeMutation.mutate()} /></Tooltip>}
    </HStack>
  );
};
