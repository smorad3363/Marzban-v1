import {
  Alert,
  AlertDescription,
  AlertIcon,
  Badge,
  Box,
  Button,
  Flex,
  FormControl,
  Grid,
  HStack,
  IconButton,
  useColorMode,
  SimpleGrid,
  Text,
  VStack,
} from "@chakra-ui/react";
import { ArrowRightOnRectangleIcon, ServerStackIcon, ShieldCheckIcon, MoonIcon, SunIcon, AdjustmentsHorizontalIcon } from "@heroicons/react/24/outline";
import { zodResolver } from "@hookform/resolvers/zod";
import { BrandMark } from "components/BrandMark";
import { resetDashboardState } from "contexts/DashboardContext";
import { Footer } from "components/Footer";
import { Input } from "components/Input";
import { FC, useEffect, useState } from "react";
import { FieldValues, useForm } from "react-hook-form";
import { useTranslation } from "react-i18next";
import { useLocation, useNavigate } from "react-router-dom";
import { fetch } from "service/http";
import { removeAuthToken, setAuthToken } from "utils/authStorage";
import { localizedApiError } from "utils/apiError";
import { useBranding } from "hooks/useBranding";
import { z } from "zod";

const schema = z.object({
  username: z.string().min(1, "login.fieldRequired"),
  password: z.string().min(1, "login.fieldRequired"),
});

