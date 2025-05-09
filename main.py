import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import os
import json

# Set page config
st.set_page_config(
    page_title="Oahu Tourist Sustainability Calculator",
    page_icon="🌴",
    layout="wide"
)

#############################
# UTILITY FUNCTIONS
#############################

def get_score_color(score):
    """Return a color corresponding to a sustainability score"""
    if score >= 80:
        return "#4CAF50"  # Green
    elif score >= 60:
        return "#8BC34A"  # Light Green
    elif score >= 40:
        return "#FFC107"  # Amber
    elif score >= 20:
        return "#FF9800"  # Orange
    else:
        return "#F44336"  # Red

def normalize_value(value, min_val, max_val, reverse=False):
    """Normalize a value to a 0-100 scale"""
    if max_val == min_val:
        return 50  # Default to middle if range is zero
        
    normalized = ((value - min_val) / (max_val - min_val)) * 100
    
    if reverse:
        normalized = 100 - normalized
        
    return max(0, min(100, normalized))

def format_percentage(value):
    """Format a decimal value as a percentage string"""
    return f"{int(value * 100)}%"

def format_carbon(tons):
    """Format carbon footprint value"""
    if tons < 1:
        kg = tons * 1000
        return f"{kg:.0f} kg CO₂e"
    else:
        return f"{tons:.1f} tons CO₂e"

def format_water(gallons):
    """Format water usage value"""
    return f"{gallons:,} gallons"

def get_recommendation_icon(category):
    """Return an icon for a recommendation category"""
    icons = {
        "transportation": "🚗",
        "energy": "⚡",
        "water": "💧",
        "waste": "🗑️",
        "food": "🍲",
        "activities": "🏄‍♀️",
        "accommodation": "🏨",
        "general": "🌱"
    }
    
    return icons.get(category.lower(), "🌴")

#############################
# OAHU SPECIFIC DATA
#############################

def get_oahu_environmental_factors():
    """
    Return a dictionary of Oahu-specific environmental factors
    that influence tourist sustainability calculations.
    """
    factors = {
        'transport': {
            'traffic_congestion_factor': 0.8,  # Higher means worse traffic
            'public_transport_quality': 0.6,   # Higher means better public transport
            'ev_rental_availability': 0.4,     # Availability of EV rentals
            'avg_tourist_travel_distance': 20  # Average daily tourist travel distance in miles
        },
        'accommodation': {
            'hotel_energy_intensity': 20.5,    # kWh per guest night
            'resort_water_intensity': 300,     # Gallons per guest night
            'green_certified_percentage': 0.25, # Percentage of accommodations with green certification
            'avg_ac_usage': 8                  # Average hours of AC use per day
        },
        'energy': {
            'electricity_cost': 0.34,          # $ per kWh (highest in the US)
            'renewable_percentage': 0.35,      # Percentage of grid from renewables
            'fossil_fuel_dependency': 0.65,    # Dependency on imported fossil fuels
            'tourism_energy_factor': 1.5       # Tourist energy use vs. resident (multiplier)
        },
        'water': {
            'freshwater_scarcity': 0.7,        # Higher means more scarce
            'rainfall_variation': 0.7,         # Geographic rainfall variation
            'tourism_water_factor': 2.0,       # Tourist water use vs. resident (multiplier)
            'avg_hotel_consumption': 300       # Average per guest daily consumption (gallons)
        },
        'waste': {
            'limited_landfill_space': 0.8,     # Limited landfill capacity
            'recycling_infrastructure': 0.5,   # Quality of recycling infrastructure
            'marine_debris_impact': 0.9,       # Impact of waste on marine environment
            'tourism_waste_factor': 1.8        # Tourist waste vs. resident (multiplier)
        },
        'food': {
            'import_dependency': 0.85,         # Percentage of food imported
            'local_agriculture_capacity': 0.3, # Capacity for local agriculture
            'fishing_sustainability': 0.6,     # Sustainability of local fishing
            'tourist_dining_impact': 1.6       # Tourist dining impact vs. resident (multiplier)
        },
        'activities': {
            'reef_vulnerability': 0.8,         # Vulnerability of coral reefs
            'trail_erosion_factor': 0.7,       # Impact of hiking on trails
            'wildlife_disturbance': 0.6,       # Impact on local wildlife
            'marine_activity_impact': 0.75     # Impact of water activities on marine ecosystems
        },
        'carbon': {
            'island_multiplier': 1.2,          # Island context multiplier for carbon emissions
            'tourism_impact': 1.5,             # Impact of tourism activities on carbon emissions
            'flight_emissions_factor': 0.2,    # Tons CO2 per 1000 miles flown
            'avg_tourist_emissions': 3.2       # Average carbon footprint (tons/tourist/week)
        }
    }
    
    return factors

