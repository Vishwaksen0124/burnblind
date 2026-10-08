"""JSON conversion helpers for canonical data contracts."""

from datetime import datetime
from typing import Any, Mapping

from backend.common.models import CandidateEvent, ContractError, FireObservation


def candidate_event_to_dict(event: CandidateEvent) -> dict[str, Any]:
    return {
        "event_id": event.event_id,
        "grid_id": event.grid_id,
        "detected_at_utc": event.detected_at_utc.isoformat().replace("+00:00", "Z"),
        "last_observed_at_utc": event.last_observed_at_utc.isoformat().replace("+00:00", "Z"),
        "latitude": event.latitude,
        "longitude": event.longitude,
        "detection_count": event.detection_count,
        "sources": list(event.sources),
        "evidence_ids": list(event.evidence_ids),
        "data_mode": event.data_mode,
        "processing_version": event.processing_version,
    }


def fire_observation_to_dict(record: FireObservation) -> dict[str, Any]:
    return {
        "fire_id": record.fire_id,
        "source": record.source,
        "observed_at_utc": record.observed_at_utc.isoformat().replace("+00:00", "Z"),
        "latitude": record.latitude,
        "longitude": record.longitude,
        "grid_id": record.grid_id,
        "confidence": record.confidence,
        "source_version": record.source_version,
        "brightness_temperature_difference_ref": record.brightness_temperature_difference_ref,
        "brightness_temperature_038_micron_k": record.brightness_temperature_038_micron_k,
        "brightness_temperature_112_micron_k": record.brightness_temperature_112_micron_k,
        "confidence_flag": record.confidence_flag,
        "source_confidence": record.source_confidence,
        "brightness_temperature_channel_1_k": record.brightness_temperature_channel_1_k,
        "brightness_temperature_channel_2_k": record.brightness_temperature_channel_2_k,
        "channel_1_name": record.channel_1_name,
        "channel_2_name": record.channel_2_name,
        "frp_mw": record.frp_mw,
        "scan_size_km": record.scan_size_km,
        "track_size_km": record.track_size_km,
        "satellite": record.satellite,
        "instrument": record.instrument,
        "daynight": record.daynight,
    }


def fire_observation_from_dict(payload: Mapping[str, Any]) -> FireObservation:
    """Parse and validate persisted JSON through the canonical contract."""
    try:
        timestamp = datetime.fromisoformat(str(payload["observed_at_utc"]).replace("Z", "+00:00"))
        return FireObservation(
            fire_id=payload["fire_id"],
            source=payload["source"],
            observed_at_utc=timestamp,
            latitude=payload["latitude"],
            longitude=payload["longitude"],
            grid_id=payload["grid_id"],
            confidence=payload["confidence"],
            source_version=payload["source_version"],
            brightness_temperature_difference_ref=payload.get("brightness_temperature_difference_ref"),
            brightness_temperature_038_micron_k=payload.get("brightness_temperature_038_micron_k"),
            brightness_temperature_112_micron_k=payload.get("brightness_temperature_112_micron_k"),
            confidence_flag=payload.get("confidence_flag"),
            source_confidence=payload.get("source_confidence"),
            brightness_temperature_channel_1_k=payload.get("brightness_temperature_channel_1_k"),
            brightness_temperature_channel_2_k=payload.get("brightness_temperature_channel_2_k"),
            channel_1_name=payload.get("channel_1_name"),
            channel_2_name=payload.get("channel_2_name"),
            frp_mw=payload.get("frp_mw"),
            scan_size_km=payload.get("scan_size_km"),
            track_size_km=payload.get("track_size_km"),
            satellite=payload.get("satellite"),
            instrument=payload.get("instrument"),
            daynight=payload.get("daynight"),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise ContractError(f"invalid FireObservation JSON: {exc}") from exc
