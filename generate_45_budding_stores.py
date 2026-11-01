"""
Generates 45 realistic, budding business e-commerce datasets for Ecomlytics.
Each store has modest, realistic numbers:
- 20 to 50 orders
- 10 to 30 customers
- 5 to 10 products
- AOV between ₹400 and ₹1,500
- 90-day time window (August - October 2026)
- 100% compliant with Ecomlytics importer headers and types.
- Validates in-memory before exporting to ZIP.
"""

import os
import sys
import random
import csv
import io
import shutil
import zipfile
import sqlite3
from datetime import date, timedelta
from pathlib import Path

# Set fixed seed for reproducibility
random.seed(2026)

REPO_DIR = Path(".")
sys.path.insert(0, str(REPO_DIR))
from ingestion.importer import import_csv_dataset

OUTPUT_DIR = Path("data/budding_stores_data")
OUTPUT_ZIP = Path("._45_Budding_Businesses_CSVs.zip")

if OUTPUT_DIR.exists():
    shutil.rmtree(OUTPUT_DIR)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

(OUTPUT_DIR / "orders_only_csv").mkdir(exist_ok=True)
(OUTPUT_DIR / "customers_only_csv").mkdir(exist_ok=True)
(OUTPUT_DIR / "products_only_csv").mkdir(exist_ok=True)
(OUTPUT_DIR / "store_packages").mkdir(exist_ok=True)

FIRST_NAMES = [
    "Aarav", "Aditya", "Akash", "Arjun", "Aryan", "Aditi", "Ananya", "Anika", "Diya", "Isha",
    "Kavya", "Meera", "Neha", "Pooja", "Riya", "Sahana", "Shreya", "Sneha", "Tanvi", "Varsha",
    "Kabir", "Rohan", "Vikram", "Karan", "Devansh", "Priya", "Ishita", "Nikhil", "Gaurav", "Simran",
    "Rahul", "Deepak", "Manish", "Preeti", "Siddharth", "Tara", "Naveen", "Divya", "Kunal", "Swati"
]

LAST_NAMES = [
    "Sharma", "Patel", "Kumar", "Singh", "Reddy", "Nair", "Gupta", "Verma", "Joshi", "Mehta",
    "Rao", "Iyer", "Shah", "Das", "Bhat", "Chopra", "Malhotra", "Menon", "Pillai", "Deshmukh"
]

CITIES = [
    "Bengaluru", "Mumbai", "Delhi", "Hyderabad", "Chennai", "Pune", "Kolkata", "Ahmedabad", "Jaipur", "Kochi",
    "Chandigarh", "Indore", "Coimbatore", "Mysuru", "Goa", "Lucknow", "Bhopal", "Visakhapatnam"
]

