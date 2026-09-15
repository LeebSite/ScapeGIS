export type MapStatus = "active" | "locked" | "requested";

export interface MapRecord {
  id: string;
  title: string;
  region?: string;
  status: MapStatus;
  owner?: string;
}

const MAPS: MapRecord[] = [
  { id: "pekanbaru", title: "Pekanbaru Demo", region: "Pekanbaru", status: "active", owner: "demo" },
  { id: "locked-1", title: "Locked Map", status: "locked" },
  { id: "requested-1", title: "Requested Map", status: "requested" },
];

export function getMapById(id: string): MapRecord | undefined {
  return MAPS.find((m) => m.id === id);
}

export function isMapActive(id: string) {
  const m = getMapById(id);
  return !!m && m.status === "active";
}

export function listMaps() {
  return MAPS;
}
