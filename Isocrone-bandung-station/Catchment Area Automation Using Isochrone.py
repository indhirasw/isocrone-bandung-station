# 0 = OpenRouteService
INPUT_PROVIDER = 0

# Contoh:
# 0 = driving-car
# 1 = driving-hgv
# 2 = cycling-regular
# 3 = cycling-road
# 4 = cycling-safe
# 5 = cycling-mountain
# 6 = foot-walking
# 7 = foot-hiking
INPUT_PROFILE = 6

# 0 = time
# 1 = distance
INPUT_METRIC = 0

# 0 = start
# 1 = destination
LOCATION_TYPE = 1

# Smoothing
INPUT_SMOOTHING = None

# Avoid features
INPUT_AVOID_FEATURES = []

# Avoid borders
INPUT_AVOID_BORDERS = None

# Avoid countries
INPUT_AVOID_COUNTRIES = ""

# Avoid polygons
INPUT_AVOID_POLYGONS = None

#=================================================

import processing
from qgis.core import (
    QgsProject,
    QgsField,
    QgsVectorLayer,
    QgsFeature,
    QgsSpatialIndex,
    QgsWkbTypes
)
from qgis.PyQt.QtCore import QVariant

#===========================================

# Nama layer yang SUDAH ADA di QGIS
POINT_LAYER_NAME = "Site Point"
KELURAHAN_LAYER_NAME = "Kelurahan Kota Bandung"

# Field populasi pada layer Kelurahan
POPULATION_FIELD = "population"

# Field ID unik kelurahan
ID_FIELD = "fid"

# Output catchment yang digunakan
TARGET_MINUTE = 20

# Isochrone ranges
ISOCHRONE_RANGES = "10, 20, 30"

#===========================================

project = QgsProject.instance()

point_layers = project.mapLayersByName(POINT_LAYER_NAME)
kel_layers = project.mapLayersByName(KELURAHAN_LAYER_NAME)

if not point_layers:
    raise Exception(
        f"Layer '{POINT_LAYER_NAME}' tidak ditemukan di QGIS."
    )

if not kel_layers:
    raise Exception(
        f"Layer '{KELURAHAN_LAYER_NAME}' tidak ditemukan di QGIS."
    )

point_layer = point_layers[0]
kel_layer = kel_layers[0]

# ============================================================
# Tambahan: Populasi usia produktif
# ============================================================

PROD_FIELDS = [
    "p_age_15_1", "p_age_20_2", "p_age_25_2", "p_age_30_3",
    "p_age_35_3", "p_age_40_4", "p_age_45_4", "p_age_50_5",
    "p_age_55_5", "p_age_60_6"
]  # sesuaikan dengan nama kolom di attribute table

# Cek semua kolom ada
for f in PROD_FIELDS:
    if kel_layer.fields().indexOf(f) < 0:
        raise Exception(f"Kolom '{f}' tidak ditemukan di layer kelurahan.")

expr = " + ".join([f'COALESCE("{f}", 0)' for f in PROD_FIELDS])

prod_result = processing.run(
    "native:fieldcalculator",
    {
        'INPUT': kel_layer,
        'FIELD_NAME': 'POP_PROD',
        'FIELD_TYPE': 1,        # integer
        'FIELD_LENGTH': 10,
        'FIELD_PRECISION': 0,
        'FORMULA': expr,
        'OUTPUT': 'TEMPORARY_OUTPUT'
    }
)

kel_layer = prod_result['OUTPUT']
POPULATION_FIELD = "POP_PROD"

print("\n==========================================")
print("AUTOMATED ISOCHRONE + CATCHMENT ANALYSIS")
print("==========================================")

print(f"Point layer     : {POINT_LAYER_NAME}")
print(f"Kelurahan layer : {KELURAHAN_LAYER_NAME}")
print(f"Population      : {POPULATION_FIELD}")
print(f"Target catchment: {TARGET_MINUTE} menit")

#==============================================================

print("\n[1/8] Membuat Isochrone...")

