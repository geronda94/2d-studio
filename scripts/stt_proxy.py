#!/usr/bin/env python3
"""Expose a localhost-only STT (faster-whisper) service to Docker.

Whisper often binds 127.0.0.1:8788, which a container cannot reach. This tiny
TCP proxy listens on the Docker bridge gateway (default 172.17.0.1:8788) and
forwards to 127.0.0.1:8788, so `host.docker.internal:8788` works without
changing the STT service or using host networking.

Run: python3 scripts/stt_proxy.py
"""
from __future__ import annotations

import argparse
import socket
import threading


def pipe(src: socket.socket, dst: socket.socket) -> None:
    try:
        while True:
            data = src.recv(65536)
            if not data:
                break
            dst.sendall(data)
    except OSError:
        pass
    finally:
        try:
            dst.shutdown(socket.SHUT_WR)
        except OSError:
            pass


def handle(client: socket.socket, target: tuple[str, int]) -> None:
    try:
        upstream = socket.create_connection(target, timeout=5)
    except OSError:
        client.close()
        return
    threading.Thread(target=pipe, args=(client, upstream), daemon=True).start()
    threading.Thread(target=pipe, args=(upstream, client), daemon=True).start()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--listen-host", default="172.17.0.1")
    ap.add_argument("--port", type=int, default=8788)
    ap.add_argument("--target-host", default="127.0.0.1")
    ap.add_argument("--target-port", type=int, default=8788)
    args = ap.parse_args()
    target = (args.target_host, args.target_port)
    with socket.create_server((args.listen_host, args.port), reuse_port=True) as srv:
        print(f"stt proxy {args.listen_host}:{args.port} -> {target[0]}:{target[1]}", flush=True)
        while True:
            client, _ = srv.accept()
            threading.Thread(target=handle, args=(client, target), daemon=True).start()


if __name__ == "__main__":
    main()
