#!/bin/bash
set -e

hostport="$1"
shift
cmd="$@"
host="${hostport%%:*}"
port="${hostport##*:}"
timeout=90
interval=2
elapsed=0

until nc -z "$host" "$port"; do
  >&2 echo "Waiting for $host:$port..."
  sleep $interval
  elapsed=$((elapsed + interval))
  if [ $elapsed -ge $timeout ]; then
    >&2 echo "Timeout waiting for $host:$port after ${timeout}s"
    exit 1
  fi
done

>&2 echo "$host:$port is up - executing command"
exec $cmd