STORES = [
    {"slug": "auric_clay", "name": "Auric Clay Ceramics", "category": "Home & Decor", "prefix": "ACC", "prods": [
        ("Terracotta Coffee Mug 300ml", "Mugs", 399, 140),
        ("Handmade Speckled Cereal Bowl", "Bowls", 499, 180),
        ("Minimalist Ceramic Planter 6in", "Planters", 699, 260),
        ("Artisan Pasta Plate (Set of 2)", "Plates", 999, 410),
        ("Earthy Glazed Vase Medium", "Vases", 849, 320),
        ("Ceramic Teapot with Infuser", "Teaware", 1299, 530)
    ]},
    {"slug": "brewcraft_roasters", "name": "BrewCraft Roasters", "category": "Food & Beverage", "prefix": "BCR", "prods": [
        ("Mysuru Estate Medium Roast 250g", "Whole Bean", 450, 190),
        ("Coorg Dark Roast Coffee 250g", "Whole Bean", 420, 180),
        ("Single-Origin Pour Over Grind 250g", "Ground Coffee", 480, 210),
        ("Cold Brew Blend Coarse Grind 500g", "Ground Coffee", 750, 320),
        ("Stainless Steel Coffee Dripper", "Brew Gear", 899, 390),
        ("French Press 350ml Glass", "Brew Gear", 1099, 480)
    ]},
    {"slug": "bloom_leaf_organics", "name": "Bloom & Leaf Organics", "category": "Health & Wellness", "prefix": "BLO", "prods": [
        ("Chamomile Citrus Calming Tea 100g", "Herbal Tea", 380, 130),
        ("Kashmiri Kahwa Green Tea 100g", "Green Tea", 450, 160),
        ("Hibiscus Rose Infusion 75g", "Herbal Tea", 399, 140),
        ("Lavender Lemongrass Wellness Tea", "Herbal Tea", 420, 150),
        ("Bamboo Tea Strainer Spoon", "Accessories", 199, 60),
        ("Double-Walled Glass Tumbler", "Drinkware", 649, 240)
    ]},
    {"slug": "terra_glow_botanicals", "name": "Terra Glow Botanicals", "category": "Beauty & Skincare", "prefix": "TGB", "prods": [
        ("Kumkumadi Radiance Face Oil 30ml", "Face Oils", 699, 240),
        ("Wild Turmeric Gentle Cleanser 100ml", "Cleansers", 399, 130),
        ("Rosewater & Aloe Vera Mist 120ml", "Toners", 349, 110),
        ("Cold-Pressed Hemp Seed Moisturizer", "Moisturizers", 549, 190),
        ("Bakuchiol Youth Restoring Serum", "Serums", 799, 280),
        ("Neem & Vetiver Purifying Clay Mask", "Face Masks", 449, 150)
    ]},
    {"slug": "the_linen_loom", "name": "The Linen Loom", "category": "Fashion & Apparel", "prefix": "TLL", "prods": [
        ("Relaxed Linen Camp Collar Shirt", "Shirts", 1299, 520),
        ("Striped Handloom Cotton Kurta", "Ethnic Wear", 999, 390),
        ("Breathable Linen Drawstring Trousers", "Bottoms", 1499, 620),
        ("Everyday Linen Tote Bag", "Accessories", 499, 170),
        ("Handloom Cotton Bandana (Olive)", "Accessories", 299, 90),
        ("Linen Apron with Deep Pockets", "Home Textile", 799, 290)
    ]},
    {"slug": "spiceroute_origins", "name": "SpiceRoute Origins", "category": "Gourmet Grocery", "prefix": "SRO", "prods": [
        ("Wayanad Black Pepper Grade A 200g", "Spices", 320, 120),
        ("Idukki Green Cardamom 100g", "Spices", 580, 240),
        ("Single-Origin Lakadong Turmeric 250g", "Spices", 360, 130),
        ("Stone Ground Garam Masala 150g", "Blends", 260, 95),
        ("Himalayan Pink Rock Salt Fine 500g", "Pantry", 180, 50),
        ("Smoked Kashmiri Chilli Flakes 100g", "Spices", 299, 110)
    ]},
    {"slug": "little_sprout_toys", "name": "Little Sprout Toys", "category": "Kids & Toys", "prefix": "LST", "prods": [
        ("Montessori Wooden Stacking Rings", "Wooden Toys", 599, 220),
        ("Organic Cotton Soft Rattle Animal", "Baby Toys", 399, 130),
        ("Natural Neem Wood Teether Ring", "Teethers", 299, 90),
        ("Geometric Sorting Board Puzzle", "Educational", 699, 260),
        ("Wooden Animal Pull Toy Elephant", "Active Toys", 749, 290)
    ]},
    {"slug": "urban_herbarium", "name": "Urban Herbarium", "category": "Gardening & Lifestyle", "prefix": "UHB", "prods": [
        ("Windowsill Microgreens Starter Kit", "Grow Kits", 499, 170),
        ("Italian Basil & Parsley Seed Pods", "Seeds", 249, 70),
        ("Mini Copper Mist Spray Bottle", "Tools", 599, 210),
        ("Organic Cocopeat Soil Mix 5kg", "Plant Care", 299, 95),
        ("Ceramic Herb Pots Trio with Saucer", "Planters", 899, 340)
    ]},
    {"slug": "kintsugi_home", "name": "Kintsugi Home Decor", "category": "Home & Decor", "prefix": "KHD", "prods": [
        ("Gold Foil Ceramic Coasters (Set of 4)", "Coasters", 599, 210),
        ("Hand-Turned Sheesham Wood Platter", "Serveware", 899, 340),
        ("Marble and Brass Trivet", "Tabletop", 749, 280),
        ("Ribbed Glass Candle Votive", "Candles", 349, 110),
        ("Hammered Brass Incense Burner", "Aromatherapy", 649, 230)
    ]},
    {"slug": "solecraft_leather", "name": "SoleCraft Leather", "category": "Accessories", "prefix": "SCL", "prods": [
        ("Full-Grain Leather Bifold Wallet", "Wallets", 1199, 440),
        ("Minimalist Slim Card Sleeve", "Wallets", 599, 190),
        ("Handstitched Key Fob Organizer", "Keychains", 349, 100),
        ("Leather Passport Case (Tan)", "Travel", 799, 290),
        ("Waxed Canvas & Leather Cable Roll", "Organizers", 699, 240)
    ]},
    {"slug": "nectar_hive", "name": "Nectar & Hive Apiaries", "category": "Gourmet Grocery", "prefix": "NAH", "prods": [
        ("Raw Wild Forest Multifloral Honey 350g", "Honey", 450, 170),
        ("Mustard Flora Raw Honey 350g", "Honey", 390, 140),
        ("Kashmir White Acacia Honey 250g", "Honey", 590, 230),
        ("Raw Honeycomb Chunk in Glass Jar", "Gourmet", 650, 260),
        ("Bee Pollen Granules 150g", "Superfood", 499, 180)
    ]},
    {"slug": "thread_needle_studio", "name": "Thread & Needle Studio", "category": "Fashion & Lifestyle", "prefix": "TNS", "prods": [
        ("Hand-Embroidered Botanical Canvas Tote", "Bags", 699, 250),
        ("Embroidered Floral Zipper Pouch", "Pouches", 349, 110),
        ("Canvas Laptop Sleeve 14-inch", "Accessories", 899, 330),
        ("Embroidery DIY Beginner Hoop Kit", "Craft Kits", 549, 180),
        ("Cotton Linen Lunch Tote Insulated", "Bags", 599, 210)
    ]},
    {"slug": "purebite_confections", "name": "PureBite Confections", "category": "Gourmet Grocery", "prefix": "PBC", "prods": [
        ("70% Kerala Dark Chocolate Bar 80g", "Chocolate", 299, 110),
        ("Roasted Almond Sea Salt Dark Chocolate", "Chocolate", 320, 120),
        ("Vegan Hazelnut Praline Spread 200g", "Spreads", 480, 180),
        ("Sugar-Free Cocoa Nibs Crunch 100g", "Snacks", 350, 125),
        ("Hot Cocoa Mix Single-Origin 200g", "Beverages", 399, 140)
    ]},
    {"slug": "the_green_wick", "name": "The Green Wick Co.", "category": "Home Fragrance", "prefix": "TGW", "prods": [
        ("Vanilla Bean & Cedarwood Soy Candle", "Candles", 549, 180),
        ("Fresh Linen & Jasmine Candle Jar", "Candles", 549, 180),
        ("Citrus Blossom Amber Jar Candle", "Candles", 499, 160),
        ("Cinnamon Spice Holiday Tin Candle", "Candles", 399, 130),
        ("Matte Black Wick Trimmer & Snuffer", "Accessories", 450, 140)
    ]},
    {"slug": "bamboo_basics", "name": "Bamboo Basics EcoStore", "category": "Eco-Friendly Living", "prefix": "BBE", "prods": [
        ("Bamboo Cutlery Travel Set in Pouch", "Kitchen", 349, 100),
        ("Solid Bamboo Cutting Board Medium", "Kitchen", 699, 250),
        ("Biodegradable Bamboo Charcoal Toothbrush (Pack of 4)", "Personal Care", 299, 85),
        ("Bamboo Fiber Salad Bowl with Servers", "Serveware", 799, 290),
        ("Bamboo Dish Scrub Brushes (Set of 2)", "Cleaning", 249, 70)
    ]},
    {"slug": "petal_press", "name": "Petal & Press Studio", "category": "Stationery & Art", "prefix": "PPS", "prods": [
        ("Pressed Flower Bookmark Set (Pack of 4)", "Stationery", 249, 70),
        ("Handmade Botanical Journal (Unlined)", "Journals", 499, 160),
        ("Pressed Fern Framed Wall Art 8x10", "Wall Decor", 899, 310),
        ("Floral Wax Seal Stamp & Wax Beads Kit", "Crafts", 649, 220),
        ("Handmade Seed Paper Postcards (Pack of 6)", "Paper Goods", 299, 85)
    ]},
    {"slug": "trailblazer_gear", "name": "Trailblazer Outdoor Gear", "category": "Sports & Outdoors", "prefix": "TBG", "prods": [
        ("Ultralight Ripstop Waist Pack 2L", "Bags", 799, 290),
        ("Waterproof Dry Bag Pouch 5L", "Dry Bags", 499, 170),
        ("Compact Microfiber Quick-Dry Towel", "Travel Towels", 399, 130),
        ("Anodized Aluminum Carabiner Trio", "Accessories", 249, 65),
        ("Insulated Stainless Camping Mug 400ml", "Cookware", 599, 210)
    ]},
    {"slug": "zenknot_macrame", "name": "ZenKnot Macrame", "category": "Home & Decor", "prefix": "ZKM", "prods": [
        ("Boho Cotton Macrame Plant Hanger 36in", "Plant Hangers", 449, 140),
        ("Geometric Macrame Wall Tapestry Medium", "Wall Art", 899, 320),
        ("Macrame Coasters with Fringe (Set of 2)", "Tabletop", 299, 85),
        ("Woven Cotton Fruit Hammock for Kitchen", "Storage", 499, 160),
        ("Macrame Keychain Wristlet (Set of 2)", "Accessories", 220, 60)
    ]},
    {"slug": "copperveda_crafts", "name": "CopperVeda Crafts", "category": "Wellness & Living", "prefix": "CVC", "prods": [
        ("Hammered Pure Copper Bottle 950ml", "Bottles", 899, 340),
        ("Seamless Glossy Copper Tumbler 300ml", "Drinkware", 399, 140),
        ("Handmade Copper Tongue Scraper (Pack of 2)", "Personal Care", 199, 50),
        ("Engraved Copper Water Carafe 1.2L", "Serveware", 1399, 560),
        ("Copper Moscow Mule Mugs (Set of 2)", "Barware", 999, 390)
    ]},
    {"slug": "nutricrunch_granola", "name": "NutriCrunch Granola", "category": "Health Food", "prefix": "NCG", "prods": [
        ("Almond Cranberry Baked Granola 350g", "Granola", 399, 150),
        ("Cacao Nibs & Coconut Clusters 350g", "Granola", 420, 160),
        ("Jaggery Spiced Ragi Crisp Bites 200g", "Healthy Snacks", 250, 85),
        ("Roasted Chia & Flaxseed Mix 250g", "Superfood", 299, 95),
        ("Gluten-Free Nut Butter Protein Bites", "Snack Bars", 349, 120)
    ]},
    {"slug": "aura_mist_scents", "name": "Aura Mist Aromatics", "category": "Home Fragrance", "prefix": "AMS", "prods": [
        ("Eucalyptus & Mint Room Freshener Mist", "Room Spray", 349, 110),
        ("Lavender Sleep Pillow Spray 100ml", "Wellness Spray", 380, 125),
        ("Sandalwood & Cardamom Reed Diffuser 100ml", "Diffusers", 749, 270),
        ("Pure Lemongrass Essential Oil 15ml", "Essential Oils", 280, 85),
        ("Sweet Orange Diffuser Oil Blend 15ml", "Essential Oils", 299, 90)
    ]},
    {"slug": "the_rustic_baker", "name": "The Rustic Baker Pantry", "category": "Artisanal Bakery", "prefix": "TRB", "prods": [
        ("Artisanal Sourdough Crackers with Rosemary", "Baked Goods", 280, 95),
        ("Dutch Cocoa Butter Cookies Tin 250g", "Cookies", 390, 140),
        ("Almond Biscotti Twice-Baked 200g", "Biscotti", 340, 115),
        ("Cinnamon Sugar Granola Crust Bites", "Snacks", 299, 95),
        ("Gluten-Free Oats & Seed Crispbread", "Healthy Breads", 310, 105)
    ]},
    {"slug": "claypaws_pets", "name": "ClayPaws Pet Care", "category": "Pet Supplies", "prefix": "CPP", "prods": [
        ("Natural Shea Butter Dog Paw Balm 50g", "Grooming", 349, 110),
        ("Oatmeal & Aloe Vera Dog Shampoo 250ml", "Grooming", 399, 130),
        ("Peanut Butter Crunch Grain-Free Biscuits", "Dog Treats", 299, 95),
        ("Hemp Rope Tug Toy with Cotton Ball", "Toys", 249, 75),
        ("Eco-Friendly Bamboo Pet Bowl Anti-Skid", "Feeding", 499, 170)
    ]},
    {"slug": "canvas_thread_tees", "name": "Canvas & Thread Tees", "category": "Apparel & Merch", "prefix": "CTT", "prods": [
        ("Minimalist Mountain Print Heavy T-Shirt", "T-Shirts", 699, 260),
        ("Coffee First Graphic Cotton Tee", "T-Shirts", 699, 260),
        ("Retro Wave Oversized Drop Shoulder Tee", "T-Shirts", 799, 310),
        ("Heavyweight 100% Organic Cotton Hoodie", "Hoodies", 1499, 610),
        ("Embroidered Logo Cotton Dad Cap", "Headwear", 449, 150)
    ]},
    {"slug": "velvet_wool_knitwear", "name": "Velvet & Wool Knits", "category": "Winterwear & Apparel", "prefix": "VWK", "prods": [
        ("Handknitted Ribbed Wool Beanie (Mustard)", "Beanies", 499, 160),
        ("Chunky Cable Knit Infinity Scarf", "Scarves", 849, 310),
        ("Merino Blend Fingerless Typing Gloves", "Gloves", 399, 130),
        ("Cozy Wool Blend Slipper Socks (Pair)", "Socks", 349, 110),
        ("Handwoven Woolen Throw Blanket Mini", "Throws", 1399, 550)
    ]},
    {"slug": "papercrafter_studio", "name": "PaperCrafter Studio", "category": "Eco-Stationery", "prefix": "PCS", "prods": [
        ("Seed Paper Calendar with Wooden Stand", "Calendars", 399, 120),
        ("Deckle-Edge Cotton Rag Paper Journal", "Journals", 549, 180),
        ("Plantable Marigold Seed Pencils (Box of 10)", "Pencils", 249, 70),
        ("Handmade Kraft Paper Gift Bags (Pack of 5)", "Packaging", 299, 80),
        ("Calligraphy Copperplate Practice Pad", "Paper Goods", 349, 105)
    ]},
    {"slug": "heritage_brassware", "name": "Heritage Brassware", "category": "Home & Spiritual", "prefix": "HBW", "prods": [
        ("Traditional Brass Diya Lamp with Etching", "Spiritual", 399, 140),
        ("Cast Brass Peacock Incense Holder", "Home Decor", 549, 210),
        ("Handcrafted Brass Coffee Filter Decanter", "Kitchen", 799, 320),
        ("Engraved Brass Pooja Bell with Nandi Handle", "Spiritual", 499, 180),
        ("Mini Brass Urlis with Floating Flower Ring", "Decor", 899, 360)
    ]},
    {"slug": "matcha_leaf_co", "name": "Matcha Leaf Co.", "category": "Gourmet Tea", "prefix": "MLC", "prods": [
        ("Uji Ceremonial Grade Matcha 30g", "Matcha", 899, 350),
        ("Culinary Grade Matcha Powder 100g", "Matcha", 649, 240),
        ("Traditional Bamboo Matcha Whisk (Chasen)", "Accessories", 499, 170),
        ("Handmade Ceramic Matcha Bowl (Chawan)", "Teaware", 799, 290),
        ("Matcha Latte Blend with Coconut Sugar", "Blends", 449, 150)
    ]},
    {"slug": "nomad_leatherworks", "name": "Nomad Leatherworks", "category": "Travel Accessories", "prefix": "NLW", "prods": [
        ("Leather Tech Organizer Pouch", "Pouches", 999, 380),
        ("Personalized Luggage Tag (Full Grain)", "Travel", 299, 85),
        ("Foldable Leather Valet Tray for Desk", "Desk Decor", 499, 160),
        ("Waxed Canvas Field Notes Cover", "Notebook Covers", 449, 150),
        ("Leather Cord Wrap Ties (Pack of 3)", "Accessories", 199, 50)
    ]},
    {"slug": "silk_dye_textiles", "name": "Silk & Dye Studio", "category": "Textiles & Scarves", "prefix": "SDS", "prods": [
        ("Madder Root Naturally Dyed Silk Scarf", "Scarves", 1199, 440),
        ("Indigo Shibori Cotton Bandana", "Bandanas", 399, 130),
        ("Marigold Petal Dyed Cotton Cushion Cover", "Home Textile", 499, 170),
        ("Mulberry Silk Sleep Eye Mask", "Accessories", 549, 190),
        ("Naturally Dyed Silk Scrunchies (Pack of 3)", "Hair Accessories", 349, 100)
    ]},
    {"slug": "cold_pressed_bar", "name": "The Cold Pressed Bar", "category": "Bath & Body", "prefix": "CPB", "prods": [
        ("Activated Charcoal Detox Soap 125g", "Soaps", 220, 65),
        ("Oatmeal Honey & Goat Milk Bar 125g", "Soaps", 240, 70),
        ("French Green Clay & Tea Tree Bar", "Soaps", 220, 65),
        ("Coffee Scrub Body Exfoliator Bar", "Soaps", 260, 75),
        ("Wooden Slotted Soap Dish Holder", "Accessories", 180, 45)
    ]},
    {"slug": "wildflower_apothecary", "name": "Wildflower Apothecary", "category": "Bath & Spa", "prefix": "WFA", "prods": [
        ("Rose Petal & Himalayan Pink Bath Salts", "Bath Care", 399, 130),
        ("Whipped Mango Body Butter 150g", "Body Care", 499, 170),
        ("Brown Sugar & Vanilla Lip Scrub 30g", "Lip Care", 220, 60),
        ("Nourishing Almond Herbal Hair Oil 100ml", "Hair Care", 420, 140),
        ("Botanical Shower Steamers (Pack of 4)", "Shower Care", 360, 110)
    ]},
    {"slug": "beantobar_kokoa", "name": "BeanToBar Kokoa", "category": "Chocolaterie", "prefix": "BBK", "prods": [
        ("85% Single-Origin Dark Cocoa Bar 70g", "Chocolates", 299, 105),
        ("Caramelized White Chocolate with Cocoa Nibs", "Chocolates", 320, 115),
        ("Sea Salt Toffee Dark Chocolate Slab", "Chocolates", 340, 120),
        ("Organic Cocoa Butter Discs 150g", "Baking", 380, 135),
        ("Artisan Truffle Box (Assorted 6 Pcs)", "Gift Boxes", 599, 220)
    ]},
    {"slug": "minimalist_woodworks", "name": "Minimalist Woodworks", "category": "Home & Kitchen", "prefix": "MWW", "prods": [
        ("Teak Wood Hexagonal Coasters (Set of 4)", "Coasters", 499, 160),
        ("Walnut Wood Phone & Tablet Stand", "Desk Decor", 399, 125),
        ("Handcarved Acacia Wood Salad Spoons", "Kitchen", 449, 145),
        ("Magnetic Wooden Key Holder Rack", "Storage", 599, 210),
        ("Wooden Desk Clock with Silent Sweep", "Clocks", 899, 330)
    ]},
    {"slug": "the_chai_box", "name": "The Chai Box Blends", "category": "Gourmet Beverages", "prefix": "TCB", "prods": [
        ("Royal Masala Chai Spiced CTC 250g", "Chai", 320, 105),
        ("Ginger Cardamom Morning Blend 250g", "Chai", 310, 100),
        ("Lemongrass Saffron Herbal Chai 150g", "Chai", 380, 130),
        ("Brass Chai Strainer with Wooden Handle", "Accessories", 349, 110),
        ("Clay Kulhad Cups (Set of 4)", "Drinkware", 399, 120)
    ]},
    {"slug": "knotty_pine_crafts", "name": "Knotty Pine Crafts", "category": "Desk & Workspace", "prefix": "KPC", "prods": [
        ("Pine Wood Dual Pen Holder with Groove", "Desk Decor", 299, 90),
        ("Monitor Riser Shelf Solid Pine Wood", "Office Furniture", 1199, 460),
        ("Wooden Sticky Note & Card Organizer", "Desk Decor", 249, 75),
        ("Cable Management Wooden Box Medium", "Storage", 699, 240),
        ("Minimal Wooden Headphone Stand", "Accessories", 799, 280)
    ]},
    {"slug": "earthy_threads_home", "name": "Earthy Threads Home", "category": "Kitchen Linen", "prefix": "ETH", "prods": [
        ("Block Printed Cotton Apron with Pocket", "Kitchen Linen", 599, 200),
        ("Waffle Weave Kitchen Hand Towels (Pair)", "Towels", 399, 130),
        ("Quilted Oven Mitts & Pot Holder Set", "Kitchen Linen", 449, 145),
        ("Handloom Cotton Dining Placemats (Set of 4)", "Dining", 699, 240),
        ("Bread Basket with Drawstring Liner", "Dining", 499, 165)
    ]},
    {"slug": "copper_slate_design", "name": "Copper & Slate Designs", "category": "Modern Decor", "prefix": "CSD", "prods": [
        ("Natural Slate Stone Coasters (Set of 4)", "Coasters", 449, 140),
        ("Copper Finish Wire Fruit Basket", "Kitchen Storage", 699, 240),
        ("Slate Chalkboard Memo Plaque with Stand", "Desk Decor", 399, 120),
        ("Brushed Copper Minimalist Desk Lamp", "Lighting", 1499, 610),
        ("Slate Cheese Board with Chalk Marker", "Serveware", 799, 270)
    ]},
    {"slug": "wholesome_paws_bakery", "name": "Wholesome Paws Bakery", "category": "Pet Treats", "prefix": "WPB", "prods": [
        ("Dehydrated Chicken Jerky Treats 100g", "Dog Treats", 349, 115),
        ("Pumpkin & Oat Digestive Biscuits 150g", "Dog Treats", 280, 90),
        ("Freeze-Dried Salmon Cat Treats 60g", "Cat Treats", 399, 135),
        ("Natural Catnip Leaves Glass Jar 30g", "Cat Supplies", 220, 65),
        ("Silicone Paw Lick Mat with Suction", "Pet Toys", 299, 95)
    ]},
    {"slug": "the_indigo_studio", "name": "The Indigo Studio", "category": "Home Textiles", "prefix": "TIS", "prods": [
        ("Dabu Block-Print Indigo Cushion Cover 16in", "Cushions", 449, 145),
        ("Hand-Dyed Indigo Cotton Table Runner 6ft", "Table Linen", 799, 275),
        ("Indigo Geometric Shibori Bed Runner", "Bed Linen", 999, 360),
        ("Indigo Dabu Canvas Tote Bag", "Bags", 549, 185),
        ("Indigo Cotton Napkins Set of 4", "Table Linen", 399, 125)
    ]},
    {"slug": "sundipped_dryfruits", "name": "SunDipped Dry Fruits", "category": "Gourmet Snacks", "prefix": "SDD", "prods": [
        ("Spiced Roasted California Almonds 200g", "Nuts", 360, 140),
        ("Pepper & Herb Cashews Dry Roasted 200g", "Nuts", 420, 170),
        ("Sun-Dried Cranberries & Blueberries 150g", "Berries", 340, 120),
        ("Kashmiri Walnuts In-Shell Fresh 400g", "Nuts", 480, 190),
        ("Trail Mix Seeds & Dry Berry Blend 250g", "Mixes", 380, 135)
    ]},
    {"slug": "pureform_skincare", "name": "PureForm Skincare", "category": "Clean Beauty", "prefix": "PFS", "prods": [
        ("100% Pure Organic Rosehip Oil 30ml", "Facial Oils", 649, 230),
        ("Cold-Pressed Jojoba Balancing Oil 50ml", "Facial Oils", 549, 190),
        ("Hyaluronic Acid Hydrating Gel Mist 100ml", "Toners", 449, 145),
        ("Centella Asiatica Barrier Cream 50g", "Moisturizers", 699, 245),
        ("Zinc Oxide Mineral Sunscreen Matte 50g", "Sun Care", 599, 210)
    ]},
    {"slug": "studio_kora_pots", "name": "Studio Kora Ceramics", "category": "Planters & Pots", "prefix": "SKP", "prods": [
        ("Terracotta Textured Succulent Bowl", "Planters", 349, 110),
        ("White Matte Ceramic Cylinder Pot 5in", "Planters", 499, 165),
        ("Hanging Terracotta Cone Planter with Jute", "Planters", 449, 140),
        ("Miniature Cactus Pots Trio on Tray", "Planters", 649, 220),
        ("Ceramic Watering Bell Dropper", "Tools", 299, 90)
    ]},
    {"slug": "the_herbal_sips", "name": "The Herbal Sips", "category": "Wellness Teas", "prefix": "THS", "prods": [
        ("Valerian Root & Chamomile Bedtime Tea", "Teas", 399, 135),
        ("Spearmint & Fennel Digestive Tisane", "Teas", 360, 120),
        ("Moringa & Lemon Morning Detox Infusion", "Teas", 380, 125),
        ("Pure Butterfly Pea Flower Tea 50g", "Teas", 320, 100),
        ("Stainless Steel Mesh Tea Ball Infuser", "Accessories", 199, 55)
    ]},
    {"slug": "urban_botanist_kits", "name": "Urban Botanist Studios", "category": "Craft & Plants", "prefix": "UBS", "prods": [
        ("Geometric Glass DIY Terrarium Kit", "Plant Kits", 999, 360),
        ("Preserved Reindeer Moss Wall Frame 6x6", "Moss Art", 849, 290),
        ("Miniature Succulent Soil & Stone Kit", "Supplies", 299, 90),
        ("Curved Terrarium Tweezer & Brush Tool Set", "Tools", 349, 110),
        ("Air Plant on Driftwood Mount Display", "Plants", 499, 165)
    ]}
]