def get_oahu_tourist_resources():
    """
    Return a dictionary of Oahu-specific educational resources
    related to sustainable tourism.
    """
    resources = {
        "Sustainable Accommodations": [
            {
                "name": "Hawaii Green Business Program",
                "description": "Directory of hotels and accommodations certified for their sustainable practices in Hawaii.",
                "url": "https://greenbusiness.hawaii.gov/"
            },
            {
                "name": "Green Hotels Association",
                "description": "Information on eco-friendly accommodations and sustainable hotel practices in Hawaii.",
                "url": "https://www.greenhotels.com/"
            }
        ],
        "Responsible Transportation": [
            {
                "name": "Biki Bikeshare",
                "description": "Honolulu's bikeshare program offering an eco-friendly way to explore urban Oahu.",
                "url": "https://gobiki.org/"
            },
            {
                "name": "TheBus - Oahu Transit Services",
                "description": "Information about Honolulu's public bus system routes and schedules for tourists.",
                "url": "http://www.thebus.org/"
            },
            {
                "name": "Sustainable Transportation Guide",
                "description": "Guide to low-impact transportation options around the island.",
                "url": "https://www.gohawaii.com/islands/oahu/travel-tips"
            }
        ],
        "Eco-Friendly Activities": [
            {
                "name": "Hawaii Ecotourism Association",
                "description": "Directory of certified tour operators committed to sustainable practices in Hawaii.",
                "url": "https://www.hawaiiecotourism.org/"
            },
            {
                "name": "Sustainable Coastlines Hawaii",
                "description": "Organizes beach cleanups that tourists can join and provides education about marine conservation.",
                "url": "https://www.sustainablecoastlineshawaii.org/"
            },
            {
                "name": "Hawaii Wildlife Fund",
                "description": "Information on responsible wildlife viewing and conservation efforts tourists can support.",
                "url": "https://www.wildhawaii.org/"
            }
        ],
        "Responsible Dining": [
            {
                "name": "Slow Food Oahu",
                "description": "Guide to restaurants and markets featuring local, sustainable food options.",
                "url": "https://www.slowfoodoahu.org/"
            },
            {
                "name": "Hawaii Farm Bureau",
                "description": "Information on farmers markets where tourists can purchase local produce.",
                "url": "https://hfbf.org/"
            },
            {
                "name": "Seafood Watch Hawaii",
                "description": "Guide to sustainable seafood choices specific to Hawaii.",
                "url": "https://www.seafoodwatch.org/"
            }
        ],
        "Conservation Programs": [
            {
                "name": "Malama Hawaii Program",
                "description": "Volunteer opportunities for tourists to give back through conservation activities during their stay.",
                "url": "https://www.gohawaii.com/malama"
            },
            {
                "name": "Hawaii Conservation Alliance",
                "description": "Information on protected areas and conservation efforts tourists can support.",
                "url": "https://www.hawaiiconservation.org/"
            },
            {
                "name": "Coral Reef Alliance Hawaii",
                "description": "Educational resources on protecting Hawaii's coral reefs during tourist activities.",
                "url": "https://coral.org/where-we-work/hawaii/"
            }
        ],
        "Cultural Sustainability": [
            {
                "name": "Hawaii Tourism Authority - Responsible Tourism",
                "description": "Guidelines for respectful and sustainable tourism that honors Hawaiian culture.",
                "url": "https://www.hawaiitourismauthority.org/responsible-tourism/"
            },
            {
                "name": "Native Hawaiian Hospitality Association",
                "description": "Resources on culturally responsible tourism practices.",
                "url": "https://www.nahha.com/"
            }
        ],
        "Zero Waste Travel": [
            {
                "name": "Zero Waste Oahu",
                "description": "Tips and locations for reducing waste during your vacation on Oahu.",
                "url": "https://www.zerowasteoahu.org/"
            },
            {
                "name": "Kokua Hawaii Foundation",
                "description": "Educational resources on reducing plastic use during beach and ocean activities.",
                "url": "https://kokuahawaiifoundation.org/"
            }
        ]
    }
    
    return resources

#############################
# TOURIST SUSTAINABILITY CALCULATOR
#############################

def calculate_impact(user_data):
    """
    Calculate environmental impact based on tourist inputs and Oahu-specific factors.
    Returns dictionary with impact scores and detailed metrics.
    """
    # Get Oahu-specific environmental factors
    oahu_factors = get_oahu_environmental_factors()
    
    # Calculate transport impact
    transport_score = calculate_transport_impact(user_data, oahu_factors)
    
    # Calculate accommodation impact
    accommodation_score = calculate_accommodation_impact(user_data, oahu_factors)
    
    # Calculate activities impact
    activities_score = calculate_activities_impact(user_data, oahu_factors)
    
    # Calculate water impact
    water_score = calculate_water_impact(user_data, oahu_factors)
    
    # Calculate waste impact
    waste_score = calculate_waste_impact(user_data, oahu_factors)
    
    # Calculate food impact
    food_score = calculate_food_impact(user_data, oahu_factors)
    
    # Calculate carbon footprint (in tons of CO2 for the trip)
    carbon_footprint = calculate_carbon_footprint(user_data, oahu_factors)
    
    # Calculate water usage (in gallons per day)
    water_usage = calculate_water_usage(user_data, oahu_factors)
    
    # Calculate waste generation (in pounds per day)
    waste_generation = calculate_waste_generation(user_data, oahu_factors)
    
    # Calculate overall score (weighted average)
    weights = {
        'transport': 0.2,
        'accommodation': 0.2,
        'activities': 0.15,
        'water': 0.15,
        'waste': 0.15,
        'food': 0.15
    }
    
    overall_score = (
        transport_score * weights['transport'] +
        accommodation_score * weights['accommodation'] +
        activities_score * weights['activities'] +
        water_score * weights['water'] +
        waste_score * weights['waste'] +
        food_score * weights['food']
    )
    
    # Round to nearest integer
    overall_score = round(overall_score)
    
    # Compile results
    results = {
        'overall_score': overall_score,
        'transport_score': transport_score,
        'accommodation_score': accommodation_score,
        'activities_score': activities_score,
        'water_score': water_score,
        'waste_score': waste_score,
        'food_score': food_score,
        'carbon_footprint': carbon_footprint,
        'water_usage': water_usage,
        'waste_generation': waste_generation,
        'impact_breakdown': {
            'transport': weights['transport'] * transport_score / overall_score if overall_score > 0 else 0,
            'accommodation': weights['accommodation'] * accommodation_score / overall_score if overall_score > 0 else 0,
            'activities': weights['activities'] * activities_score / overall_score if overall_score > 0 else 0,
            'water': weights['water'] * water_score / overall_score if overall_score > 0 else 0,
            'waste': weights['waste'] * waste_score / overall_score if overall_score > 0 else 0,
            'food': weights['food'] * food_score / overall_score if overall_score > 0 else 0
        }
    }
    
    return results

