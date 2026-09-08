import { CreateToastFnReturn } from "@chakra-ui/react";
import { UseFormReturn } from "react-hook-form";
import { localizedApiError } from "./apiError";

export const generateErrorMessage = (
  e: any,
  toast: CreateToastFnReturn,
  form?: UseFormReturn<any>
) => {
  const payload = e?.response?.data ?? e?.response?._data ?? e?.data;
  const detail = payload?.detail;
  if (form && detail && typeof detail === "object" && detail.fields) {
    Object.keys(detail.fields).forEach((field) =>
      form.setError(field, { message: localizedApiError(e, field) })
    );
    return;
  }
  return toast({
    title: localizedApiError(e),
    status: "error",
    isClosable: true,
    position: "top",
    duration: 7000,
  });
};

export const generateSuccessMessage = (
  message: string,
  toast: CreateToastFnReturn
) => {
  return toast({
    title: message,
    status: "success",
    isClosable: true,
    position: "top",
    duration: 3000,
  });
};