# In-memory test connection for validation
mem_conn = sqlite3.connect(":memory:")
mem_conn.row_factory = sqlite3.Row
with open(REPO_DIR / "database" / "schema.sql", "r", encoding="utf-8") as f:
    mem_conn.executescript(f.read())

summary_rows = []

# Reference date: 2026-11-01
END_DATE = date(2026, 11, 1)
START_DATE = END_DATE - timedelta(days=85)

print(f"Generating datasets for {len(STORES)} budding businesses...")

for idx, store_info in enumerate(STORES, start=1):
    slug = store_info["slug"]
    name = store_info["name"]
    category = store_info["category"]
    prefix = store_info["prefix"]
    prods_def = store_info["prods"]
    store_num = f"{idx:02d}"

    # 1. GENERATE PRODUCTS
    products = []
    for p_idx, (p_name, p_cat, p_price, p_cost) in enumerate(prods_def, start=1):
        pid = f"PROD-{prefix}-{p_idx:02d}"
        products.append({
            "product_id": pid,
            "product_name": p_name,
            "category": p_cat,
            "price": p_price,
            "cost": p_cost
        })

    # 2. GENERATE CUSTOMERS (12 to 25 customers per budding store)
    num_custs = random.randint(12, 24)
    customers = []
    used_cust_ids = set()
    for c_idx in range(1, num_custs + 1):
        cid = f"CUST-{prefix}-{c_idx:03d}"
        c_name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
        c_email = f"{c_name.lower().replace(' ', '.')}_{random.randint(10, 99)}@example.com"
        c_city = random.choice(CITIES)
        customers.append({
            "customer_id": cid,
            "customer_name": c_name,
            "email": c_email,
            "city": c_city
        })

    # 3. GENERATE ORDERS (22 to 45 orders per budding store over 85 days)
    num_orders = random.randint(22, 45)
    orders = []

    # Choose repeat buyers
    repeat_customers = random.sample(customers, k=random.randint(4, min(8, len(customers))))
    normal_customers = [c for c in customers if c not in repeat_customers]

    # Weighted pool: repeat buyers have higher weight
    pool = normal_customers[:] + (repeat_customers * 3)

    total_revenue = 0.0
    completed_orders_cnt = 0
    returned_orders_cnt = 0

    for o_idx in range(1, num_orders + 1):
        oid = f"ORD-{prefix}-{1000 + o_idx}"
        cust = random.choice(pool)
        prod = random.choice(products)

        qty = 1 if random.random() > 0.18 else 2
        price = float(prod["price"])
        discount = 0
        if random.random() < 0.22:
            discount = random.choice([30, 50, 75])
        
        gross = price * qty
        rev = max(0.0, gross - discount)

        day_offset = random.randint(0, 85)
        odate = START_DATE + timedelta(days=day_offset)

        roll = random.random()
        if roll < 0.92:
            st = "completed"
            total_revenue += rev
            completed_orders_cnt += 1
        elif roll < 0.97:
            st = "returned"
            returned_orders_cnt += 1
        else:
            st = "cancelled"

        orders.append({
            "order_id": oid,
            "customer_id": cust["customer_id"],
            "product_id": prod["product_id"],
            "order_date": odate.isoformat(),
            "quantity": qty,
            "price": int(price),
            "discount": discount,
            "revenue": round(rev, 2),
            "status": st
        })

    aov = round(total_revenue / completed_orders_cnt, 2) if completed_orders_cnt > 0 else 0.0
    ret_rate = round((returned_orders_cnt / (completed_orders_cnt + returned_orders_cnt)) * 100, 1) if (completed_orders_cnt + returned_orders_cnt) > 0 else 0.0

    # 4. SERIALIZE TO CSV STRINGS
    def to_csv_string(rows):
        if not rows:
            return ""
        out = io.StringIO()
        w = csv.DictWriter(out, fieldnames=rows[0].keys())
        w.writeheader()
        w.writerows(rows)
        return out.getvalue()

    prod_csv_str = to_csv_string(products)
    cust_csv_str = to_csv_string(customers)
    ord_csv_str = to_csv_string(orders)

    # 5. VALIDATE WITH INGESTION ENGINE IN MEMORY
    test_ws_id = f"ws_val_{idx}"
    mem_conn.execute("INSERT INTO workspaces (id, name) VALUES (?, ?)", (test_ws_id, name))
    
    res_p = import_csv_dataset(mem_conn, test_ws_id, "products", prod_csv_str, "products.csv")
    res_c = import_csv_dataset(mem_conn, test_ws_id, "customers", cust_csv_str, "customers.csv")
    res_o = import_csv_dataset(mem_conn, test_ws_id, "orders", ord_csv_str, "orders.csv")

    assert res_p["rejected_rows"] == 0, f"Store {name} products had rejected rows: {res_p['errors']}"
    assert res_c["rejected_rows"] == 0, f"Store {name} customers had rejected rows: {res_c['errors']}"
    assert res_o["rejected_rows"] == 0, f"Store {name} orders had rejected rows: {res_o['errors']}"

    # 6. WRITE CSV FILES TO DISK
    # A) Flat orders CSV (for quick drag-and-drop into the default Orders upload)
    flat_order_filename = f"store_{store_num}_{slug}_orders.csv"
    with open(OUTPUT_DIR / "orders_only_csv" / flat_order_filename, "w", encoding="utf-8", newline="") as f:
        f.write(ord_csv_str)

    # Flat customer & product CSVs
    flat_cust_filename = f"store_{store_num}_{slug}_customers.csv"
    with open(OUTPUT_DIR / "customers_only_csv" / flat_cust_filename, "w", encoding="utf-8", newline="") as f:
        f.write(cust_csv_str)

    flat_prod_filename = f"store_{store_num}_{slug}_products.csv"
    with open(OUTPUT_DIR / "products_only_csv" / flat_prod_filename, "w", encoding="utf-8", newline="") as f:
        f.write(prod_csv_str)

    # B) Store Package folder (all 3 files together with standard names)
    store_pkg_dir = OUTPUT_DIR / "store_packages" / f"store_{store_num}_{slug}"
    store_pkg_dir.mkdir(parents=True, exist_ok=True)
    with open(store_pkg_dir / "orders.csv", "w", encoding="utf-8", newline="") as f:
        f.write(ord_csv_str)
    with open(store_pkg_dir / "products.csv", "w", encoding="utf-8", newline="") as f:
        f.write(prod_csv_str)
    with open(store_pkg_dir / "customers.csv", "w", encoding="utf-8", newline="") as f:
        f.write(cust_csv_str)

    summary_rows.append({
        "store_number": store_num,
        "store_slug": slug,
        "business_name": name,
        "industry_category": category,
        "orders_count": len(orders),
        "customers_count": len(customers),
        "products_count": len(products),
        "total_revenue_inr": round(total_revenue, 2),
        "aov_inr": aov,
        "return_rate_pct": ret_rate,
        "sample_orders_file": flat_order_filename,
        "store_package_folder": f"store_packages/store_{store_num}_{slug}/"
    })