def calculate_transport_impact(user_data, oahu_factors):
    """Calculate transport-related environmental impact score (0-100)"""
    # Higher score = more sustainable
    base_score = 100
    
    # Flight impact - longer flights = more emissions
    flight_distance = user_data['flight_distance']
    flight_impact = flight_distance * 0.02  # More miles = bigger impact
    base_score -= flight_impact
    
    # Local transport impacts
    local_transport = user_data['local_transport']
    
    # Transport type multipliers (lower is better - less emissions)
    transport_multipliers = {
        "Rental EV": 0.3,
        "Rental hybrid": 0.6,
        "Rental economy car": 1.0,
        "Rental SUV/large vehicle": 2.0,
        "Public transportation/shuttle": 0.4,
        "Mostly walking/biking": 0.1,
        "Rideshare/taxi": 0.8
    }
    
    # Calculate local transport impact
    daily_miles = oahu_factors['transport']['avg_tourist_travel_distance']
    transport_impact = daily_miles * transport_multipliers[local_transport] * 0.15
    base_score -= transport_impact
    
    # Adjust for Oahu-specific factors
    if local_transport in ["Public transportation/shuttle", "Mostly walking/biking"]:
        # Public transport quality factor (higher quality = better score)
        base_score += 10 * oahu_factors['transport']['public_transport_quality']
    elif local_transport == "Rental EV":
        # EV rental availability factor (lower availability = decreased score)
        base_score -= 5 * (1 - oahu_factors['transport']['ev_rental_availability'])
    
    # Tourism-specific congestion impact
    congestion_impact = 5 * oahu_factors['transport']['traffic_congestion_factor']
    base_score -= congestion_impact
    
    # Ensure score is within bounds
    return max(0, min(100, base_score))

def calculate_accommodation_impact(user_data, oahu_factors):
    """Calculate accommodation-related environmental impact score (0-100)"""
    # Higher score = more sustainable
    base_score = 100
    
    # Accommodation type has different baseline impacts
    accommodation_type = user_data['accommodation_type']
    
    # Accommodation impact multipliers (lower is better - less impact)
    accommodation_multipliers = {
        "Eco-certified hotel/resort": 0.5,
        "Standard hotel/resort": 1.0,
        "Luxury resort": 1.5,
        "Vacation rental": 0.8,
        "Hostel/budget accommodation": 0.6,
        "Camping/outdoor lodging": 0.3
    }
    
    # Base impact from accommodation type
    accommodation_impact = 30 * accommodation_multipliers[accommodation_type]
    base_score -= accommodation_impact
    
    # AC usage impact
    ac_usage = user_data['ac_usage']
    ac_impact = ac_usage * 2  # More hours = bigger impact
    base_score -= ac_impact
    
    # Water conservation practices
    water_conservation = user_data['water_conservation']
    water_practices_impact = 15 * (1 - water_conservation)  # Higher conservation = less impact
    base_score -= water_practices_impact
    
    # Linen reuse
    linen_reuse = user_data['linen_reuse']
    if linen_reuse:
        base_score += 10
    
    # Adjust for Oahu-specific factors
    energy_factor = oahu_factors['energy']['tourism_energy_factor']
    base_score -= 5 * (energy_factor - 1)  # Adjust for higher tourist energy use
    
    # Green certification percentage factor
    green_cert_adjustment = 5 * oahu_factors['accommodation']['green_certified_percentage']
    base_score += green_cert_adjustment
    
    # Ensure score is within bounds
    return max(0, min(100, base_score))

def calculate_activities_impact(user_data, oahu_factors):
    """Calculate activities-related environmental impact score (0-100)"""
    # Higher score = more sustainable
    base_score = 100
    
    # Activity types
    activities = user_data['activities']
    
    # Activity impact multipliers (lower is better - less impact)
    activity_impacts = {
        "Snorkeling/scuba on coral reefs": 15 * oahu_factors['activities']['reef_vulnerability'],
        "Motorized water sports (jet ski, motorboats)": 25,
        "Hiking on maintained trails": 5 * oahu_factors['activities']['trail_erosion_factor'],
        "Off-trail hiking/exploration": 20 * oahu_factors['activities']['trail_erosion_factor'],
        "Wildlife viewing tours": 10 * oahu_factors['activities']['wildlife_disturbance'],
        "ATV/off-road vehicle tours": 30,
        "Shopping/dining": 10,
        "Cultural sites/museums": 5,
        "Beach relaxation": 5,
        "Surfing/paddleboarding": 5 * oahu_factors['activities']['marine_activity_impact']
    }
    
    # Calculate impact from selected activities
    total_activity_impact = 0
    for activity in activities:
        total_activity_impact += activity_impacts.get(activity, 10)
    
    # Normalize by number of activities
    if activities:
        avg_activity_impact = total_activity_impact / len(activities)
        base_score -= avg_activity_impact
    
    # Eco-tour selection
    eco_tours = user_data['eco_tours']
    if eco_tours:
        base_score += 15
    
    # Wildlife distance
    wildlife_distance = user_data['wildlife_distance']
    if wildlife_distance:
        base_score += 10
    else:
        base_score -= 10 * oahu_factors['activities']['wildlife_disturbance']
    
    # Reef-safe sunscreen
    reef_safe = user_data['reef_safe']
    if reef_safe:
        base_score += 15
    else:
        base_score -= 15 * oahu_factors['activities']['reef_vulnerability']
    
    # Ensure score is within bounds
    return max(0, min(100, base_score))

def calculate_water_impact(user_data, oahu_factors):
    """Calculate water-related environmental impact score (0-100)"""
    # Higher score = more sustainable
    base_score = 100
    
    # Shower length has direct impact
    shower_length = user_data['shower_length']
    shower_impact = shower_length * 2.5  # Longer shower = bigger impact
    base_score -= shower_impact
    
    # Water conservation practices at accommodation
    water_conservation = user_data['water_conservation']
    conservation_impact = 20 * (1 - water_conservation)  # Less conservation = bigger impact
    base_score -= conservation_impact
    
    # Linen reuse reduces water impact
    linen_reuse = user_data['linen_reuse']
    if linen_reuse:
        base_score += 15
    else:
        base_score -= 10
    
    # Swimming pool usage
    pool_usage = user_data['pool_usage']
    pool_impact = pool_usage * 3  # More pool time = bigger impact
    base_score -= pool_impact
    
    # Adjust for Oahu-specific factors
    water_scarcity = oahu_factors['water']['freshwater_scarcity']
    scarcity_impact = 10 * water_scarcity  # Higher scarcity = bigger impact
    base_score -= scarcity_impact
    
    # Tourism water factor adjustment
    tourism_water_factor = oahu_factors['water']['tourism_water_factor']
    base_score -= 5 * (tourism_water_factor - 1)  # Adjust for higher tourist water use
    
    # Ensure score is within bounds
    return max(0, min(100, base_score))

