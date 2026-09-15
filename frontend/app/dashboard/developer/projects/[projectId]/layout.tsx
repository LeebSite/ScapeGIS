// This layout will use the parent layout from developer/layout.tsx
// No need for separate layout here to maintain consistency
export default function ProjectLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <>{children}</>;
}

