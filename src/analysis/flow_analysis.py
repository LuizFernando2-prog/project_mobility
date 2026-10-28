"""
Maximum Flow analysis using Edmonds-Karp algorithm.
Models social influence zones → Points of Interest → Sink.
"""

import math
from collections import deque, defaultdict
from typing import Dict, List, Tuple

import pyodbc
import folium

from src.config import (
    get_connection_string,
    SP_LAT_MIN, SP_LAT_MAX,
    SP_LON_MIN, SP_LON_MAX,
    DIST_MAX_KM,
    MAX_CONNECTIONS,
)


class FlowGraph:
    """Directed graph with capacity for Edmonds-Karp max-flow."""

    def __init__(self):
        self.capacity = defaultdict(lambda: defaultdict(float))
        self.adj = defaultdict(list)

    def add_edge(self, u: str, v: str, capacity: float):
        if v not in self.adj[u]:
            self.adj[u].append(v)
        if u not in self.adj[v]:
            self.adj[v].append(u)
        self.capacity[u][v] += float(capacity)
        self.capacity[v][u] += 0  # residual

    def max_flow(self, source: str, sink: str) -> float:
        total_flow = 0.0
        while True:
            parent = {source: None}
            queue = deque([source])

            while queue:
                u = queue.popleft()
                for v in self.adj[u]:
                    if v not in parent and self.capacity[u][v] > 0:
                        parent[v] = u
                        queue.append(v)

            if sink not in parent:
                break

            # Find bottleneck
            path_flow = float("inf")
            v = sink
            while v != source:
                u = parent[v]
                path_flow = min(path_flow, self.capacity[u][v])
                v = u

            # Update residual capacities
            v = sink
            while v != source:
                u = parent[v]
                self.capacity[u][v] -= path_flow
                self.capacity[v][u] += path_flow
                v = u

            total_flow += path_flow

        return total_flow