def calculate_waste_impact(user_data, oahu_factors):
    """Calculate waste-related environmental impact score (0-100)"""
    # Higher score = more sustainable
    base_score = 100
    
    # Reusable water bottle usage reduces waste
    reusable_bottle = user_data['reusable_bottle']
    if reusable_bottle:
        base_score += 15
    else:
        base_score -= 15
    
    # Reusable bag usage reduces waste
    reusable_bag = user_data['reusable_bag']
    if reusable_bag:
        base_score += 10
    else:
        base_score -= 10
    
    # Refuse single-use items reduces waste
    refuse_single_use = user_data['refuse_single_use']
    single_use_impact = 20 * (1 - refuse_single_use)  # Less refusal = bigger impact
    base_score -= single_use_impact
    
    # Beach/trail cleanup participation
    cleanup_participation = user_data['cleanup_participation']
    if cleanup_participation:
        base_score += 20
    
    # Adjust for Oahu-specific factors
    landfill_factor = oahu_factors['waste']['limited_landfill_space']
    landfill_impact = 10 * landfill_factor  # More limited space = bigger impact
    base_score -= landfill_impact
    
    # Marine debris impact
    marine_factor = oahu_factors['waste']['marine_debris_impact']
    marine_impact = 10 * marine_factor  # Higher marine impact = bigger impact
    base_score -= marine_impact
    
    # Tourism waste factor adjustment
    tourism_waste_factor = oahu_factors['waste']['tourism_waste_factor']
    base_score -= 5 * (tourism_waste_factor - 1)  # Adjust for higher tourist waste generation
    
    # Ensure score is within bounds
    return max(0, min(100, base_score))

def calculate_food_impact(user_data, oahu_factors):
    """Calculate food-related environmental impact score (0-100)"""
    # Higher score = more sustainable
    base_score = 100
    
    # Local food consumption reduces impact
    local_food = user_data['local_food']
    local_food_impact = 25 * (1 - local_food)  # Less local food = bigger impact
    base_score -= local_food_impact
    
    # Plant-based meals reduce impact
    plant_based = user_data['plant_based']
    plant_based_impact = 20 * (1 - plant_based)  # Fewer plant-based meals = bigger impact
    base_score -= plant_based_impact
    
    # Seafood sustainability
    seafood_sustainable = user_data['seafood_sustainable']
    if seafood_sustainable:
        base_score += 15
    else:
        base_score -= 15
    
    # Food waste reduction
    food_waste = user_data['food_waste']
    food_waste_impact = 15 * (1 - food_waste)  # Less reduction = bigger impact
    base_score -= food_waste_impact
    
    # Adjust for Oahu-specific factors
    import_dependency = oahu_factors['food']['import_dependency']
    import_impact = 10 * import_dependency  # Higher import dependency = bigger impact
    base_score -= import_impact
    
    # Local agriculture capacity
    ag_capacity = oahu_factors['food']['local_agriculture_capacity']
    ag_impact = 10 * (1 - ag_capacity)  # Lower capacity = bigger impact
    base_score -= ag_impact
    
    # Tourism dining impact factor
    tourism_food_factor = oahu_factors['food']['tourist_dining_impact']
    base_score -= 5 * (tourism_food_factor - 1)  # Adjust for higher tourist food impact
    
    # Ensure score is within bounds
    return max(0, min(100, base_score))

def calculate_carbon_footprint(user_data, oahu_factors):
    """Calculate carbon footprint (in tons of CO2) for the trip"""
    carbon_factors = oahu_factors['carbon']
    
    # Calculate flight emissions
    flight_distance = user_data['flight_distance']
    flight_emissions = flight_distance * carbon_factors['flight_emissions_factor'] / 1000
    
    # Calculate local transport emissions
    local_transport = user_data['local_transport']
    days = user_data['duration']
    daily_miles = oahu_factors['transport']['avg_tourist_travel_distance']
    
    # Transport type carbon factors (tons CO2 per mile)
    transport_carbon = {
        "Rental EV": 0.0001,
        "Rental hybrid": 0.0002,
        "Rental economy car": 0.0004,
        "Rental SUV/large vehicle": 0.0007,
        "Public transportation/shuttle": 0.0001,
        "Mostly walking/biking": 0.00001,
        "Rideshare/taxi": 0.0003
    }
    
    local_emissions = daily_miles * transport_carbon[local_transport] * days
    
    # Calculate accommodation emissions
    accommodation_type = user_data['accommodation_type']
    
    # Accommodation carbon factors (tons CO2 per night)
    accommodation_carbon = {
        "Eco-certified hotel/resort": 0.01,
        "Standard hotel/resort": 0.03,
        "Luxury resort": 0.06,
        "Vacation rental": 0.02,
        "Hostel/budget accommodation": 0.01,
        "Camping/outdoor lodging": 0.005
    }
    
    accommodation_emissions = accommodation_carbon[accommodation_type] * days
    
    # Calculate food emissions
    plant_based = user_data['plant_based']
    local_food = user_data['local_food']
    
    # Base food emissions per day
    food_emissions_base = 0.01
    
    # Adjust for diet and local food
    food_adjustment = 1.0
    if plant_based < 0.3:  # Mostly meat-based
        food_adjustment = 2.0
    elif plant_based < 0.7:  # Mixed diet
        food_adjustment = 1.5
    else:  # Mostly plant-based
        food_adjustment = 0.8
    
    # Local food reduces carbon footprint
    food_adjustment *= (1.5 - local_food * 0.5)
    
    food_emissions = food_emissions_base * food_adjustment * days
    
    # Calculate activities emissions
    activities = user_data['activities']
    
    # Activity carbon factors (tons CO2 per activity)
    activity_carbon = {
        "Snorkeling/scuba on coral reefs": 0.005,
        "Motorized water sports (jet ski, motorboats)": 0.03,
        "Hiking on maintained trails": 0.001,
        "Off-trail hiking/exploration": 0.001,
        "Wildlife viewing tours": 0.01,
        "ATV/off-road vehicle tours": 0.04,
        "Shopping/dining": 0.005,
        "Cultural sites/museums": 0.002,
        "Beach relaxation": 0.001,
        "Surfing/paddleboarding": 0.001
    }
    
    activities_emissions = sum(activity_carbon.get(activity, 0.01) for activity in activities) * (days / 3)  # Assuming not all activities every day
    
    # Combine all emissions
    total_emissions = flight_emissions + local_emissions + accommodation_emissions + food_emissions + activities_emissions
    
    # Apply island context multiplier
    total_emissions *= carbon_factors['island_multiplier']
    
    return total_emissions

