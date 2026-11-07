import "react-datepicker/dist/react-datepicker.css";
import "react-loading-skeleton/dist/skeleton.css";
import { RouterProvider } from "react-router-dom";
import { Center, Skeleton, Stack } from "@chakra-ui/react";
import { Suspense } from "react";
import { router } from "./pages/Router";

function App() {
    return <Suspense fallback={<Center minH="100dvh" p={5} role="status" aria-label="در حال آماده‌سازی صفحه"><Stack w="full" maxW="1100px" spacing={5}><Skeleton h="60px" /><Skeleton h="150px" /><Skeleton h="320px" /></Stack></Center>}><RouterProvider router={router} /></Suspense>;
}

export default App;
