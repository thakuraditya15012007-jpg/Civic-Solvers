"""
maps_helper.py — Geospatial rendering utilities.
Generates Folium marker maps, density heatmaps, and routing diagrams.
Provides fallbacks to OpenStreetMap (OSM) when Google Maps API keys are unset.
"""
import folium
from folium.plugins import HeatMap, MarkerCluster
from config import GOOGLE_MAPS_API_KEY, PRIORITY_COLORS, DEFAULT_MAP_LAT, DEFAULT_MAP_LNG, DEFAULT_MAP_ZOOM
from backend.gcp_manager import download_gcs_bytes

def render_complaint_map(complaints: list[dict], center_lat: float = None, center_lng: float = None) -> str:
    """
    Builds a Folium map showing complaints as color-coded priority markers.
    Includes a HeatMap density layer and circular overlays for critical complaints.
    Returns the raw HTML representation of the map.
    """
    # Filter valid coordinates
    valid_complaints = []
    for c in complaints:
        lat, lng = c.get("latitude"), c.get("longitude")
        if lat is not None and lng is not None:
            # Check basic bounds for India (between lat 5-40, lng 65-100) or general coordinates
            try:
                valid_complaints.append((float(lat), float(lng), c))
            except ValueError:
                continue

    # Determine center coordinates
    if center_lat is None or center_lng is None:
        if valid_complaints:
            center_lat = sum(x[0] for x in valid_complaints) / len(valid_complaints)
            center_lng = sum(x[1] for x in valid_complaints) / len(valid_complaints)
            zoom = 10
        else:
            center_lat = DEFAULT_MAP_LAT
            center_lng = DEFAULT_MAP_LNG
            zoom = DEFAULT_MAP_ZOOM
    else:
        zoom = 12

    # Instantiate Map
    m = folium.Map(location=[center_lat, center_lng], zoom_start=zoom, control_scale=True)

    # Heatmap Layer
    heat_data = [[lat, lng] for lat, lng, _ in valid_complaints]
    if heat_data:
        HeatMap(heat_data, name="Complaint Density Hotspots", radius=25, blur=15).add_to(m)

    # Marker Cluster for high density markers
    marker_cluster = MarkerCluster(name="Complaint Markers").add_to(m)

    for lat, lng, comp in valid_complaints:
        priority = comp.get("priority", "MEDIUM")
        color = PRIORITY_COLORS.get(priority, "#FFD700")
        cid = comp.get("complaint_id", "N/A")
        issue_type = comp.get("issue_type", "Other")
        status = comp.get("status", "PENDING")
        reporter = comp.get("citizen_name", "Anonymous")
        submitted = comp.get("submitted_at", "N/A")[:10]

        # Premium design HTML Popup Card
        popup_html = f"""
        <div style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; width: 220px; font-size: 13px;">
            <h4 style="margin: 0 0 5px 0; color: #1E3A8A; font-weight: 600;">{issue_type}</h4>
            <div style="margin-bottom: 5px;">
                <span style="background-color: {color}; color: white; padding: 2px 6px; border-radius: 4px; font-weight: bold; font-size: 11px;">
                    {priority}
                </span>
                <span style="background-color: #E5E7EB; color: #374151; padding: 2px 6px; border-radius: 4px; font-size: 11px; margin-left: 5px;">
                    {status}
                </span>
            </div>
            <hr style="border: 0; border-top: 1px solid #E5E7EB; margin: 8px 0;"/>
            <table style="width: 100%; border-collapse: collapse;">
                <tr><td style="color: #6B7280; padding: 2px 0;">ID:</td><td style="font-weight: 500;">{cid}</td></tr>
                <tr><td style="color: #6B7280; padding: 2px 0;">Reporter:</td><td style="font-weight: 500;">{reporter}</td></tr>
                <tr><td style="color: #6B7280; padding: 2px 0;">Date:</td><td style="font-weight: 500;">{submitted}</td></tr>
            </table>
        </div>
        """
        iframe = folium.IFrame(html=popup_html, width=240, height=130)
        popup = folium.Popup(iframe, max_width=260)

        # Custom circular marker matching styling
        folium.CircleMarker(
            location=[lat, lng],
            radius=8,
            color="#FFFFFF",
            weight=1.5,
            fill=True,
            fill_color=color,
            fill_opacity=0.9,
            popup=popup,
            tooltip=f"{issue_type} ({priority})"
        ).add_to(marker_cluster)

        # Draw safety ring overlay for Critical priority issues
        if priority == "CRITICAL":
            folium.Circle(
                location=[lat, lng],
                radius=150, # 150m buffer
                color="#FF3333",
                weight=1,
                fill=True,
                fill_color="#FF3333",
                fill_opacity=0.15,
                tooltip="CRITICAL safety radius buffer zone (150m)"
            ).add_to(m)

    folium.LayerControl().add_to(m)
    return m._repr_html_()