def calculate_water_usage(user_data, oahu_factors):
    """Calculate water usage (in gallons per day)"""
    water_factors = oahu_factors['water']
    
    # Base water usage from accommodation type
    accommodation_type = user_data['accommodation_type']
    
    # Accommodation water factors (gallons per person per day)
    accommodation_water = {
        "Eco-certified hotel/resort": 80,
        "Standard hotel/resort": 150,
        "Luxury resort": 250,
        "Vacation rental": 100,
        "Hostel/budget accommodation": 70,
        "Camping/outdoor lodging": 30
    }
    
    base_water = accommodation_water[accommodation_type]
    
    # Shower water usage
    shower_length = user_data['shower_length']
    shower_water = shower_length * 2.5 * 10  # 2.5 gallons per minute * minutes
    
    # Pool usage water impact
    pool_usage = user_data['pool_usage']
    pool_water = pool_usage * 15  # Estimated gallons per hour of pool time
    
    # Water conservation practices
    water_conservation = user_data['water_conservation']
    conservation_factor = 1 - (water_conservation * 0.3)  # Up to 30% reduction
    
    # Linen reuse water savings
    linen_reuse = user_data['linen_reuse']
    linen_factor = 0.9 if linen_reuse else 1.0  # 10% savings if reusing linens
    
    # Calculate total water usage
    total_water = (base_water + shower_water + pool_water) * conservation_factor * linen_factor
    
    # Apply tourism water factor
    total_water *= water_factors['tourism_water_factor']
    
    return round(total_water)

def calculate_waste_generation(user_data, oahu_factors):
    """Calculate waste generation (in pounds per day)"""
    waste_factors = oahu_factors['waste']
    
    # Base waste from tourist activities
    base_waste = 4.0  # Pounds per day (EPA average)
    
    # Adjust for reusable items
    reusable_bottle = user_data['reusable_bottle']
    bottle_factor = 0.8 if reusable_bottle else 1.2  # 20% reduction or 20% increase
    
    reusable_bag = user_data['reusable_bag']
    bag_factor = 0.9 if reusable_bag else 1.1  # 10% reduction or 10% increase
    
    # Single-use items refusal
    refuse_single_use = user_data['refuse_single_use']
    single_use_factor = 1 - (refuse_single_use * 0.4)  # Up to 40% reduction
    
    # Beach/trail cleanup participation
    cleanup_participation = user_data['cleanup_participation']
    cleanup_factor = 0.9 if cleanup_participation else 1.0  # 10% reduction if participating
    
    # Food waste reduction
    food_waste = user_data['food_waste']
    food_waste_factor = 1 - (food_waste * 0.3)  # Up to 30% reduction
    
    # Calculate total waste generation
    total_waste = base_waste * bottle_factor * bag_factor * single_use_factor * cleanup_factor * food_waste_factor
    
    # Apply tourism waste factor
    total_waste *= waste_factors['tourism_waste_factor']
    
    return round(total_waste, 1)

