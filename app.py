import streamlit as st
import tempfile
import os
import ezdxf
from ezdxf import path
import simplekml
import xml.etree.ElementTree as ET
from pyproj import Transformer

# --- Streamlit Page Setup ---
st.set_page_config(
    page_title="Sri Lanka Grid (SLD99) Converter",
    page_icon="🗺️",
    layout="centered"
)

st.title("🗺️ SLD99 ↔ WGS84 Converter- K.D.R.W")
st.write("Convert CAD DXF files (**EPSG:5235 / SLD99**) to Google Earth KML files (**EPSG:4326 / WGS84**) and vice versa.")

# Define Transformers globally
transformer_to_wgs84 = Transformer.from_crs("EPSG:5235", "EPSG:4326", always_xy=True)
transformer_to_sld99 = Transformer.from_crs("EPSG:4326", "EPSG:5235", always_xy=True)

# --- Core Conversion Functions ---

def convert_dxf_to_kml(dxf_file_path):
    def transform_coords(x, y, z=0.0):
        lon, lat = transformer_to_wgs84.transform(x, y)
        return (lon, lat, z)

    doc = ezdxf.readfile(dxf_file_path)
    msp = doc.modelspace()
    kml = simplekml.Kml()

    for entity in msp:
        dxftype = entity.dxftype()

        if dxftype == 'POINT':
            x, y, z = entity.dxf.location
            kml.newpoint(coords=[transform_coords(x, y, z)])

        elif dxftype == 'LINE':
            start, end = entity.dxf.start, entity.dxf.end
            pt1 = transform_coords(start.x, start.y, start.z)
            pt2 = transform_coords(end.x, end.y, end.z)
            kml.newlinestring(coords=[pt1, pt2])

        elif dxftype in ['LWPOLYLINE', 'POLYLINE', 'SPLINE']:
            try:
                p = path.make_path(entity)
                vertices = [transform_coords(pt.x, pt.y, pt.z) for pt in p.flattening(distance=0.1)]
                if len(vertices) >= 2:
                    kml.newlinestring(coords=vertices)
            except Exception:
                pass

        elif dxftype == 'ARC':
            try:
                p = path.make_path(entity)
                vertices = [transform_coords(pt.x, pt.y, pt.z) for pt in p.flattening(distance=0.1)]
                if len(vertices) >= 2:
                    kml.newlinestring(coords=vertices)
            except Exception:
                pass

        elif dxftype in ['TEXT', 'MTEXT']:
            text_content = entity.plain_text() if dxftype == 'MTEXT' else entity.dxf.text
            insert = entity.dxf.insert
            kml.newpoint(name=text_content, coords=[transform_coords(insert.x, insert.y, insert.z)])

    return kml

def convert_kml_to_dxf(kml_file_path, text_height=2.5):
    def transform_coords(lon, lat, alt=0.0):
        x, y = transformer_to_sld99.transform(lon, lat)
        return (x, y, alt)

    tree = ET.parse(kml_file_path)
    root = tree.getroot()
    ns = {'kml': 'http://www.opengis.net/kml/2.2'}

    #doc = ezdxf.new(dxfversion='R2010')
    doc = ezdxf.new(dxfversion='R12')
    msp = doc.modelspace()

    def parse_coordinates(coord_str):
        points = []
        for coord in coord_str.strip().split():
            parts = coord.split(',')
            if len(parts) >= 2:
                lon, lat = float(parts[0]), float(parts[1])
                alt = float(parts[2]) if len(parts) >= 3 else 0.0
                points.append(transform_coords(lon, lat, alt))
        return points

    for placemark in root.findall('.//kml:Placemark', ns):
        name_elem = placemark.find('kml:name', ns)
        name = name_elem.text if name_elem is not None else "Unnamed"

        point = placemark.find('.//kml:Point', ns)
        if point is not None:
            coord_elem = point.find('kml:coordinates', ns)
            if coord_elem is not None and coord_elem.text:
                pts = parse_coordinates(coord_elem.text)
                if pts:
                    insertion_pt = pts[0]
                    msp.add_point(insertion_pt)
                    msp.add_text(name, dxfattribs={'height': text_height}).set_placement(insertion_pt)

        linestring = placemark.find('.//kml:LineString', ns)
        if linestring is not None:
            coord_elem = linestring.find('kml:coordinates', ns)
            if coord_elem is not None and coord_elem.text:
                pts = parse_coordinates(coord_elem.text)
                if len(pts) >= 2:
                    msp.add_polyline3d(pts)

    return doc

# --- Web UI Tabs ---

tab1, tab2 = st.tabs(["📄 DXF → KML", "🌐 KML → DXF"])

with tab1:
    st.subheader("Convert DXF (SLD99) to KML (WGS84)")
    uploaded_dxf = st.file_uploader("Choose a DXF file", type=["dxf"], key="dxf_input")

    if uploaded_dxf:
        if st.button("Convert DXF to KML"):
            try:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".dxf") as tmp_in:
                    tmp_in.write(uploaded_dxf.getvalue())
                    tmp_in_path = tmp_in.name

                with tempfile.NamedTemporaryFile(delete=False, suffix=".kml") as tmp_out:
                    tmp_out_path = tmp_out.name

                # Run conversion
                kml_obj = convert_dxf_to_kml(tmp_in_path)
                kml_obj.save(tmp_out_path)

                # Read output
                with open(tmp_out_path, "rb") as f:
                    kml_bytes = f.read()

                st.success("Conversion complete!")
                st.download_button(
                    label="📥 Download KML File",
                    data=kml_bytes,
                    file_name=f"{os.path.splitext(uploaded_dxf.name)[0]}.kml",
                    mime="application/vnd.google-earth.kml+xml"
                )

                # Cleanup
                os.remove(tmp_in_path)
                os.remove(tmp_out_path)

            except Exception as e:
                st.error(f"Error converting DXF: {str(e)}")

with tab2:
    st.subheader("Convert KML (WGS84) to DXF (SLD99)")
    uploaded_kml = st.file_uploader("Choose a KML file", type=["kml"], key="kml_input")
    # text_h = st.number_input("AutoCAD Text Height (meters)", value=2.5, step=0.5)
    text_h = st.number_input("AutoCAD Text Height (meters)", value=2, min_value=1, step=1, format="%d")

    if uploaded_kml:
        if st.button("Convert KML to DXF"):
            try:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".kml") as tmp_in:
                    tmp_in.write(uploaded_kml.getvalue())
                    tmp_in_path = tmp_in.name

                with tempfile.NamedTemporaryFile(delete=False, suffix=".dxf") as tmp_out:
                    tmp_out_path = tmp_out.name

                # Run conversion
                doc_obj = convert_kml_to_dxf(tmp_in_path, text_height=text_h)
                doc_obj.saveas(tmp_out_path)

                # Read output
                with open(tmp_out_path, "rb") as f:
                    dxf_bytes = f.read()

                st.success("Conversion complete!")
                st.download_button(
                    label="📥 Download DXF File",
                    data=dxf_bytes,
                    file_name=f"{os.path.splitext(uploaded_kml.name)[0]}.dxf",
                    mime="application/dxf"
                )

                # Cleanup
                os.remove(tmp_in_path)
                os.remove(tmp_out_path)

            except Exception as e:
                st.error(f"Error converting KML: {str(e)}")
