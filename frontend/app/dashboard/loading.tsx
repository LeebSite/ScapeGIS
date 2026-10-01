import LoadingScreen from "@/components/ui/loading-screen";

export default function DashboardLoading() {
  return (
    <LoadingScreen
      fullScreen={false}
      message="Memuat Dashboard & Data Spatial ScapeGIS..."
      subtext="Menyiapkan statistik workspace, proyek, dan peta geospasial Anda."
    />
  );
}