def get_recommendations(user_data, results):
    """Generate personalized sustainability recommendations based on user data and results"""
    recommendations = []
    
    # Transport recommendations
    if user_data['local_transport'] in ["Rental SUV/large vehicle", "Rental economy car"]:
        recommendations.append({
            "category": "transportation",
            "title": "Consider sustainable transportation",
            "description": "Opt for Oahu's reliable public bus system (TheBus) or the Waikiki Trolley for getting around tourist areas. You can also rent bikes or use the Biki bikeshare system in Honolulu."
        })
    
    if user_data['flight_distance'] > 3000:
        recommendations.append({
            "category": "transportation",
            "title": "Offset your flight emissions",
            "description": "Consider purchasing carbon offsets for your long-distance flight to Hawaii. Many airlines offer this option, or you can use services like Cool Effect or Sustainable Travel International."
        })
    
    # Accommodation recommendations
    if user_data['accommodation_type'] in ["Standard hotel/resort", "Luxury resort"] and user_data['ac_usage'] > 6:
        recommendations.append({
            "category": "accommodation",
            "title": "Reduce AC usage",
            "description": "Hawaii's natural trade winds provide excellent ventilation. Try using ceiling fans and opening windows instead of running AC constantly. When using AC, set it to 76-78°F (24-26°C)."
        })
    
    if not user_data['linen_reuse']:
        recommendations.append({
            "category": "accommodation",
            "title": "Reuse hotel towels and linens",
            "description": "Let your hotel know you don't need daily linen changes. This saves water and energy, which are both precious resources on an island."
        })
    
    # Water recommendations
    if user_data['shower_length'] > 5:
        recommendations.append({
            "category": "water",
            "title": "Take shorter showers",
            "description": "Fresh water is a limited resource on Oahu. Try to limit showers to 5 minutes or less, especially after beach activities when a quick rinse is sufficient."
        })
    
    if user_data['pool_usage'] > 3:
        recommendations.append({
            "category": "water",
            "title": "Balance pool and ocean time",
            "description": "While resort pools are enjoyable, consider spending more time in the ocean. Hawaii's beaches offer natural swimming opportunities without the water and chemical use of pools."
        })
    
    # Waste recommendations
    if not user_data['reusable_bottle']:
        recommendations.append({
            "category": "waste",
            "title": "Bring a reusable water bottle",
            "description": "Plastic waste is a significant issue on Oahu, with limited landfill space. Carry a reusable water bottle - Hawaii tap water is clean and safe to drink."
        })
    
    if not user_data['cleanup_participation']:
        recommendations.append({
            "category": "waste",
            "title": "Join a beach cleanup",
            "description": "Consider participating in a beach cleanup through organizations like Sustainable Coastlines Hawaii or the Surfrider Foundation. This is a great way to give back to the places you're enjoying."
        })
    
    # Food recommendations
    if user_data['local_food'] < 0.5:
        recommendations.append({
            "category": "food",
            "title": "Eat more local food",
            "description": "Over 85% of Hawaii's food is imported. Support local farmers and reduce carbon emissions by choosing restaurants that serve locally-sourced ingredients, and shopping at farmers markets."
        })
    
    if not user_data['seafood_sustainable']:
        recommendations.append({
            "category": "food",
            "title": "Choose sustainable seafood",
            "description": "Hawaii's marine ecosystems are fragile. When ordering seafood, ask about sustainable options or check the Seafood Watch app to make ocean-friendly choices."
        })
    
    # Activities recommendations
    if "Motorized water sports (jet ski, motorboats)" in user_data['activities'] or "ATV/off-road vehicle tours" in user_data['activities']:
        recommendations.append({
            "category": "activities",
            "title": "Choose low-impact activities",
            "description": "Consider eco-friendly alternatives like kayaking, paddleboarding, or electric boat tours that minimize noise pollution and marine ecosystem disruption."
        })
    
    if "Snorkeling/scuba on coral reefs" in user_data['activities'] and not user_data['reef_safe']:
        recommendations.append({
            "category": "activities",
            "title": "Use reef-safe sunscreen",
            "description": "Hawaii has banned sunscreens containing oxybenzone and octinoxate because they damage coral reefs. Look for mineral-based sunscreens with zinc oxide or titanium dioxide."
        })
    
    if "Wildlife viewing tours" in user_data['activities'] and not user_data['wildlife_distance']:
        recommendations.append({
            "category": "activities",
            "title": "Maintain distance from wildlife",
            "description": "Hawaii law requires keeping at least 50 feet from sea turtles, monk seals, and other protected species. Never touch or chase wildlife - observe respectfully from a distance."
        })
    
    # Add general recommendations if we have few specific ones
    if len(recommendations) < 3:
        recommendations.append({
            "category": "general",
            "title": "Support Hawaiian conservation efforts",
            "description": "Consider donating to local conservation organizations like The Nature Conservancy Hawaii or volunteering with a Malama Hawaii program during your stay."
        })
        
        recommendations.append({
            "category": "general",
            "title": "Learn about Hawaiian culture",
            "description": "Understanding Hawaiian culture and values like 'malama 'aina' (caring for the land) can enhance your visit and inspire more sustainable choices. Visit cultural sites respectfully."
        })
    
    return recommendations

#############################
# UI COMPONENTS
#############################

def display_header():
    """Display the application header"""
    col1, col2 = st.columns([1, 3])
    
    with col1:
        # Using an emoji instead of an external image to avoid image loading issues
        st.markdown("# 🌴")
    
    with col2:
        st.title("Oahu Tourist Sustainability Calculator 🏝️")
        st.markdown("""
        Measure and improve your environmental impact while vacationing in paradise.
        Make your visit to Oahu more sustainable with personalized recommendations.
        """)

def display_sustainability_score(score, category=None):
    """Display a sustainability score with visual indicator"""
    label = category if category else "Overall Sustainability Score"
    
    # Get color based on score
    color = get_score_color(score)
    
    # Create the score display
    html_content = f"""
    <div style="text-align: center; margin-bottom: 10px;">
        <p style="margin-bottom: 5px; font-weight: bold;">{label}</p>
        <div style="position: relative; width: 150px; height: 150px; border-radius: 50%; background: #f0f0f0; margin: 0 auto;">
            <div style="position: absolute; top: 5px; left: 5px; width: 140px; height: 140px; border-radius: 50%; background: {color}; display: flex; justify-content: center; align-items: center;">
                <span style="font-size: 36px; font-weight: bold; color: white;">{score}</span>
            </div>
        </div>
    </div>
    """
    
    st.markdown(html_content, unsafe_allow_html=True)

def display_impact_metrics(results):
    """Display key environmental impact metrics"""
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "Carbon Footprint", 
            format_carbon(results['carbon_footprint']),
            help="Estimated carbon emissions from your trip, including flights, local transport, accommodation, food, and activities."
        )
    
    with col2:
        st.metric(
            "Water Usage", 
            format_water(results['water_usage']) + " per day",
            help="Estimated daily water consumption based on your accommodation, activities, and practices."
        )
    
    with col3:
        st.metric(
            "Waste Generation", 
            f"{results['waste_generation']} lbs per day",
            help="Estimated daily waste generated based on your consumption patterns and reuse practices."
        )

def display_radar_chart(results):
    """Display a radar chart of sustainability categories"""
    categories = [
        'Transport', 'Accommodation', 'Activities', 
        'Water Use', 'Waste', 'Food'
    ]
    
    values = [
        results['transport_score'],
        results['accommodation_score'],
        results['activities_score'],
        results['water_score'],
        results['waste_score'],
        results['food_score']
    ]
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatterpolar(
        r=values,
        theta=categories,
        fill='toself',
        fillcolor='rgba(76, 175, 80, 0.3)',
        line=dict(color='#4CAF50')
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100]
            )
        ),
        showlegend=False,
        height=350,
        margin=dict(l=40, r=40, b=40, t=40)
    )
    
    st.plotly_chart(fig, use_container_width=True)

