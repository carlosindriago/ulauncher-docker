"""
Tests for dk.timeutils.
"""
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from dk.timeutils import (
    compute_cpu_percent,
    describe_container_activity,
    humanize_bytes,
    humanize_timedelta,
    parse_docker_timestamp,
)


class TestParseDockerTimestamp:

    def test_parses_nanosecond_precision_timestamp(self):
        dt = parse_docker_timestamp("2024-01-15T10:23:45.123456789Z")
        assert dt == datetime(2024, 1, 15, 10, 23, 45, 123456, tzinfo=timezone.utc)

    def test_parses_timestamp_without_fraction(self):
        dt = parse_docker_timestamp("2024-01-15T10:23:45Z")
        assert dt == datetime(2024, 1, 15, 10, 23, 45, tzinfo=timezone.utc)

    def test_zero_time_returns_none(self):
        assert parse_docker_timestamp("0001-01-01T00:00:00Z") is None

    def test_empty_returns_none(self):
        assert parse_docker_timestamp("") is None
        assert parse_docker_timestamp(None) is None

    def test_malformed_returns_none(self):
        assert parse_docker_timestamp("not-a-timestamp") is None


class TestHumanizeTimedelta:

    def test_seconds(self):
        assert humanize_timedelta(timedelta(seconds=42)) == "42s"

    def test_minutes(self):
        assert humanize_timedelta(timedelta(minutes=15)) == "15m"

    def test_hours_and_minutes(self):
        assert humanize_timedelta(timedelta(hours=2, minutes=15)) == "2h 15m"

    def test_exact_hours(self):
        assert humanize_timedelta(timedelta(hours=3)) == "3h"

    def test_days_and_hours(self):
        assert humanize_timedelta(timedelta(days=3, hours=4)) == "3d 4h"

    def test_exact_days(self):
        assert humanize_timedelta(timedelta(days=3)) == "3d"

    def test_negative_clamps_to_zero(self):
        assert humanize_timedelta(timedelta(seconds=-5)) == "0s"


class TestHumanizeBytes:

    def test_bytes(self):
        assert humanize_bytes(512) == "512 B"

    def test_kib(self):
        assert humanize_bytes(2048) == "2.0 KiB"

    def test_mib(self):
        assert humanize_bytes(100 * 1024 * 1024) == "100.0 MiB"

    def test_gib(self):
        assert humanize_bytes(2 * 1024 ** 3) == "2.0 GiB"

    def test_none_is_unknown(self):
        assert humanize_bytes(None) == "unknown"


class TestDescribeContainerActivity:

    FIXED_NOW = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

    def test_running_container(self):
        started_at = (self.FIXED_NOW - timedelta(hours=1, minutes=30))
        attrs = {"State": {"Status": "running",
                           "StartedAt": started_at.strftime("%Y-%m-%dT%H:%M:%S.%fZ")}}

        with patch("dk.timeutils.utcnow", return_value=self.FIXED_NOW):
            assert describe_container_activity(attrs) == "up 1h 30m"

    def test_exited_container_uses_finished_at(self):
        finished_at = (self.FIXED_NOW - timedelta(days=3))
        attrs = {"State": {
            "Status": "exited",
            "StartedAt": "2025-12-01T00:00:00Z",
            "FinishedAt": finished_at.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        }}

        with patch("dk.timeutils.utcnow", return_value=self.FIXED_NOW):
            assert describe_container_activity(attrs) == "stopped 3d ago"

    def test_never_started_container_uses_created(self):
        created_at = (self.FIXED_NOW - timedelta(hours=5))
        attrs = {
            "State": {"Status": "created", "FinishedAt": "0001-01-01T00:00:00Z"},
            "Created": created_at.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        }

        with patch("dk.timeutils.utcnow", return_value=self.FIXED_NOW):
            assert describe_container_activity(attrs) == "created 5h ago"

    def test_no_usable_timestamp_returns_none(self):
        assert describe_container_activity({"State": {"Status": "created"}}) is None


class TestComputeCpuPercent:

    def test_computes_percentage(self):
        stats = {
            "cpu_stats": {
                "cpu_usage": {"total_usage": 20_000_000},
                "system_cpu_usage": 200_000_000,
                "online_cpus": 4,
            },
            "precpu_stats": {
                "cpu_usage": {"total_usage": 0},
                "system_cpu_usage": 0,
            },
        }
        # cpu_delta=20e6, system_delta=200e6 -> (0.1) * 4 * 100 = 40.0
        assert compute_cpu_percent(stats) == 40.0

    def test_missing_fields_returns_none(self):
        assert compute_cpu_percent({}) is None

    def test_zero_system_delta_returns_none(self):
        stats = {
            "cpu_stats": {"cpu_usage": {"total_usage": 100}, "system_cpu_usage": 100},
            "precpu_stats": {"cpu_usage": {"total_usage": 100}, "system_cpu_usage": 100},
        }
        assert compute_cpu_percent(stats) is None