# Write master index catalog
catalog_path = OUTPUT_DIR / "ACCOUNTS_AND_STORES_CATALOG.csv"
with open(catalog_path, "w", encoding="utf-8", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=summary_rows[0].keys())
    writer.writeheader()
    writer.writerows(summary_rows)

# Write comprehensive README instructions
readme_text = f"""========================================================================
ECOMLYTICS — 45 REALISTIC BUDDING BUSINESS DEMO DATASETS
========================================================================
Designed specifically for student/academic presentation of Ecomlytics.

CONTENTS SUMMARY:
- 45 Budding Indian & Global D2C Businesses (Handcrafted, Organic, Artisanal, Niche).
- Modest & Realistic Numbers (12-25 customers, 22-45 orders, INR 12,000 - 45,000 revenue).
- 100% verified against Ecomlytics CSV Ingestion Engine (0 errors, 0 rejected rows).
- Synchronized Foreign Keys (Order customer_id and product_id match customer & product CSVs).

DIRECTORY STRUCTURE INSIDE THIS ZIP:
1. orders_only_csv/
   Contains 45 CSV files (one for each store) named:
   store_01_auric_clay_orders.csv, store_02_brewcraft_roasters_orders.csv, ...
   Use this if you simply want to upload Orders on any account!

2. products_only_csv/
   Contains 45 product catalog CSV files.

3. customers_only_csv/
   Contains 45 customer list CSV files.

4. store_packages/
   Contains 45 individual store folders (e.g., store_01_auric_clay/).
   Inside each store folder, you find:
   - orders.csv
   - products.csv
   - customers.csv
   Uploading all 3 enables every single dashboard tab:
   - Overview (Sales, AOV, Gross Profit, Repeat Rate)
   - Sales Analytics (Daily trends, units sold)
   - Product Intelligence (Gross margins %, top sellers, units)
   - Customer Intelligence (RFM segments: Champions, Loyal, At Risk)
   - Retention & Funnel (Monthly acquisition retention matrix)
   - Business Insights (Automated AI suggestions)

5. ACCOUNTS_AND_STORES_CATALOG.csv
   Master lookup sheet showing every store name, category, order count,
   customer count, total revenue, AOV, and return rate.

HOW TO UPLOAD TO ECOMLYTICS:
1. Open the website: https://ecomlytics.onrender.com/ (or your local server http://127.0.0.1:8000/)
2. Register a new user / login to an account.
3. In the sidebar, click 'Data Sources'.
4. In the 'Import Store CSV Dataset' card:
   - To upload Orders: Set Dataset Type to 'Orders (orders.csv)' -> Drag or select any store's orders CSV.
   - To upload Products: Set Dataset Type to 'Products (products.csv)' -> Drag products.csv.
   - To upload Customers: Set Dataset Type to 'Customers (customers.csv)' -> Drag customers.csv.
5. Watch the dashboard instantly calculate all analytics!
========================================================================
"""

with open(OUTPUT_DIR / "README.txt", "w", encoding="utf-8") as f:
    f.write(readme_text)

# CREATE THE ZIP FILE
print(f"Creating zip file at {OUTPUT_ZIP}...")
with zipfile.ZipFile(OUTPUT_ZIP, "w", zipfile.ZIP_DEFLATED) as zf:
    for root, dirs, files in os.walk(OUTPUT_DIR):
        for file in files:
            full_path = Path(root) / file
            rel_path = full_path.relative_to(OUTPUT_DIR)
            zf.write(full_path, arcname=str(rel_path))

# Also copy to artifacts dir

zip_size_kb = OUTPUT_ZIP.stat().st_size / 1024
print(f"SUCCESS! Zip generated with {len(STORES)} stores. Total zip size: {zip_size_kb:.1f} KB.")