def display_breakdown_chart(results):
    """Display a pie chart of impact breakdown"""
    impact = results['impact_breakdown']
    
    labels = [
        'Transportation', 'Accommodation', 'Activities',
        'Water Use', 'Waste', 'Food'
    ]
    
    values = [
        impact['transport'],
        impact['accommodation'],
        impact['activities'],
        impact['water'],
        impact['waste'],
        impact['food']
    ]
    
    colors = ['#FF9800', '#2196F3', '#9C27B0', '#03A9F4', '#8BC34A', '#FF5722']
    
    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=.4,
        marker=dict(colors=colors)
    )])
    
    fig.update_layout(
        title="Impact Breakdown",
        height=350,
        margin=dict(l=40, r=40, b=40, t=60)
    )
    
    st.plotly_chart(fig, use_container_width=True)

def display_recommendations(recommendations):
    """Display personalized sustainability recommendations"""
    st.subheader("Personalized Recommendations")
    
    for i, rec in enumerate(recommendations[:5]):  # Show top 5 recommendations
        with st.expander(f"{get_recommendation_icon(rec['category'])} {rec['title']}"):
            st.markdown(rec['description'])

def display_resources():
    """Display educational resources for sustainable tourism in Oahu"""
    st.subheader("Sustainable Tourism Resources")
    
    resources = get_oahu_tourist_resources()
    
    tabs = st.tabs(list(resources.keys()))
    
    for i, (category, resource_list) in enumerate(resources.items()):
        with tabs[i]:
            for resource in resource_list:
                st.markdown(f"**[{resource['name']}]({resource['url']})**")
                st.markdown(resource['description'])
                st.markdown("---")

def display_comparison(results):
    """Display comparison to average tourist"""
    col1, col2 = st.columns(2)
    
    # Average tourist values
    avg_carbon = 1.2  # tons for 1-week trip
    avg_water = 250   # gallons per day
    avg_waste = 5.2   # pounds per day
    
    user_carbon = results['carbon_footprint']
    user_water = results['water_usage']
    user_waste = results['waste_generation']
    
    # Carbon comparison
    carbon_diff = ((avg_carbon - user_carbon) / avg_carbon) * 100
    carbon_status = "lower" if carbon_diff > 0 else "higher"
    carbon_color = "normal" if carbon_diff > 0 else "off"
    
    with col1:
        st.metric(
            "Your Carbon vs Average Tourist", 
            format_carbon(user_carbon),
            f"{abs(carbon_diff):.1f}% {carbon_status}",
            delta_color=carbon_color
        )
    
    # Water comparison
    water_diff = ((avg_water - user_water) / avg_water) * 100
    water_status = "lower" if water_diff > 0 else "higher"
    water_color = "normal" if water_diff > 0 else "off"
    
    with col2:
        st.metric(
            "Your Water Use vs Average Tourist", 
            format_water(user_water) + " per day",
            f"{abs(water_diff):.1f}% {water_status}",
            delta_color=water_color
        )
    
    # Waste comparison
    waste_diff = ((avg_waste - user_waste) / avg_waste) * 100
    waste_status = "lower" if waste_diff > 0 else "higher"
    waste_color = "normal" if waste_diff > 0 else "off"
    
    with col1:
        st.metric(
            "Your Waste vs Average Tourist", 
            f"{user_waste} lbs per day",
            f"{abs(waste_diff):.1f}% {waste_status}",
            delta_color=waste_color
        )
    
    # Overall score context
    with col2:
        score_context = ""
        score = results['overall_score']
        
        if score >= 80:
            score_context = "Excellent! You're a sustainable tourism champion."
        elif score >= 60:
            score_context = "Good job! Your vacation has a lower-than-average impact."
        elif score >= 40:
            score_context = "Average impact. Some simple changes could make a big difference."
        else:
            score_context = "Higher impact than most. Check recommendations to improve."
        
        st.info(score_context)

#############################
# INPUT FORM
#############################

