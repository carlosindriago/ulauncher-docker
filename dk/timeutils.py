"""
Helpers to turn Docker's raw timestamps and stats() payloads into the
human-readable strings shown in the extension's UI. Kept dependency-free
(no docker/gi imports) so it can be unit tested in isolation.
"""
from datetime import datetime, timezone

# Docker reports "no value" timestamps (e.g. FinishedAt on a container that
# never stopped) as the Go zero time, which always starts with this prefix.
_ZERO_TIME_PREFIX = "0001-01-01"


def utcnow():
    """ Returns the current time as a timezone-aware UTC datetime. """
    return datetime.now(timezone.utc)


def parse_docker_timestamp(timestamp):
    """
    Parses a Docker RFC3339 timestamp (nanosecond precision, e.g.
    "2024-01-15T10:23:45.123456789Z") into an aware UTC datetime.
    Returns None for empty, malformed or zero-value timestamps.
    """
    if not timestamp or timestamp.startswith(_ZERO_TIME_PREFIX):
        return None

    value = timestamp.rstrip("Z")
    if "." in value:
        date_part, fraction = value.split(".", 1)
        # datetime.strptime only supports microsecond (6-digit) precision.
        value = "%s.%s" % (date_part, fraction[:6].ljust(6, "0"))
        fmt = "%Y-%m-%dT%H:%M:%S.%f"
    else:
        fmt = "%Y-%m-%dT%H:%M:%S"

    try:
        return datetime.strptime(value, fmt).replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def humanize_timedelta(delta):
    """ Formats a timedelta as a short string, e.g. "2h 15m", "3d", "42s". """
    seconds = int(delta.total_seconds())
    if seconds < 0:
        seconds = 0

    days, remainder = divmod(seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)

    if days:
        return "%dd %dh" % (days, hours) if hours else "%dd" % days
    if hours:
        return "%dh %dm" % (hours, minutes) if minutes else "%dh" % hours
    if minutes:
        return "%dm" % minutes
    return "%ds" % seconds


def humanize_bytes(num_bytes):
    """ Formats a byte count as a short human-readable string, e.g. "45.2 MiB". """
    if num_bytes is None:
        return "unknown"

    value = float(num_bytes)
    for unit in ("B", "KiB", "MiB", "GiB", "TiB"):
        if unit == "B":
            if value < 1024.0:
                return "%d B" % value
        elif value < 1024.0 or unit == "TiB":
            return "%.1f %s" % (value, unit)
        value /= 1024.0
    return "%.1f TiB" % value  # pragma: no cover - unreachable in practice


def describe_container_activity(attrs):
    """
    Describes how long a container has been in its current state, based on
    the `attrs` dict returned by the Docker API (from a list or inspect
    call). Returns e.g. "up 2h 15m", "stopped 3d ago", "created 5h ago", or
    None when no usable timestamp is available.
    """
    state = attrs.get("State") or {}

    if state.get("Status") == "running" or state.get("Running"):
        started_at = parse_docker_timestamp(state.get("StartedAt"))
        if started_at:
            return "up %s" % humanize_timedelta(utcnow() - started_at)
        return None

    finished_at = parse_docker_timestamp(state.get("FinishedAt"))
    if finished_at:
        return "stopped %s ago" % humanize_timedelta(utcnow() - finished_at)

    created_at = parse_docker_timestamp(attrs.get("Created"))
    if created_at:
        return "created %s ago" % humanize_timedelta(utcnow() - created_at)

    return None


def compute_cpu_percent(stats):
    """
    Computes the CPU usage percentage from a single docker `stats(stream=False)`
    payload, using the same delta formula as the Docker CLI. Returns None if
    the payload doesn't have the fields needed (e.g. a container that just
    started and has no previous sample yet).
    """
    try:
        cpu = stats["cpu_stats"]
        precpu = stats["precpu_stats"]
        cpu_delta = cpu["cpu_usage"]["total_usage"] - precpu["cpu_usage"]["total_usage"]
        system_delta = cpu["system_cpu_usage"] - precpu["system_cpu_usage"]
        online_cpus = cpu.get("online_cpus") or len(cpu["cpu_usage"].get("percpu_usage") or [1])
    except (KeyError, TypeError):
        return None

    if system_delta <= 0 or cpu_delta < 0:
        return None

    return (cpu_delta / system_delta) * online_cpus * 100.0