iso_result = processing.run(
    "ORS Tools:isochrones_from_layer",
    {
        'INPUT_PROVIDER': INPUT_PROVIDER,
        'INPUT_PROFILE': INPUT_PROFILE,
        'INPUT_POINT_LAYER': point_layer.source(),
        'INPUT_FIELD': '',
        'INPUT_METRIC': INPUT_METRIC,
        'INPUT_RANGES': ISOCHRONE_RANGES,
        'INPUT_SMOOTHING': INPUT_SMOOTHING,
        'LOCATION_TYPE': LOCATION_TYPE,
        'INPUT_AVOID_FEATURES': INPUT_AVOID_FEATURES,
        'INPUT_AVOID_BORDERS': INPUT_AVOID_BORDERS,
        'INPUT_AVOID_COUNTRIES': INPUT_AVOID_COUNTRIES,
        'INPUT_AVOID_POLYGONS': INPUT_AVOID_POLYGONS,
        'OUTPUT': 'TEMPORARY_OUTPUT'
    }
)

iso_layer = iso_result['OUTPUT']

print("Isochrone berhasil dibuat.")

#==================================================================================

print("\n[2/8] Mencari field range isochrone...")

print("Field hasil ORS:")

for field in iso_layer.fields():
    print(" -", field.name(), field.typeName())


# ORS umumnya menghasilkan AA_MINS / AA_METERS.
# Kita cari secara otomatis.

range_field = None

possible_fields = [
    "AA_MINS",
    "AA_METERS",
    "range",
    "value",
    "VALUE"
]

for candidate in possible_fields:
    if iso_layer.fields().indexOf(candidate) >= 0:
        range_field = candidate
        break

if range_field is None:
    raise Exception(
        "Tidak menemukan field range isochrone. "
        "Lihat daftar field hasil ORS di console."
    )

print(f"Range field ditemukan: {range_field}")

#===========================================================================

print(f"\n[3/8] Mengambil isochrone {TARGET_MINUTE} menit...")

# Buat temporary layer untuk catchment 20 menit
iso10_result = processing.run(
    "native:extractbyexpression",
    {
        'INPUT': iso_layer,
        'EXPRESSION':
            f'"{range_field}" = {TARGET_MINUTE}',
        'OUTPUT': 'TEMPORARY_OUTPUT'
    }
)

iso10 = iso10_result['OUTPUT']

print(
    f"Isochrone {TARGET_MINUTE} menit berhasil diekstrak."
)

#==============================================================================

print("\n[4/8] Memilih kelurahan yang terkena catchment...")

selected_kel_result = processing.run(
    "native:extractbylocation",
    {
        'INPUT': kel_layer,
        'PREDICATE': [0],   # intersects
        'INTERSECT': iso10,
        'OUTPUT': 'TEMPORARY_OUTPUT'
    }
)

selected_kel = selected_kel_result['OUTPUT']

print(
    f"Kelurahan terkena catchment: "
    f"{selected_kel.featureCount()}"
)

#==============================================================

print("\n[5/8] Menghitung luas masing-masing kelurahan...")

area_result = processing.run(
    "native:fieldcalculator",
    {
        'INPUT': selected_kel,
        'FIELD_NAME': 'AREA_KM2',
        'FIELD_TYPE': 0,
        'FIELD_LENGTH': 20,
        'FIELD_PRECISION': 6,
        'FORMULA': '$area / 1000000',
        'OUTPUT': 'TEMPORARY_OUTPUT'
    }
)

selected_area = area_result['OUTPUT']

print("Luas kelurahan berhasil dihitung.")

#===========================================================================

print("\n[6/8] Melakukan clip kelurahan dengan catchment...")

clip_result = processing.run(
    "native:clip",
    {
        'INPUT': selected_area,
        'OVERLAY': iso10,
        'OUTPUT': 'TEMPORARY_OUTPUT'
    }
)

clipped = clip_result['OUTPUT']

print(
    f"Feature hasil clip: {clipped.featureCount()}"
)

#================================================================

print("\n[7/8] Menghitung luas area yang masuk catchment...")

clip_area_result = processing.run(
    "native:fieldcalculator",
    {
        'INPUT': clipped,
        'FIELD_NAME': 'CLIP_KM2',
        'FIELD_TYPE': 0,
        'FIELD_LENGTH': 20,
        'FIELD_PRECISION': 6,
        'FORMULA': '$area / 1000000',
        'OUTPUT': 'TEMPORARY_OUTPUT'
    }
)

clipped_area = clip_area_result['OUTPUT']

#======================================================================

print("\nMenggabungkan kembali hasil clip per kelurahan...")

dissolve_result = processing.run(
    "native:dissolve",
    {
        'INPUT': clipped_area,
        'FIELD': [ID_FIELD],
        'SEPARATE_DISJOINT': False,
        'OUTPUT': 'TEMPORARY_OUTPUT'
    }
)