def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Distance in kilometers between two points."""
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2) ** 2
    )
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def get_connection():
    return pyodbc.connect(get_connection_string())


def run_flow_analysis(year: int, output_path: str = None) -> float:
    """
    Build the social-transport flow network for a given year
    and compute the maximum flow.
    Returns the max flow value and optionally saves an interactive map.
    """
    conn = get_connection()
    cursor = conn.cursor()

    print(f"\n{'='*70}")
    print(f"  FLOW ANALYSIS — São Paulo {year}")
    print(f"{'='*70}\n")

    # --- Load social zones ---
    cursor.execute(
        """
        SELECT T.latitude, T.longitude, I.impacto_estimado, S.valor
        FROM Coleta_Interacao_SocialTransporte I
        JOIN Coleta_SPTrans T ON I.sptrans_id = T.id
        JOIN Coleta_Sociais_Agregados S ON I.sociais_id = S.id
        WHERE S.ano = ?
          AND T.latitude BETWEEN ? AND ?
          AND T.longitude BETWEEN ? AND ?
        """,
        (year, SP_LAT_MIN, SP_LAT_MAX, SP_LON_MIN, SP_LON_MAX),
    )

    zones = [
        {
            "lat": float(r[0]),
            "lon": float(r[1]),
            "impact": float(r[2]),
            "value": float(r[3]),
            "is_social": True,
        }
        for r in cursor.fetchall()
    ]
    print(f"Social zones found: {len(zones)}")

    # Fallback: check-ins
    if not zones:
        print("No social interaction data. Falling back to check-ins...")
        cursor.execute(
            """
            SELECT latitude, longitude, COUNT(*) as cnt
            FROM Coleta_Checkins
            WHERE YEAR(checkin_time) = ?
              AND latitude BETWEEN ? AND ?
              AND longitude BETWEEN ? AND ?
            GROUP BY latitude, longitude
            HAVING COUNT(*) >= 3
            """,
            (year, SP_LAT_MIN, SP_LAT_MAX, SP_LON_MIN, SP_LON_MAX),
        )
        zones = [
            {
                "lat": float(r[0]),
                "lon": float(r[1]),
                "impact": 1.0,
                "value": float(r[2]),
                "is_social": False,
            }
            for r in cursor.fetchall()
        ]
        print(f"Check-in zones used: {len(zones)}")

    # --- Load POIs ---
    cursor.execute(
        """
        SELECT G.place_id, G.latitude, G.longitude,
               ISNULL(P.total_avaliacoes, 0),
               ISNULL(P.nota_media, 0)
        FROM Coleta_Google G
        LEFT JOIN Coleta_Google_Popularidade P ON G.place_id = P.place_id
        WHERE G.latitude IS NOT NULL AND G.longitude IS NOT NULL
        """
    )

    poi_dict = {}
    for r in cursor.fetchall():
        place_id, lat, lon, pop, rating = r
        key = (round(float(lat), 5), round(float(lon), 5))
        if key not in poi_dict or pop > poi_dict[key]["pop"]:
            poi_dict[key] = {
                "id": place_id,
                "lat": float(lat),
                "lon": float(lon),
                "pop": float(pop),
                "rating": float(rating),
            }
    pois = list(poi_dict.values())
    print(f"Unique POIs loaded: {len(pois)}")

    # --- Build graph ---
    graph = FlowGraph()
    SOURCE, SINK = "SOURCE", "SINK"
    edges = []

    for z in zones:
        node_z = f"ZONA_{z['lat']:.6f}_{z['lon']:.6f}"
        if z.get("is_social", True):
            capacity = max(1.0, (z["impact"] * z["value"]) / 100)
        else:
            capacity = max(1.0, z["value"] / 20)
        graph.add_edge(SOURCE, node_z, capacity)

        nearby = [
            (haversine(z["lat"], z["lon"], p["lat"], p["lon"]), p)
            for p in pois
            if 0.01 < haversine(z["lat"], z["lon"], p["lat"], p["lon"]) < DIST_MAX_KM
        ]
        nearby.sort(key=lambda x: x[0])

        for _, p in nearby[:MAX_CONNECTIONS]:
            node_p = f"POI_{p['id']}"
            graph.add_edge(node_z, node_p, 50.0)
            edges.append((z, p))

    for p in pois:
        graph.add_edge(f"POI_{p['id']}", SINK, max(1.0, p["pop"] / 20))

    print(f"Edges created: {len(edges)}")

    # --- Compute max flow ---
    flow = graph.max_flow(SOURCE, SINK)
    print(f"\n>>> Maximum Flow ({year}): {flow:.2f}")

    # --- Optional map ---
    if output_path:
        _generate_map(zones, pois, edges, graph, year, output_path)

    conn.close()
    return flow


def _generate_map(zones, pois, edges, graph, year, path):
    """Generate an interactive Folium map."""
    m = folium.Map(
        location=[-23.55, -46.63],
        zoom_start=12,
        tiles="CartoDB positron",
    )

    influenced = set()
    for z, p in edges:
        node_z = f"ZONA_{z['lat']:.6f}_{z['lon']:.6f}"
        node_p = f"POI_{p['id']}"
        if graph.capacity[node_p][node_z] > 0:
            influenced.add(p["id"])

    for p in pois:
        color = "purple" if p["id"] in influenced else "#808080"
        folium.CircleMarker(
            [p["lat"], p["lon"]],
            radius=3.5,
            color=color,
            fill=True,
            fill_opacity=0.85,
            popup=f"POI<br>Popularity: {p['pop']}",
        ).add_to(m)

    for z in zones:
        color = "#0066FF" if z.get("is_social", True) else "#FF8800"
        folium.CircleMarker(
            [z["lat"], z["lon"]],
            radius=7,
            color=color,
            fill=True,
            fill_opacity=0.95,
            popup="Social Zone" if z.get("is_social", True) else "Fallback Zone",
        ).add_to(m)

    for z, p in edges:
        node_z = f"ZONA_{z['lat']:.6f}_{z['lon']:.6f}"
        node_p = f"POI_{p['id']}"
        flow_val = graph.capacity[node_p][node_z]
        if flow_val <= 0:
            continue

        if flow_val > 40:
            color, weight = "#00FF00", 6
        elif flow_val > 20:
            color, weight = "#FFAA00", 4.5
        else:
            color, weight = "#FF3333", 3

        folium.PolyLine(
            [[z["lat"], z["lon"]], [p["lat"], p["lon"]]],
            color=color,
            weight=weight,
            opacity=0.85,
        ).add_to(m)

    legend = f"""
    <div style="position:fixed; bottom:40px; left:40px; width:320px;
                background:white; border:2px solid #333; z-index:9999;
                font-size:13px; padding:14px; border-radius:8px;">
      <b>Urban Social Flow — São Paulo {year}</b><br><br>
      <b>Nodes:</b><br>
      <span style="color:#0066FF;">●</span> Social Zone<br>
      <span style="color:#FF8800;">●</span> Fallback Zone<br>
      <span style="color:purple;">●</span> Influenced POI<br>
      <span style="color:#808080;">●</span> Neutral POI<br><br>
      <b>Edge Flow:</b><br>
      <span style="color:#00FF00;">—</span> High (&gt;40)<br>
      <span style="color:#FFAA00;">—</span> Medium (20-40)<br>
      <span style="color:#FF3333;">—</span> Low / Bottleneck (≤20)
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend))
    m.fit_bounds([[SP_LAT_MIN, SP_LON_MIN], [SP_LAT_MAX, SP_LON_MAX]])
    m.save(path)
    print(f"Map saved → {path}")


if __name__ == "__main__":
    year = int(input("Enter year for analysis (e.g. 2021): ").strip())
    run_flow_analysis(year, output_path=f"maps/fluxo_social_SP_{year}.html")
