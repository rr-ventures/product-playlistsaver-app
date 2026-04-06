export interface User {
  id: string;
  email: string;
  display_name: string | null;
  avatar_url: string | null;
}

export interface Playlist {
  id: string;
  platform: "spotify" | "youtube";
  platform_playlist_id: string;
  name: string;
  playlist_url: string;
  is_public_monitor: boolean;
  is_active: boolean;
  last_checked_at: string | null;
}
