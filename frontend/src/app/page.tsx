import Link from "next/link";
import { API_URL } from "@/lib/api";

export default function HomePage() {
  return (
    <main className="mx-auto max-w-4xl p-8">
      <div className="rounded-xl bg-white p-8 shadow-sm">
        <h1 className="text-3xl font-bold">Playlist Saver</h1>
        <p className="mt-3 text-slate-600">
          Monitor Spotify and YouTube playlists, detect removed tracks, and get email alerts.
        </p>

        <div className="mt-8 flex flex-wrap gap-3">
          <a
            href={`${API_URL}/api/auth/spotify/login`}
            className="rounded bg-green-600 px-4 py-2 font-medium text-white hover:bg-green-500"
          >
            Continue with Spotify
          </a>
          <a
            href={`${API_URL}/api/auth/google/login`}
            className="rounded bg-blue-600 px-4 py-2 font-medium text-white hover:bg-blue-500"
          >
            Continue with Google
          </a>
          <Link href="/dashboard" className="rounded border border-slate-300 px-4 py-2 font-medium hover:bg-slate-50">
            Open Dashboard
          </Link>
        </div>

        <div className="mt-10 rounded border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
          Payments are intentionally disabled in this build; auth and playlist monitoring are fully available.
        </div>
      </div>
    </main>
  );
}
