"use client";

import { FormEvent, useEffect, useState } from "react";
import { LogoutButton } from "@/components/logout-button";
import { apiFetch } from "@/lib/api";
import { Playlist, User } from "@/types";

type PlatformPlaylist = { id: string; name: string; url: string };

export default function DashboardPage() {
  const [user, setUser] = useState<User | null>(null);
  const [playlists, setPlaylists] = useState<Playlist[]>([]);
  const [spotifyPlaylists, setSpotifyPlaylists] = useState<PlatformPlaylist[]>([]);
  const [youtubePlaylists, setYoutubePlaylists] = useState<PlatformPlaylist[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const [form, setForm] = useState({
    platform: "spotify",
    platform_playlist_id: "",
    name: "",
    playlist_url: "",
    is_public_monitor: false
  });

  const load = async () => {
    setLoading(true);
    try {
      const [me, ownPlaylists] = await Promise.all([apiFetch<User>("/api/auth/me"), apiFetch<Playlist[]>("/api/playlists")]);
      setUser(me);
      setPlaylists(ownPlaylists);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load dashboard");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void load();
  }, []);

  const loadPlatformPlaylists = async (platform: "spotify" | "youtube") => {
    try {
      if (platform === "spotify") {
        const rows = await apiFetch<PlatformPlaylist[]>("/api/platforms/spotify/playlists");
        setSpotifyPlaylists(rows);
      } else {
        const rows = await apiFetch<PlatformPlaylist[]>("/api/platforms/youtube/playlists");
        setYoutubePlaylists(rows);
      }
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to fetch platform playlists");
    }
  };

  const addPlaylist = async (event: FormEvent) => {
    event.preventDefault();
    try {
      await apiFetch<Playlist>("/api/playlists", { method: "POST", body: JSON.stringify(form) });
      setForm({
        platform: "spotify",
        platform_playlist_id: "",
        name: "",
        playlist_url: "",
        is_public_monitor: false
      });
      await load();
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to add playlist");
    }
  };

  const removePlaylist = async (id: string) => {
    await apiFetch(`/api/playlists/${id}`, { method: "DELETE" });
    await load();
  };

  if (loading) {
    return <main className="mx-auto max-w-5xl p-8">Loading...</main>;
  }

  if (error && !user) {
    return (
      <main className="mx-auto max-w-5xl p-8">
        <div className="rounded border border-red-200 bg-red-50 p-4 text-red-800">
          {error}. Please sign in from the home page.
        </div>
      </main>
    );
  }

  return (
    <main className="mx-auto max-w-5xl p-8">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Dashboard</h1>
          <p className="text-slate-600">
            {user?.email} - Tier: <span className="font-semibold uppercase">{user?.subscription_tier}</span>
          </p>
        </div>
        <LogoutButton />
      </div>

      {error ? <div className="mb-4 rounded bg-red-50 p-3 text-sm text-red-700">{error}</div> : null}

      <div className="grid gap-6 md:grid-cols-2">
        <section className="rounded bg-white p-5 shadow-sm">
          <h2 className="text-lg font-semibold">Add Monitored Playlist</h2>
          <form onSubmit={addPlaylist} className="mt-4 space-y-3">
            <select
              value={form.platform}
              onChange={(e) => setForm((f) => ({ ...f, platform: e.target.value }))}
              className="w-full rounded border px-3 py-2"
            >
              <option value="spotify">Spotify</option>
              <option value="youtube">YouTube</option>
            </select>
            <input
              placeholder="Platform playlist ID"
              value={form.platform_playlist_id}
              onChange={(e) => setForm((f) => ({ ...f, platform_playlist_id: e.target.value }))}
              className="w-full rounded border px-3 py-2"
              required
            />
            <input
              placeholder="Playlist name"
              value={form.name}
              onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
              className="w-full rounded border px-3 py-2"
              required
            />
            <input
              placeholder="Playlist URL"
              value={form.playlist_url}
              onChange={(e) => setForm((f) => ({ ...f, playlist_url: e.target.value }))}
              className="w-full rounded border px-3 py-2"
              required
            />
            <label className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={form.is_public_monitor}
                onChange={(e) => setForm((f) => ({ ...f, is_public_monitor: e.target.checked }))}
              />
              Public URL monitor (paid only)
            </label>
            <button className="rounded bg-slate-900 px-4 py-2 text-white hover:bg-slate-800" type="submit">
              Save playlist
            </button>
          </form>
        </section>

        <section className="rounded bg-white p-5 shadow-sm">
          <h2 className="text-lg font-semibold">Platform Discovery</h2>
          <div className="mt-3 flex gap-2">
            <button
              className="rounded border px-3 py-2 text-sm hover:bg-slate-50"
              onClick={() => void loadPlatformPlaylists("spotify")}
              type="button"
            >
              Load Spotify playlists
            </button>
            <button
              className="rounded border px-3 py-2 text-sm hover:bg-slate-50"
              onClick={() => void loadPlatformPlaylists("youtube")}
              type="button"
            >
              Load YouTube playlists
            </button>
          </div>
          <div className="mt-3 text-sm">
            <p className="font-medium">Spotify</p>
            <ul className="list-disc pl-5">
              {spotifyPlaylists.map((p) => (
                <li key={p.id}>
                  {p.name} ({p.id})
                </li>
              ))}
            </ul>
            <p className="mt-3 font-medium">YouTube</p>
            <ul className="list-disc pl-5">
              {youtubePlaylists.map((p) => (
                <li key={p.id}>
                  {p.name} ({p.id})
                </li>
              ))}
            </ul>
          </div>
        </section>
      </div>

      <section className="mt-6 rounded bg-white p-5 shadow-sm">
        <h2 className="text-lg font-semibold">Your monitored playlists</h2>
        <div className="mt-4 space-y-3">
          {playlists.length === 0 ? <p className="text-slate-600">No playlists added yet.</p> : null}
          {playlists.map((playlist) => (
            <div key={playlist.id} className="flex items-center justify-between rounded border p-3">
              <div>
                <p className="font-medium">{playlist.name}</p>
                <p className="text-sm text-slate-600">
                  {playlist.platform} - {playlist.platform_playlist_id}
                </p>
              </div>
              <button
                onClick={() => void removePlaylist(playlist.id)}
                type="button"
                className="rounded bg-red-600 px-3 py-2 text-sm text-white hover:bg-red-500"
              >
                Delete
              </button>
            </div>
          ))}
        </div>
      </section>
    </main>
  );
}
