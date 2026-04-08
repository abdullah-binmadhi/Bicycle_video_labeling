import re

with open('desktop-app/src/renderer.js', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Globalize defaultClasses
match = r'''    // Ensure all target classes are registered
    const defaultClasses = \['''

sub = '''    // Ensure all target classes are registered
    window.defaultClasses = window.defaultClasses || ['''

content = re.sub(match, sub, content)

# 2. Change references to window.defaultClasses inside renderLegend
content = content.replace("defaultClasses.forEach(cls => window.registerSurface(cls));", "window.defaultClasses.forEach(cls => window.registerSurface(cls));")
content = content.replace("if (defaultClasses.includes(className)) {", "if (window.defaultClasses.includes(className)) {")

# 3. Change reference inside renderDistanceFilter
content = content.replace("const surfaceLabels = defaultClasses.filter", "const surfaceLabels = window.defaultClasses.filter")


# 4. Declare window.defaultClasses globally at the top
top_insert = '''window.defaultClasses = ["0 - bicycle", "1 - potholes", "2 - manhole", "3 - water_puddle", "4 - uneven_surface", "5 - speed_bump", "6 - drain", "7 - crack", "8 - gravel", "9 - sand", "10 - mud", "11 - wet_leaves", "12 - dry_leaves", "13 - branches", "14 - ice", "15 - snow", "16 - glass", "17 - metal_plate", "18 - rail_tracks", "19 - cobblestone", "20 - brick_paving", "21 - concrete_pavers", "22 - tree_root", "23 - painted_lines", "24 - road_marking", "25 - crosswalk", "26 - pedestrian", "27 - dog", "28 - cat", "29 - squirrel", "30 - car", "31 - motorcycle", "32 - truck", "33 - bus", "34 - scooter", "35 - e-scooter", "36 - traffic_cone", "37 - bollard", "38 - construction_barrier", "39 - fallen_tree", "40 - debris", "41 - plastic_bag", "42 - trash_can", "43 - standing_water", "44 - oil_spill", "45 - smooth_asphalt", "46 - rough_asphalt", "47 - grate", "48 - tactile_paving", "49 - curb", "50 - shadow", "51 - street_light", "52 - traffic_light", "53 - stop_sign", "54 - yield_sign", "55 - speed_limit_sign", "56 - bus_stop", "57 - train_station", "58 - parked_car", "59 - moving_car", "60 - turning_car", "61 - reversing_car", "62 - emergency_vehicle", "63 - construction_vehicle", "64 - farm_vehicle", "65 - delivery_truck", "66 - garbage_truck", "67 - street_sweeper", "68 - snow_plow", "69 - tow_truck", "70 - flatbed_truck", "71 - semi_truck", "72 - box_truck", "73 - pickup_truck", "74 - van", "75 - minivan", "76 - suv", "77 - jeep", "78 - crossover", "79 - sedan", "80 - coupe", "81 - convertible", "82 - hatchback", "83 - station_wagon", "84 - sports_car", "85 - luxury_car", "86 - classic_car", "87 - antique_car", "88 - muscle_car", "89 - electric_car", "90 - hybrid_car", "91 - diesel_car", "92 - gas_car", "93 - hydrogen_car", "94 - fuel_cell_car", "95 - solar_car", "96 - flying_car", "97 - hover_car", "98 - submarine_car", "99 - boat_car", "100 - dirt_road", "101 - macadam", "102 - grassy_path", "103 - wood_planks", "104 - metal_grating", "105 - paved_path", "106 - unpaved_path", "107 - pothole_cluster", "108 - alligator_cracking", "109 - longitudinal_cracks", "110 - transverse_cracks", "111 - block_cracking", "112 - edge_cracking", "113 - rutting", "114 - shoving", "115 - corrugation", "116 - bleeding", "117 - polished_aggregate", "118 - pumping", "119 - raveling", "120 - stripping", "121 - delamination", "122 - patch", "123 - traverse_speed_bump", "124 - rubber_speed_bump", "125 - concrete_speed_bump", "126 - asphalt_speed_bump", "127 - wide_speed_bump", "128 - narrow_speed_bump", "129 - rumble_strips", "130 - speed_cushion", "131 - speed_table", "132 - bycicle_lane", "133 - bicycle_lane", "134 - asphalt"];\n'''

content = top_insert + content

# Also, remove the redundant local declaration inside renderLegend replacing it completely if needed, but window.defaultClasses = window.defaultClasses || [ ...] is safe.

with open('desktop-app/src/renderer.js', 'w', encoding='utf-8') as f:
    f.write(content)