def input_form():
    """Create input form for user data collection"""
    with st.form("sustainability_calculator_form"):
        st.subheader("Your Oahu Trip Details")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Trip duration
            duration = st.slider(
                "How many days will you spend in Oahu?",
                min_value=1,
                max_value=30,
                value=7,
                help="Duration of your stay in Oahu"
            )
            
            # Flight distance
            flight_distance = st.slider(
                "Approximate flight distance (miles, one-way)",
                min_value=300,
                max_value=10000,
                value=3000,
                step=100,
                help="Distance of your flight to Hawaii (one-way)"
            )
            
            # Local transportation
            local_transport = st.selectbox(
                "Primary transportation method on Oahu",
                options=[
                    "Rental EV",
                    "Rental hybrid",
                    "Rental economy car",
                    "Rental SUV/large vehicle",
                    "Public transportation/shuttle",
                    "Mostly walking/biking",
                    "Rideshare/taxi"
                ],
                help="How you'll primarily get around during your stay"
            )
            
            # Accommodation
            accommodation_type = st.selectbox(
                "Accommodation type",
                options=[
                    "Eco-certified hotel/resort",
                    "Standard hotel/resort",
                    "Luxury resort",
                    "Vacation rental",
                    "Hostel/budget accommodation",
                    "Camping/outdoor lodging"
                ],
                help="Type of accommodation during your stay"
            )
            
            # AC usage
            ac_usage = st.slider(
                "Average daily AC usage (hours)",
                min_value=0,
                max_value=24,
                value=6,
                help="How many hours you plan to use air conditioning daily"
            )
            
            # Water conservation
            water_conservation = st.slider(
                "Water conservation efforts",
                min_value=0,
                max_value=100,
                value=50,
                format="%d%%",
                help="How much effort you'll make to conserve water (turn off taps, shorter showers, etc.)"
            ) / 100  # Convert to decimal for calculations
        
        with col2:
            # Linen reuse
            linen_reuse = st.checkbox(
                "Will you reuse towels/linens during your stay?",
                value=True,
                help="Reusing towels and linens saves water and energy"
            )
            
            # Reusable bottle
            reusable_bottle = st.checkbox(
                "Will you bring/use a reusable water bottle?",
                value=True,
                help="Using a reusable water bottle reduces plastic waste"
            )
            
            # Reusable bag
            reusable_bag = st.checkbox(
                "Will you bring/use reusable shopping bags?",
                value=True,
                help="Using reusable bags reduces plastic waste"
            )
            
            # Single-use items
            refuse_single_use = st.slider(
                "Refusing single-use items (straws, utensils, etc.)",
                min_value=0,
                max_value=100,
                value=50,
                format="%d%%",
                help="How often you'll decline single-use plastic items"
            ) / 100  # Convert to decimal for calculations
            
            # Beach cleanup
            cleanup_participation = st.checkbox(
                "Planning to participate in a beach/trail cleanup?",
                value=False,
                help="Many organizations offer opportunities to join cleanup efforts"
            )
            
            # Food choices
            plant_based = st.slider(
                "Percentage of plant-based meals",
                min_value=0,
                max_value=100,
                value=40,
                format="%d%%",
                help="Eating more plant-based meals reduces environmental impact"
            ) / 100  # Convert to decimal for calculations
            
            # Local food
            local_food = st.slider(
                "Percentage of local food consumption",
                min_value=0,
                max_value=100,
                value=50,
                format="%d%%",
                help="Choosing locally-grown food reduces carbon emissions from imports"
            ) / 100  # Convert to decimal for calculations
        
        st.subheader("Additional Details")
        
        col3, col4 = st.columns(2)
        
        with col3:
            # Sustainable seafood
            seafood_sustainable = st.checkbox(
                "Will you choose sustainable seafood options?",
                value=True,
                help="Sustainable seafood helps protect marine ecosystems"
            )
            
            # Food waste
            food_waste = st.slider(
                "Food waste reduction efforts",
                min_value=0,
                max_value=100,
                value=70,
                format="%d%%",
                help="Efforts to reduce food waste (finishing meals, taking leftovers, etc.)"
            ) / 100  # Convert to decimal for calculations
            
            # Shower length
            shower_length = st.slider(
                "Average shower length (minutes)",
                min_value=1,
                max_value=30,
                value=8,
                help="Average length of your showers during your stay"
            )
            
            # Pool usage
            pool_usage = st.slider(
                "Average daily pool usage (hours)",
                min_value=0,
                max_value=8,
                value=2,
                help="How many hours you plan to use pools daily"
            )
        
        with col4:
            # Activities
            activities = st.multiselect(
                "Planned activities",
                options=[
                    "Snorkeling/scuba on coral reefs",
                    "Motorized water sports (jet ski, motorboats)",
                    "Hiking on maintained trails",
                    "Off-trail hiking/exploration",
                    "Wildlife viewing tours",
                    "ATV/off-road vehicle tours",
                    "Shopping/dining",
                    "Cultural sites/museums",
                    "Beach relaxation",
                    "Surfing/paddleboarding"
                ],
                default=["Snorkeling/scuba on coral reefs", "Hiking on maintained trails", "Beach relaxation"],
                help="Activities you plan to participate in during your visit"
            )
            
            # Reef-safe sunscreen
            reef_safe = st.checkbox(
                "Will you use reef-safe sunscreen?",
                value=True,
                help="Regular sunscreen contains chemicals harmful to coral reefs"
            )
            
            # Wildlife distance
            wildlife_distance = st.checkbox(
                "Will you maintain appropriate distance from wildlife?",
                value=True,
                help="Keeping proper distance from wildlife reduces disturbance and stress"
            )
            
            # Eco-tour selection
            eco_tours = st.checkbox(
                "Will you choose certified eco-tours when available?",
                value=True,
                help="Certified eco-tours follow sustainable practices that minimize environmental impact"
            )
        
        submit_button = st.form_submit_button("Calculate My Impact")
        
        if submit_button:
            # Compile user data
            user_data = {
                'duration': duration,
                'flight_distance': flight_distance,
                'local_transport': local_transport,
                'accommodation_type': accommodation_type,
                'ac_usage': ac_usage,
                'water_conservation': water_conservation,
                'linen_reuse': linen_reuse,
                'reusable_bottle': reusable_bottle,
                'reusable_bag': reusable_bag,
                'refuse_single_use': refuse_single_use,
                'cleanup_participation': cleanup_participation,
                'plant_based': plant_based,
                'local_food': local_food,
                'seafood_sustainable': seafood_sustainable,
                'food_waste': food_waste,
                'shower_length': shower_length,
                'pool_usage': pool_usage,
                'activities': activities,
                'reef_safe': reef_safe,
                'wildlife_distance': wildlife_distance,
                'eco_tours': eco_tours
            }
            
            # Store in session state
            st.session_state.user_data = user_data
            st.session_state.results = calculate_impact(user_data)
            st.session_state.recommendations = get_recommendations(user_data, st.session_state.results)
            
            # Rerun to show results
            st.rerun()

#############################
# MAIN APP FUNCTION
#############################

def main():
    display_header()
    
    if 'results' not in st.session_state:
        input_form()
    else:
        # Display results
        st.header("Your Sustainability Results")
        
        results = st.session_state.results
        
        col1, col2 = st.columns([1, 3])
        
        with col1:
            display_sustainability_score(results['overall_score'])
        
        with col2:
            display_impact_metrics(results)
        
        st.markdown("---")
        
        col3, col4 = st.columns(2)
        
        with col3:
            display_radar_chart(results)
        
        with col4:
            display_breakdown_chart(results)
        
        st.markdown("---")
        
        display_comparison(results)
        
        st.markdown("---")
        
        display_recommendations(st.session_state.recommendations)
        
        st.markdown("---")
        
        display_resources()
        
        st.markdown("---")
        
        if st.button("Calculate Again"):
            # Clear session state and return to input form
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

if __name__ == "__main__":
    main()