clipped_dissolved = dissolve_result['OUTPUT']


# Hitung ulang area setelah dissolve
clip_area_result2 = processing.run(
    "native:fieldcalculator",
    {
        'INPUT': clipped_dissolved,
        'FIELD_NAME': 'CATCH_KM2',
        'FIELD_TYPE': 0,
        'FIELD_LENGTH': 20,
        'FIELD_PRECISION': 6,
        'FORMULA': '$area / 1000000',
        'OUTPUT': 'TEMPORARY_OUTPUT'
    }
)

clipped_dissolved = clip_area_result2['OUTPUT']

#==================================================================================

print("\nJoining luas catchment ke layer kelurahan...")

join_result = processing.run(
    "native:joinattributestable",
    {
        'INPUT': selected_area,
        'FIELD': ID_FIELD,
        'INPUT_2': clipped_dissolved,
        'FIELD_2': ID_FIELD,
        'FIELDS_TO_COPY': ['CATCH_KM2'],
        'METHOD': 1,
        'DISCARD_NONMATCHING': False,
        'PREFIX': 'CATCH_',
        'OUTPUT': 'TEMPORARY_OUTPUT'
    }
)

final_layer = join_result['OUTPUT']

#========================================================================

print("\nMenghitung proporsi area yang masuk catchment...")

fraction_result = processing.run(
    "native:fieldcalculator",
    {
        'INPUT': final_layer,
        'FIELD_NAME': 'CATCH_FRAC',
        'FIELD_TYPE': 0,
        'FIELD_LENGTH': 20,
        'FIELD_PRECISION': 6,
        'FORMULA':
            'CASE '
            'WHEN "AREA_KM2" > 0 '
            'THEN "CATCH_CATCH_KM2" / "AREA_KM2" '
            'ELSE 0 '
            'END',
        'OUTPUT': 'TEMPORARY_OUTPUT'
    }
)

final_layer = fraction_result['OUTPUT']

#=========================================================================

print("\nMenghitung estimasi populasi tercatchment...")

pop_result = processing.run(
    "native:fieldcalculator",
    {
        'INPUT': final_layer,
        'FIELD_NAME': 'POP_CATCH',
        'FIELD_TYPE': 0,
        'FIELD_LENGTH': 20,
        'FIELD_PRECISION': 2,
        'FORMULA':
            f'COALESCE("{POPULATION_FIELD}", 0) * "CATCH_FRAC"',
        'OUTPUT': 'TEMPORARY_OUTPUT'
    }
)

final_layer = pop_result['OUTPUT']

#===================================================================================

# Add Layer Hasil
final_layer.setName(
    f"Catchment {TARGET_MINUTE}min - Kelurahan"
)
QgsProject.instance().addMapLayer(final_layer)


# Add Layer Isochrone
iso10.setName(
    f"Isochrone {TARGET_MINUTE}min"
)
QgsProject.instance().addMapLayer(iso10)

# Summary
print("\n==========================================")
print("ANALISIS SELESAI")
print("==========================================")

print(
    f"Jumlah kelurahan terkena catchment : "
    f"{final_layer.featureCount()}"
)

print(
    f"Catchment yang digunakan            : "
    f"{TARGET_MINUTE} menit"
)

print("\nField hasil:")

for field in final_layer.fields():
    print(" -", field.name())

print("\nOutput utama:")
print("1. Isochrone 10 menit")
print("2. Kelurahan terdampak")
print("3. AREA_KM2      = luas seluruh kelurahan")
print("4. CATCH_KM2     = luas bagian yang tercatchment")
print("5. CATCH_FRAC    = proporsi area tercatchment")
print("6. POP_CATCH     = estimasi populasi tercatchment")

print("\n==========================================")
print("DONE")
print("==========================================")

iso_layer.setName("Isochrone semua interval")
QgsProject.instance().addMapLayer(iso_layer)
#==============================================================================================
total_pop = sum(f["POP_CATCH"] for f in final_layer.getFeatures())
total_kota = sum(f[POPULATION_FIELD] for f in kel_layer.getFeatures())
total_area = sum(f["CATCH_CATCH_KM2"] or 0 for f in final_layer.getFeatures())

print(f"\nTotal populasi tercatchment : {total_pop:,.0f}")
print(f"Total luas catchment (km2)  : {total_area:.2f}")
print(f"% dari penduduk Kota Bandung: {total_pop / total_kota * 100:.1f}%")