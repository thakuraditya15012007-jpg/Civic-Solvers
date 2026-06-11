# backend/gps_extractor.py
"""
GPS coordinate extraction from image EXIF metadata.
Used by the Citizen complaint page to auto-fill latitude/longitude
from the photo the citizen uploads.

Supports JPEG, PNG (with EXIF), HEIC (via Pillow).
Falls back gracefully if no GPS data is present.
"""
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
import io
import logging

logger = logging.getLogger(__name__)


def _get_exif_data(image: Image.Image) -> dict:
    """Extract raw EXIF data from a PIL Image object."""
    exif_data = {}
    try:
        raw_exif = image._getexif()
        if raw_exif:
            for tag_id, value in raw_exif.items():
                tag = TAGS.get(tag_id, tag_id)
                exif_data[tag] = value
    except (AttributeError, Exception) as e:
        logger.debug(f"No EXIF data: {e}")
    return exif_data


def _get_gps_info(exif_data: dict) -> dict:
    """Extract GPS sub-dictionary from EXIF data."""
    gps_info = {}
    raw_gps  = exif_data.get("GPSInfo")
    if not raw_gps:
        return {}
    for key, val in raw_gps.items():
        tag = GPSTAGS.get(key, key)
        gps_info[tag] = val
    return gps_info


def _dms_to_decimal(dms, ref: str) -> float:
    """
    Convert GPS DMS (degrees, minutes, seconds) tuple to decimal degrees.
    dms is a tuple of three values: (degrees, minutes, seconds)
    Each may be an IFDRational, float, or int.
    ref is 'N', 'S', 'E', or 'W'.
    """
    def to_float(val):
        try:
            return float(val)
        except Exception:
            # Handle IFDRational objects
            return float(val.numerator) / float(val.denominator)

    degrees = to_float(dms[0])
    minutes = to_float(dms[1])
    seconds = to_float(dms[2])

    decimal = degrees + (minutes / 60.0) + (seconds / 3600.0)

    if ref in ("S", "W"):
        decimal = -decimal

    return round(decimal, 7)


def extract_gps_from_bytes(image_bytes: bytes) -> dict:
    """
    Main entry point. Given raw image bytes, returns:
    {
        "found":     True/False,
        "latitude":  float or None,
        "longitude": float or None,
        "altitude":  float or None,
        "source":    "exif" | "none",
        "message":   human-readable status string,
    }

    Never raises an exception — always returns a dict.
    """
    result = {
        "found":     False,
        "latitude":  None,
        "longitude": None,
        "altitude":  None,
        "source":    "none",
        "message":   "No GPS data found in photo.",
    }

    if not image_bytes:
        result["message"] = "No photo provided."
        return result

    try:
        image     = Image.open(io.BytesIO(image_bytes))
        exif_data = _get_exif_data(image)

        if not exif_data:
            result["message"] = "Photo has no EXIF metadata. Enter coordinates manually."
            return result

        gps_info = _get_gps_info(exif_data)

        if not gps_info:
            result["message"] = (
                "Photo has no GPS tags in EXIF. "
                "This happens when location is disabled on the camera. "
                "Enter coordinates manually."
            )
            return result

        # Extract latitude
        lat_dms = gps_info.get("GPSLatitude")
        lat_ref = gps_info.get("GPSLatitudeRef", "N")
        lon_dms = gps_info.get("GPSLongitude")
        lon_ref = gps_info.get("GPSLongitudeRef", "E")

        if not lat_dms or not lon_dms:
            result["message"] = "GPS tags present but coordinates are empty."
            return result

        latitude  = _dms_to_decimal(lat_dms, lat_ref)
        longitude = _dms_to_decimal(lon_dms, lon_ref)

        # Basic sanity check — India is roughly 8°N–37°N, 68°E–97°E
        # But we accept any valid lat/lon worldwide
        if not (-90 <= latitude <= 90) or not (-180 <= longitude <= 180):
            result["message"] = f"GPS values out of range: {latitude}, {longitude}"
            return result

        # Extract altitude if present
        altitude = None
        alt_raw  = gps_info.get("GPSAltitude")
        if alt_raw is not None:
            try:
                altitude = round(float(alt_raw), 2)
            except Exception:
                altitude = None

        result.update({
            "found":     True,
            "latitude":  latitude,
            "longitude": longitude,
            "altitude":  altitude,
            "source":    "exif",
            "message":   (
                f"✅ GPS location extracted from photo: "
                f"{latitude:.6f}°, {longitude:.6f}°"
                + (f" | Alt: {altitude}m" if altitude else "")
            ),
        })
        logger.info(f"GPS extracted: {latitude}, {longitude}")
        return result

    except Exception as e:
        logger.warning(f"GPS extraction failed: {e}")
        result["message"] = f"Could not read photo metadata: {e}. Enter coordinates manually."
        return result


def extract_gps_from_uploaded_file(uploaded_file) -> dict:
    """
    Convenience wrapper for Streamlit uploaded file objects.
    uploaded_file is the return value of st.file_uploader().
    """
    if uploaded_file is None:
        return {
            "found": False, "latitude": None, "longitude": None,
            "altitude": None, "source": "none",
            "message": "No file uploaded.",
        }
    try:
        uploaded_file.seek(0)
        image_bytes = uploaded_file.read()
        uploaded_file.seek(0)   # Reset so the file can be read again for display
        return extract_gps_from_bytes(image_bytes)
    except Exception as e:
        return {
            "found": False, "latitude": None, "longitude": None,
            "altitude": None, "source": "none",
            "message": f"Error reading file: {e}",
        }