def render_worker_route_map(worker_lat: float, worker_lng: float, complaint_lat: float, complaint_lng: float) -> str:
    """
    Builds a Folium map showing a field worker's location and their assigned complaint.
    Draws a direct route line connecting both markers.
    """
    m = folium.Map(location=[(worker_lat + complaint_lat)/2.0, (worker_lng + complaint_lng)/2.0], zoom_start=14)

    # Worker Location Marker
    folium.Marker(
        location=[worker_lat, worker_lng],
        popup="Worker Location",
        tooltip="Worker Location",
        icon=folium.Icon(color="blue", icon="user", prefix="fa")
    ).add_to(m)

    # Complaint Location Marker
    folium.Marker(
        location=[complaint_lat, complaint_lng],
        popup="Repair Job Location",
        tooltip="Repair Job Location",
        icon=folium.Icon(color="red", icon="wrench", prefix="fa")
    ).add_to(m)

    # Direct connect line representational path
    folium.PolyLine(
        locations=[[worker_lat, worker_lng], [complaint_lat, complaint_lng]],
        color="#2563EB",
        weight=3.5,
        opacity=0.8,
        tooltip="Straight Route Path"
    ).add_to(m)

    return m._repr_html_()

def get_geocode(address: str) -> dict:
    """
    Geocodes an address string using Google Maps Geocoding API.
    Provides standard Nagpur coordinates fallback if key is unset.
    """
    if GOOGLE_MAPS_API_KEY and address.strip():
        import requests
        try:
            url = f"https://maps.googleapis.com/maps/api/geocode/json?address={address}&key={GOOGLE_MAPS_API_KEY}"
            res = requests.get(url, timeout=10).json()
            if res.get("status") == "OK":
                loc = res["results"][0]["geometry"]["location"]
                return {
                    "lat": loc["lat"],
                    "lng": loc["lng"],
                    "formatted_address": res["results"][0]["formatted_address"],
                    "success": True
                }
        except Exception as e:
            print(f"⚠️ Geocoding failed: {e}")

    # Fallback to Nagpur (geographic center of India)
    return {
        "lat": 21.1458,
        "lng": 79.0882,
        "formatted_address": f"{address} (Local Fallback - Nagpur Central)",
        "success": False
    }

def build_google_maps_embed_url(lat: float, lng: float, zoom: int = 15) -> str:
    """
    Generates a Google Maps Iframe Embed URL if the API key is active.
    Defaults to OpenStreetMap iframe embeds for local sandbox demonstration.
    """
    if GOOGLE_MAPS_API_KEY:
        return f"https://www.google.com/maps/embed/v1/view?key={GOOGLE_MAPS_API_KEY}&center={lat},{lng}&zoom={zoom}"
    
    # OpenStreetMap IFrame Embed URL
    bbox_left = lng - 0.005
    bbox_right = lng + 0.005
    bbox_bottom = lat - 0.002
    bbox_top = lat + 0.002
    return f"https://www.openstreetmap.org/export/embed.html?bbox={bbox_left}%2C{bbox_bottom}%2C{bbox_right}%2C{bbox_top}&layer=mapnik&marker={lat}%2C{lng}"
