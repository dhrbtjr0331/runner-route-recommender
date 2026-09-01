"""Benchmark evaluation test suite with 12 distinct cases across 3 topographies."""

from typing import List, Optional
from pydantic import BaseModel


class TestCase(BaseModel):
    __test__ = False
    id: str
    name: str
    city_key: str
    location_query: str
    target_distance_km: float
    difficulty: str
    user_prompt: str
    poi_keywords: List[str]
    avoid_keywords: List[str]
    max_gain_ceiling_m: Optional[float] = None
    min_gain_floor_m: Optional[float] = None
    is_showcase_hard_case: bool = False


BENCHMARK_CASES: List[TestCase] = [
    TestCase(
        id="C01",
        name="Santa Monica Coastal 5k Easy",
        city_key="santa_monica_pier",
        location_query="Santa Monica Pier, CA",
        target_distance_km=5.0,
        difficulty="easy",
        user_prompt="Flat recovery run near the beach along the boardwalk, avoid Ocean Ave traffic",
        poi_keywords=["beach", "ocean", "boardwalk", "sand", "coast"],
        avoid_keywords=["ocean_ave", "4th_st", "lincoln"],
        max_gain_ceiling_m=35.0,
    ),
    TestCase(
        id="C02",
        name="Santa Monica 10k Moderate",
        city_key="santa_monica_pier",
        location_query="Santa Monica Pier, CA",
        target_distance_km=10.0,
        difficulty="moderate",
        user_prompt="10k run heading north towards Palisades Park, some rolling terrain is great",
        poi_keywords=["palisades", "ocean", "park", "bluff"],
        avoid_keywords=["pch", "freeway"],
        min_gain_floor_m=35.0,
        max_gain_ceiling_m=120.0,
    ),
    TestCase(
        id="C03",
        name="Santa Monica 8k Easy (Avoid Lincoln)",
        city_key="santa_monica_pier",
        location_query="Santa Monica Pier, CA",
        target_distance_km=8.0,
        difficulty="easy",
        user_prompt="8km easy loop, stay close to beach path, strictly avoid Lincoln Blvd and 4th St",
        poi_keywords=["beach", "boardwalk", "ocean"],
        avoid_keywords=["lincoln", "4th_st"],
        max_gain_ceiling_m=45.0,
    ),
    TestCase(
        id="C04",
        name="Griffith Park 6k Hard Climb",
        city_key="griffith_park",
        location_query="Griffith Park, LA, CA",
        target_distance_km=6.0,
        difficulty="hard",
        user_prompt="Challenging hill climb loop towards the Observatory with steep trails",
        poi_keywords=["observatory", "trail", "peak", "summit", "canyon"],
        avoid_keywords=["freeway", "i_5"],
        min_gain_floor_m=110.0,
    ),
    TestCase(
        id="C05",
        name="Griffith Park 5k Easy Flats",
        city_key="griffith_park",
        location_query="Griffith Park, LA, CA",
        target_distance_km=5.0,
        difficulty="easy",
        user_prompt="Flat easy recovery run in the park, stay strictly on the lower flats, avoid hills",
        poi_keywords=["park", "lawn", "golf", "river", "flat"],
        avoid_keywords=["observatory", "mount_hollywood", "peak", "climb"],
        max_gain_ceiling_m=40.0,
    ),
    TestCase(
        id="C06",
        name="Griffith Park 12k Hard Mountain Loop",
        city_key="griffith_park",
        location_query="Griffith Park, LA, CA",
        target_distance_km=12.0,
        difficulty="hard",
        user_prompt="Long 12km trail loop covering mountain trails and ridges with high elevation gain",
        poi_keywords=["trail", "ridge", "mount", "canyon", "view"],
        avoid_keywords=["zoo_parking", "freeway"],
        min_gain_floor_m=200.0,
    ),
    TestCase(
        id="C07",
        name="Central Park NYC 5k Lake Loop",
        city_key="central_park_nyc",
        location_query="Central Park, NYC",
        target_distance_km=5.0,
        difficulty="easy",
        user_prompt="Easy lower park loop around the Lake and Ramble, paved walkways only",
        poi_keywords=["lake", "ramble", "mall", "bethesda", "terrace"],
        avoid_keywords=["5th_ave", "central_park_south", "columbus_circle"],
        max_gain_ceiling_m=35.0,
    ),
    TestCase(
        id="C08",
        name="Central Park NYC 10k Full Perimeter",
        city_key="central_park_nyc",
        location_query="Central Park, NYC",
        target_distance_km=9.7,
        difficulty="moderate",
        user_prompt="Full perimeter park drive loop including Harlem Hill, moderate rolling effort",
        poi_keywords=["drive", "reservoir", "harlem_hill", "meadow"],
        avoid_keywords=["traffic", "cross_town"],
        min_gain_floor_m=50.0,
        max_gain_ceiling_m=110.0,
    ),
    TestCase(
        id="C09",
        name="Central Park NYC 4k Shaded Easy",
        city_key="central_park_nyc",
        location_query="Central Park, NYC",
        target_distance_km=4.0,
        difficulty="easy",
        user_prompt="Quiet shaded recovery loop, avoid noisy Central Park South traffic",
        poi_keywords=["shade", "trees", "meadow", "bridle_path"],
        avoid_keywords=["central_park_south", "59th_st"],
        max_gain_ceiling_m=30.0,
    ),
    TestCase(
        id="C10",
        name="Venice Beach 6k Canals Loop",
        city_key="venice_beach",
        location_query="Venice Beach, CA",
        target_distance_km=6.0,
        difficulty="easy",
        user_prompt="Canals and ocean boardwalk loop, avoid congested Abbot Kinney Blvd",
        poi_keywords=["canals", "boardwalk", "beach", "ocean"],
        avoid_keywords=["abbot_kinney", "lincoln"],
        max_gain_ceiling_m=25.0,
    ),
    TestCase(
        id="C11",
        name="Downtown LA 5k Urban Architecture",
        city_key="downtown_la",
        location_query="Downtown LA, CA",
        target_distance_km=5.0,
        difficulty="moderate",
        user_prompt="Bunker Hill, Grand Park and Disney Hall exploration, paved sidewalks with city steps",
        poi_keywords=["grand_park", "bunker_hill", "broad", "civic_center"],
        avoid_keywords=["freeway_ramp", "skid_row"],
        min_gain_floor_m=30.0,
        max_gain_ceiling_m=80.0,
    ),
    TestCase(
        id="C12",
        name="Santa Monica Palisades 8k Showcase Hard Case",
        city_key="santa_monica_pier",
        location_query="Santa Monica, CA",
        target_distance_km=8.0,
        difficulty="easy",
        user_prompt="Start at beach, loop near ocean view, strictly under 40m gain, avoid PCH traffic",
        poi_keywords=["ocean", "beach", "bluffs", "sand"],
        avoid_keywords=["pch", "pacific_coast_hwy", "freeway"],
        max_gain_ceiling_m=40.0,
        is_showcase_hard_case=True,
    ),
]
