# Isochrone Accessibility Analysis: Bandung Railway Station (South Gate)

![Bandung Station Isochrone Map](Isochrone_map_Bandung_Station.jpeg)

## 📌 Project Overview
This project presents an **Isochrone Accessibility Analysis** to evaluate pedestrian reachability from the **South Entrance of Bandung Railway Station (Stasiun Bandung)**. Using spatial network analysis, the project delineates 10-, 20-, and 30-minute walking boundaries (isochrones) to understand urban mobility, pedestrian catchment areas, and accessibility to public transit hubs in Bandung, West Java.

---

## 🎯 Key Objectives
* **Map Catchment Areas:** Delineate 10, 20, and 30-minute pedestrian walking zones around Stasiun Bandung (South Gate).
* **Urban Mobility Assessment:** Identify which sub-districts (*kelurahan*) fall within critical walking thresholds.
* **Data Integration:** Combine OpenStreetMap network data with administrative boundaries and satellite imagery for enhanced spatial context.

---

## 🛠️ Tech Stack & Data Sources
* **Language/Environment:** Python 3.x (Jupyter Notebook)
* **GIS Tools & Libraries:** `OSMnx`, `GeoPandas`, `Shapely`, `Matplotlib`, `Contextily`
* **Network & Isochrone Provider:** OpenRouteService API (Foot-walking mode)
* **Spatial Data Sources:** 
  * Road Network & Pedestrian Paths: **OpenStreetMap (OSM)**
  * Administrative Boundaries: **BPS / Indonesia Geospasial**
  * Basemap: **Esri World Imagery**

---

## 📊 Key Findings & Insights
1. **Primary Catchment Area (10-Minute Walk):**
   * Covers immediate urban areas including parts of *Kebon Jeruk* and *Pasir Kaliki*.
   * High pedestrian transit density with direct commercial access.
2. **Secondary Catchment Area (20-Minute Walk):**
   * Reaches key commercial and residential zones such as *Braga*, *Babakan Ciamis*, and *Arjuna*.
3. **Tertiary Catchment Area (30-Minute Walk):**
   * Extends to *Taman Sari*, *Merdeka*, and *Kebon Pisang*. Beyond this threshold, commuters are likely to switch from walking to motorized transport or micro-mobility options.

---

## 📁 Repository Structure
```text
├── data/
│   ├── raw/                  # Administrative SHP files & CSVs
│   └── processed/            # Exported GeoJSON isochrone polygons
├── notebooks/
│   └── isochrone_analysis.ipynb  # Complete Python workflow
├── outputs/
│   └── isochrone_map_bandung.jpg # Final map layout
├── README.md
└── requirements.txt
