# 🗺️ Sri Lanka Grid (SLD99) CAD & KML Converter

A lightweight web application built with Streamlit to perform bi-directional coordinate transformations and file conversions between AutoCAD DXF drawings and Google Earth KML files for Sri Lanka[cite: 1].

## 🚀 Features

* **DXF to KML Conversion:** Transforms 2D/3D entities (`POINT`, `LINE`, `POLYLINE`, `SPLINE`, `ARC`, and `TEXT` labels) from **SLD99 / Sri Lanka Grid 1999 (EPSG:5235)** to **WGS84 (EPSG:4326)** for Google Earth[cite: 1].
* **KML to DXF Conversion:** Converts Google Earth placemarks and linestrings back to AutoCAD DXF entities in **SLD99** coordinates, with customizable text height for labels[cite: 2, 3].
* **Web-Based UI:** Simple drag-and-drop file processing in the browser with zero software installation required.

-Ranjith Wijekoon/2026 August

## 🛠️ Built With

* [Streamlit](https://streamlit.io/)
* [ezdxf](https://ezdxf.readthedocs.io/)
* [pyproj](https://pyproj4.github.io/pyproj/stable/)
* [simplekml](https://simplekml.readthedocs.io/)
