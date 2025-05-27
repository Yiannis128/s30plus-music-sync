#!/usr/bin/env python3

import argparse
import json
import subprocess
from pathlib import Path
from typing import Dict, Any

from nokia_sync_music.nokia_music import write_playlists

data_file: Path = Path("data.json")
music_dir: Path = Path("Music")


def init() -> None:
    if not data_file.exists():
        with open(data_file, "w") as f:
            json.dump({"playlists": {}}, f, indent=4)
        print("Initialized data.json")
    else:
        print("data.json already exists")


def sync() -> None:
    if not data_file.exists():
        print("data.json does not exist. Please run 'init' first.")
        return

    with open(data_file, "r") as f:
        data: Dict[str, Any] = json.load(f)
        playlists = data.get("playlists", {})

    for name, info in playlists.items():
        url = info.get("url")
        print(f"Syncing playlist: {name} ({url})")
        result = subprocess.run(
            ["yt-dlp", "--flat-playlist", "-J", "--ignore-errors", url],
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            print(
                f"Warning: yt-dlp exited with code {result.returncode} for {name}\n{result.stderr}"
            )

        try:
            playlist_data = json.loads(result.stdout)
            entries = playlist_data.get("entries", [])
            info["entries"] = [entry for entry in entries if entry]
        except json.JSONDecodeError:
            print(f"Failed to parse yt-dlp output for {name}.")

    with open(data_file, "w") as f:
        json.dump({"playlists": playlists}, f, indent=4)


def add_playlist(url: str) -> None:
    playlists_data: Dict[str, Any] = {"playlists": {}}
    if data_file.exists():
        with open(data_file, "r") as f:
            playlists_data = json.load(f)

    existing_playlists = playlists_data.get("playlists", {})

    result = subprocess.run(
        ["yt-dlp", "-J", "--ignore-errors", url], capture_output=True, text=True
    )

    if result.returncode != 0:
        print(f"Warning: yt-dlp exited with code {result.returncode}\n{result.stderr}")

    try:
        data = json.loads(result.stdout)
        if data.get("_type") != "playlist" or "title" not in data:
            print("Provided URL is not a valid playlist.")
            return
        name: str = data["title"]
        entries = [entry for entry in data.get("entries", []) if entry]
    except json.JSONDecodeError:
        print("Failed to parse yt-dlp output.")
        return

    if name in existing_playlists:
        print(f"Playlist '{name}' already exists. Run 'sync' to update it.")
        return

    existing_playlists[name] = {"url": url, "entries": entries}

    with open(data_file, "w") as f:
        json.dump({"playlists": existing_playlists}, f, indent=4)

    print(f"Added playlist: {name}")


def delete_playlist(name: str) -> None:
    if not data_file.exists():
        print("data.json does not exist.")
        return

    with open(data_file, "r") as f:
        data = json.load(f)

    if name in data.get("playlists", {}):
        del data["playlists"][name]
        with open(data_file, "w") as f:
            json.dump(data, f, indent=4)
        print(f"Deleted playlist: {name}")
    else:
        print(f"Playlist '{name}' not found.")


def list_playlists() -> None:
    if not data_file.exists():
        print("data.json does not exist.")
        return

    with open(data_file, "r") as f:
        data = json.load(f)
        for name in data.get("playlists", {}).keys():
            print(name)


def download() -> None:
    if not data_file.exists():
        print("data.json does not exist. Please run 'init' first.")
        return

    with open(data_file, "r") as f:
        data: Dict[str, Any] = json.load(f)
        playlists = data.get("playlists", {})

    for name, info in playlists.items():
        print(f"Downloading songs from playlist: {name}")
        entries = info.get("entries", [])
        for entry in entries:
            video_id = entry.get("id")
            title = entry.get("title")
            if not video_id or not title:
                continue
            safe_title = "".join(
                c for c in title if c.isalnum() or c in " -_()[]{}."
            ).strip()
            output_path = music_dir / f"{safe_title}.%(ext)s"
            if any(
                (music_dir / f).stem == safe_title
                for f in music_dir.iterdir()
                if f.is_file()
            ):
                print(f"\tAlready downloaded: {title}")
                continue
            url = f"https://www.youtube.com/watch?v={video_id}"
            result = subprocess.run(
                [
                    "yt-dlp",
                    "--ignore-errors",
                    "-o",
                    str(output_path),
                    "-x",
                    "--audio-format",
                    "mp3",
                    url,
                ],
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                print(f"\tDownloaded: {title}")
            else:
                print(f"Failed to download: {title}\n{result.stderr}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="A tool to manage and sync YouTube playlists."
    )
    parser.add_argument(
        "--data",
        type=Path,
        required=True,
        default=Path("data.json"),
        help="The path to the data json.",
    )
    parser.add_argument(
        "--music-dir",
        type=Path,
        required=True,
        default=Path("Music"),
        help="The output folder.",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("init", help="Initialize the data.json file")
    subparsers.add_parser("sync", help="Sync all playlists from data.json")

    add_parser = subparsers.add_parser("add_playlist", help="Add a new playlist by URL")
    add_parser.add_argument("url", help="YouTube playlist URL")

    subparsers.add_parser("download", help="Download all songs to the Music folder")

    delete_parser = subparsers.add_parser(
        "delete_playlist", help="Delete a playlist by name"
    )
    delete_parser.add_argument("name", help="Name of the playlist to delete")

    nokia_parser = subparsers.add_parser("nokia", help="Work on Nokia")
    nokia_parser.add_argument(
        "--nokia-root",
        type=Path,
        required=True,
        help="Nokia root directory path",
    )

    subparsers.add_parser("list", help="List all playlist names")

    args = parser.parse_args()

    global data_file
    data_file = args.data
    global music_dir
    music_dir = args.music_dir
    music_dir.mkdir(exist_ok=True)

    match args.command:
        case "init":
            init()
        case "sync":
            sync()
        case "add_playlist":
            add_playlist(args.url)
        case "download":
            download()
        case "delete_playlist":
            delete_playlist(args.name)
        case "list":
            list_playlists()
        case "nokia":
            assert getattr(args, "nokia_root")
            nokia_root: Path = args.nokia_root
            assert nokia_root.exists()
            with open(data_file, "r") as f:
                data: Dict[str, Any] = json.load(f)
                playlists = data.get("playlists", {})
            write_playlists(nokia_root, music_dir, playlists)
        case _:
            print(f"Unknown command: {args.command}")


if __name__ == "__main__":
    main()
