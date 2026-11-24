/** Shapes of what the backend sends (see websocket_api.py) and the parts of `hass` the panel uses. */

export interface PortInfo {
  index: number;
  label: string;
  is_poe: boolean;
  connected: boolean;
  speed_mbps: number;
  admin_enabled: boolean;
  poe_enabled: boolean | null;
  power_w: number | null;
  tx_kbps: number;
  rx_kbps: number;
  phy_mode: string | null;
  flow_control: boolean | null;
  priority: number | null;
  limit_up_mbps: number | null;
  limit_down_mbps: number | null;
}

export interface DeviceInfo {
  entry_id: string;
  title: string;
  available: boolean;
  model: string | null;
  firmware: string;
  voltage_v: number | null;
  total_power_w: number | null;
  temperature_c: number | null;
  cloud_status: number | null;
  settings: Record<string, number | null>;
  ports: PortInfo[];
  /** Only sent to administrators. */
  host?: string;
}

export type ViewName = "overview" | "device" | "settings";
export type ModeSetting = "auto" | "dark" | "light";

export interface PanelSettings {
  scheme: string;
  mode: ModeSetting;
  language: string; // "auto" or a language code
  device: string; // last selected entry id
}

export interface Hass {
  language: string;
  user?: { is_admin: boolean; name: string };
  themes?: { darkMode?: boolean };
  connection: {
    subscribeMessage<T>(cb: (msg: T) => void, msg: Record<string, unknown>): Promise<() => Promise<void>>;
  };
  callWS<T = unknown>(msg: Record<string, unknown>): Promise<T>;
}

/** What a view hands up when the user changes something. */
export interface WriteRequest {
  action: string;
  index?: number;
  value?: boolean | number | string;
  confirm?: boolean;
}
