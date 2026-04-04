import json
import os

base_classes = [
    "bicycle", "potholes", "manhole", "water_puddle", "uneven_surface", "speed_bump", "drain", "crack", 
    "gravel", "sand", "mud", "wet_leaves", "dry_leaves", "branches", "ice", "snow", "glass", "metal_plate", 
    "rail_tracks", "cobblestone", "brick_paving", "concrete_pavers", "tree_root", "painted_lines", 
    "road_marking", "crosswalk", "pedestrian", "dog", "cat", "squirrel", "car", "motorcycle", "truck", 
    "bus", "scooter", "e-scooter", "traffic_cone", "bollard", "construction_barrier", "fallen_tree", 
    "debris", "plastic_bag", "trash_can", "standing_water", "oil_spill", "smooth_asphalt", "rough_asphalt", 
    "grate", "tactile_paving", "curb", "shadow", "street_light", "traffic_light", "stop_sign", "yield_sign",
    "speed_limit_sign", "bus_stop", "train_station", "parked_car", "moving_car", "turning_car", 
    "reversing_car", "emergency_vehicle", "construction_vehicle", "farm_vehicle", "delivery_truck", 
    "garbage_truck", "street_sweeper", "snow_plow", "tow_truck", "flatbed_truck", "semi_truck", 
    "box_truck", "pickup_truck", "van", "minivan", "suv", "jeep", "crossover", "sedan", "coupe", 
    "convertible", "hatchback", "station_wagon", "sports_car", "luxury_car", "classic_car", "antique_car", 
    "muscle_car", "electric_car", "hybrid_car", "diesel_car", "gas_car", "hydrogen_car", "fuel_cell_car", 
    "solar_car", "flying_car", "hover_car", "submarine_car", "boat_car",
    "dirt_road", "macadam", "grassy_path", "wood_planks", "metal_grating", "paved_path", "unpaved_path", 
    "pothole_cluster", "alligator_cracking", "longitudinal_cracks", "transverse_cracks", "block_cracking", 
    "edge_cracking", "rutting", "shoving", "corrugation", "bleeding", "polished_aggregate", "pumping", 
    "raveling", "stripping", "delamination", "patch", "traverse_speed_bump", "rubber_speed_bump", 
    "concrete_speed_bump", "asphalt_speed_bump", "wide_speed_bump", "narrow_speed_bump", "rumble_strips", 
    "speed_cushion", "speed_table"
]

labels_dict = {}
for i, cls in enumerate(base_classes):
    key = f"{i} - {cls}"
    name_clean = cls.replace('_', ' ')
    labels_dict[key] = [
        f"a first-person POV video from a bicycle riding near {name_clean}",
        f"looking down at {name_clean} on the street from a bike",
        f"a dashboard camera view of {name_clean} on the road"
    ]

# get the path absolute
script_dir = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(script_dir, "config", "labels.json"), "w") as f:
    json.dump(labels_dict, f, indent=4)

print(f"Generated config/labels.json with {len(labels_dict)} classes.")
