/// <reference types="next" />
/// <reference types="next/image-types/global" />

declare module 'next-intl/server' {
  export function getMessages(): Promise<Record<string, unknown>>;
  export function getRequestConfig(
    fn: (params: { locale: string }) => Promise<{ messages: Record<string, unknown> }>
  ): any;
}

declare module 'next-intl/middleware' {
  export default function createMiddleware(config: {
    locales: readonly string[];
    defaultLocale: string;
    localePrefix: string;
  }): any;
}

declare module 'next-intl' {
  export function useTranslations(namespace?: string): (key: string) => string;
  export function useLocale(): string;
  export function NextIntlClientProvider(props: {
    messages: Record<string, unknown>;
    children: React.ReactNode;
  }): JSX.Element;
}