export const Login: FC = () => {
  const { branding } = useBranding();
  const { colorMode, toggleColorMode } = useColorMode();
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const { t } = useTranslation();
  const location = useLocation();
  const { register, formState: { errors }, handleSubmit } = useForm({ resolver: zodResolver(schema) });

  useEffect(() => {
    removeAuthToken();
    resetDashboardState();
    if (location.pathname !== "/login") navigate("/login", { replace: true });
  }, []);

  const login = (values: FieldValues) => {
    setError("");
    const formData = new FormData();
    formData.append("username", values.username);
    formData.append("password", values.password);
    formData.append("grant_type", "password");
    setLoading(true);
    fetch("/admin/token", { method: "post", body: formData })
      .then(({ access_token: token }) => {
        if (typeof token !== "string" || !token) {
          throw new Error("Login response did not contain an access token");
        }
        setAuthToken(token);
        resetDashboardState();
        navigate("/");
      })
      .catch((err) => setError(localizedApiError(err)))
      .finally(setLoading.bind(null, false));
  };

  return (
    <Grid className="console-login" templateColumns={{ base: "1fr", lg: "1fr 1fr" }} gap={{ base: 0, lg: 6 }} p={{ base: 0, lg: 5 }}>
      <Flex direction="column" minH="calc(100dvh - 40px)" minW={0} px={{ base: 6, md: 12 }} pt="max(24px, env(safe-area-inset-top))" pb="max(20px, env(safe-area-inset-bottom))">
        <HStack justify="space-between" w="full" gap={4}>
          <HStack spacing={3} minW={0}>
            {branding.logo_url ? <Box as="img" src={branding.logo_url} alt={`${branding.panel_name} logo`} boxSize="40px" objectFit="contain" /> : <Box className="console-brand-symbol"><BrandMark aria-hidden="true" boxSize="25px" /></Box>}
            <Box minW={0}><Text fontSize="sm" fontWeight="700" noOfLines={2}>{branding.panel_name}</Text><Text fontSize="xs" color="var(--panel-text-muted)" letterSpacing=".08em">MANAGEMENT CONSOLE</Text></Box>
          </HStack>
          <IconButton variant="outline" size="sm" flexShrink={0} aria-label={colorMode === "dark" ? "تم روشن" : "تم تیره"} onClick={toggleColorMode} icon={colorMode === "dark" ? <SunIcon width="18" /> : <MoonIcon width="18" />} />
        </HStack>
        <Flex flex="1" align="center" justify="center" py={{ base: 10, lg: 14 }}>
          <Box w="full" maxW="400px">
            <HStack spacing={2} color="var(--panel-accent)" fontSize="xs" mb={4}><ShieldCheckIcon width="17" aria-hidden="true" /><Text>ورود به فضای مدیریت</Text></HStack>
            <VStack align="start" w="full" spacing={3}>
              <Text as="h1" fontSize={{ base: "30px", md: "36px" }} lineHeight="1.5" letterSpacing="-.025em" fontWeight="700">{branding.login_title}</Text>
              <Text color="var(--panel-text-muted)" fontSize="sm" lineHeight="1.9">{branding.description || t("login.welcomeBack")}</Text>
            </VStack>
            <Box w="full" pt={8}>
              <form onSubmit={handleSubmit(login)}>
                <VStack spacing={5}>
                  <FormControl><Input w="full" label={t("username")} placeholder={t("username")} autoComplete="username" {...register("username")} error={t(errors?.username?.message as string)} /></FormControl>
                  <FormControl><Input w="full" label={t("password")} type="password" placeholder={t("password")} autoComplete="current-password" {...register("password")} error={t(errors?.password?.message as string)} /></FormControl>
                  {error && <Alert status="error" rounded="md"><AlertIcon /><AlertDescription>{error}</AlertDescription></Alert>}
                  <Button isLoading={loading} type="submit" w="full" colorScheme="primary" mt={1} minH="48px" rightIcon={<ArrowRightOnRectangleIcon width="18px" aria-hidden="true" />}>{t("login")}</Button>
                </VStack>
              </form>
              <Text mt={6} textAlign="center" fontSize="xs" color="var(--panel-text-muted)" lineHeight="1.9">دسترسی به بخش‌های پنل مطابق مجوزهای حساب شماست.</Text>
            </Box>
          </Box>
        </Flex>
        <Footer />
      </Flex>
      <Flex className="console-login-story" display={{ base: "none", lg: "flex" }} direction="column" justify="space-between" p={{ lg: 8, xl: 12 }} overflow="hidden">
        <HStack color="var(--panel-text-muted)" fontSize="xs" justify="space-between"><Text letterSpacing=".15em" fontSize="xs">MARZBAN / WORKSPACE</Text><ShieldCheckIcon width="20" aria-hidden="true" /></HStack>
        <Box py={12} maxW="520px" mx="auto" w="full">
          <Box className="console-login-diagram" mb={10} aria-hidden="true">
            <HStack justify="space-between" pb={4} borderBottom="1px solid var(--panel-border)"><HStack spacing={2}><Box w="7px" h="7px" bg="var(--panel-accent)" borderRadius="full" /><Text fontSize="xs" fontWeight="600">یک فضای کاری، یک نگاه دقیق</Text></HStack><Box w="30px" h="5px" bg="var(--panel-border-strong)" borderRadius="full" /></HStack>
            <SimpleGrid columns={3} spacing={3} mt={5}>{[UsersSymbol, ServerStackIcon, AdjustmentsHorizontalIcon].map((Icon, i) => <Box key={i} p={4} borderRadius="12px" border="1px solid var(--panel-border)" bg="var(--panel-surface)"><Icon width="22" color="var(--panel-accent)" /><Box mt={4} h="6px" w="65%" bg="var(--panel-border-strong)" borderRadius="full" /><Box mt={2} h="5px" w="40%" bg="var(--panel-border)" borderRadius="full" /></Box>)}</SimpleGrid>
            <Box mt={5} h="100px" borderRadius="12px" bg="var(--panel-accent-soft)" p={4}><svg viewBox="0 0 400 70" width="100%" height="100%" preserveAspectRatio="none" fill="none"><path d="M0 60 C35 62 32 32 70 42 S110 66 145 30 S185 40 220 16 S280 45 310 20 S365 23 400 5" stroke="var(--panel-accent)" strokeWidth="2" vectorEffect="non-scaling-stroke" /></svg></Box>
          </Box>
          <Text as="h2" fontSize={{ lg: "32px", xl: "40px" }} fontWeight="600" lineHeight="1.7" letterSpacing="-.03em">مدیریت منظم.<br /><Text as="span" color="var(--panel-accent)">تصمیم‌های روشن.</Text></Text>
          <Text mt={4} fontSize="sm" color="var(--panel-text-muted)" lineHeight="2" maxW="44ch">کاربران، دسترسی‌ها و حسابداری، در یک محیط یکپارچه و همیشه در دسترس.</Text>
        </Box>
        <HStack color="var(--panel-text-muted)" fontSize="xs" spacing={6}><HStack spacing={2}><ShieldCheckIcon width="16" aria-hidden="true" /><Text>دسترسی کنترل‌شده</Text></HStack><HStack spacing={2}><ServerStackIcon width="16" aria-hidden="true" /><Text>مدیریت یکپارچه</Text></HStack></HStack>
      </Flex>
    </Grid>
  );
};
const UsersSymbol = ShieldCheckIcon;
export default Login;
