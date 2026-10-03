# VisionIQ RAG Corpus Specification Consistency Report

> **Generated at**: `2026-10-03 15:12:15Z`  
> **Corpus Location**: `data/corpus/`  
> **Rule**: Flag every numeric value or spec not present in `data/products/products.json`. Do not auto-fix; list for audit.

---

## 1. Executive Summary

| Metric | Count |
| :--- | :---: |
| **Total Products Audited** | 25 |
| **Total Markdown Documents Checked** | 100 |
| **Total Flagged Items** | 114 |
| **Plausible Procedural / Policy Numbers** (step #s, button timers, warranty durations) | 112 |
| **Unlisted Numeric Specifications** | 0 |
| **Unlisted Spec Tokens** (alphanumeric protocols, certifications, standards) | 2 |

---

## 2. Per-Product Audit Breakdown

### P001 — Sony WH-1000XM5 (Headphones)

#### `usage_guide.md` (1 flagged items)
| Line | Flagged Value | Classification | Context |
| :---: | :--- | :--- | :--- |
| 27 | `4` | Generic Procedural/Policy | ## 4. Recommended Use Cases & Scenarios |

#### `user_manual.md` (1 flagged items)
| Line | Flagged Value | Classification | Context |
| :---: | :--- | :--- | :--- |
| 48 | `4` | Generic Procedural/Policy | ## 4. Maintenance & Cleaning Instructions |

#### `warranty.md` (1 flagged items)
| Line | Flagged Value | Classification | Context |
| :---: | :--- | :--- | :--- |
| 28 | `4` | Generic Procedural/Policy | ## 4. How to File a Warranty Claim |

### P002 — Bose QuietComfort Ultra (Headphones)

#### `usage_guide.md` (1 flagged items)
| Line | Flagged Value | Classification | Context |
| :---: | :--- | :--- | :--- |
| 5 | `1` | Generic Procedural/Policy | ## 1. Ergonomics & Ideal Fit / Placement |

#### `user_manual.md` (2 flagged items)
| Line | Flagged Value | Classification | Context |
| :---: | :--- | :--- | :--- |
| 3 | `1` | Generic Procedural/Policy | ## 1. Product Overview & In the Box |
| 29 | `1` | Generic Procedural/Policy | 1. Charge the headphones |

#### `warranty.md` (3 flagged items)
| Line | Flagged Value | Classification | Context |
| :---: | :--- | :--- | :--- |
| 5 | `1` | Generic Procedural/Policy | ## 1. Warranty Coverage & Duration |
| 32 | `1` | Generic Procedural/Policy | 1. Gather required information: proof of purchase (retailer receipt or order confirmation), product serial number, date of purchase, and a detailed description of the problem. Include clear photos or short video clips that show the issue when applicable. |
| 33 | `1` | Generic Procedural/Policy | 2. Contact Bose customer support through official Bose channels for your region (online support portal, authorized retailer, or authorized service center). Provide the information collected in Step 1 and request a warranty evaluation. Bose may ask additional diagnostic questions. |

### P003 — Apple AirPods Max (Headphones)

No unlisted numeric values or spec tokens detected. All specs strictly match `products.json`.

### P004 — Sennheiser Momentum 4 Wireless (Headphones)

#### `usage_guide.md` (1 flagged items)
| Line | Flagged Value | Classification | Context |
| :---: | :--- | :--- | :--- |
| 3 | `1` | Generic Procedural/Policy | ## 1. Ergonomics & Ideal Fit / Placement |

#### `user_manual.md` (3 flagged items)
| Line | Flagged Value | Classification | Context |
| :---: | :--- | :--- | :--- |
| 3 | `1` | Generic Procedural/Policy | ## 1. Product Overview & In the Box |
| 16 | `USB-C` | Unlisted spec tokens | - USB-C charging cable |
| 26 | `1` | Generic Procedural/Policy | 1. Power on and enter pairing |

#### `warranty.md` (2 flagged items)
| Line | Flagged Value | Classification | Context |
| :---: | :--- | :--- | :--- |
| 5 | `1` | Generic Procedural/Policy | ## 1. Warranty Coverage & Duration |
| 29 | `1` | Generic Procedural/Policy | 1. Gather documentation: retain your original proof of purchase (retailer receipt or invoice), product serial number, and a detailed description of the issue. Photos or short video demonstrating the fault are helpful. |

### P005 — Audio-Technica ATH-M50xBT2 (Headphones)

#### `usage_guide.md` (1 flagged items)
| Line | Flagged Value | Classification | Context |
| :---: | :--- | :--- | :--- |
| 3 | `1` | Generic Procedural/Policy | ## 1. Ergonomics & Ideal Fit / Placement |

#### `user_manual.md` (2 flagged items)
| Line | Flagged Value | Classification | Context |
| :---: | :--- | :--- | :--- |
| 3 | `1` | Generic Procedural/Policy | ## 1. Product Overview & In the Box |
| 27 | `1` | Generic Procedural/Policy | 1. Charge and power on |

#### `warranty.md` (2 flagged items)
| Line | Flagged Value | Classification | Context |
| :---: | :--- | :--- | :--- |
| 5 | `1` | Generic Procedural/Policy | ## 1. Warranty Coverage & Duration |
| 32 | `1` | Generic Procedural/Policy | 1. Gather documentation: Keep your original proof of purchase (receipt or invoice), the product serial number (if present), and a clear description of the issue. Note the date of purchase and any steps you have already taken to troubleshoot. |

### P006 — Bowers & Wilkins Px7 S2e (Headphones)

#### `usage_guide.md` (1 flagged items)
| Line | Flagged Value | Classification | Context |
| :---: | :--- | :--- | :--- |
| 3 | `1` | Generic Procedural/Policy | ## 1. Ergonomics & Ideal Fit / Placement |

#### `user_manual.md` (2 flagged items)
| Line | Flagged Value | Classification | Context |
| :---: | :--- | :--- | :--- |
| 3 | `1` | Generic Procedural/Policy | ## 1. Product Overview & In the Box |
| 30 | `1` | Generic Procedural/Policy | 1. Charge and power on |

#### `warranty.md` (3 flagged items)
| Line | Flagged Value | Classification | Context |
| :---: | :--- | :--- | :--- |
| 5 | `1` | Generic Procedural/Policy | ## 1. Warranty Coverage & Duration |
| 34 | `1` | Generic Procedural/Policy | 1. Prepare required information: Locate your proof of purchase (receipt or invoice), the product serial number, and describe the issue. Where possible, include photos or short video demonstrating the fault and any error messages or behaviors. |
| 35 | `1` | Generic Procedural/Policy | 2. Contact support: Reach out to Bowers & Wilkins customer support or your authorized dealer to open a warranty claim. Provide the information prepared in step 1 and follow any diagnostic instructions provided by support. |

### P007 — Herman Miller Aeron Chair (Chairs)

#### `usage_guide.md` (2 flagged items)
| Line | Flagged Value | Classification | Context |
| :---: | :--- | :--- | :--- |
| 13 | `4` | Generic Procedural/Policy | 4. Ensure your feet rest flat on the floor or a footrest; knees should be roughly level with hips. |
| 28 | `4` | Generic Procedural/Policy | ## 4. Recommended Use Cases & Scenarios |

#### `user_manual.md` (1 flagged items)
| Line | Flagged Value | Classification | Context |
| :---: | :--- | :--- | :--- |
| 46 | `4` | Generic Procedural/Policy | ## 4. Maintenance & Cleaning Instructions |

#### `warranty.md` (1 flagged items)
| Line | Flagged Value | Classification | Context |
| :---: | :--- | :--- | :--- |
| 29 | `4` | Generic Procedural/Policy | ## 4. How to File a Warranty Claim |

### P008 — Steelcase Gesture (Chairs)

#### `usage_guide.md` (1 flagged items)
| Line | Flagged Value | Classification | Context |
| :---: | :--- | :--- | :--- |
| 42 | `5` | Generic Procedural/Policy | ## 5. Do's and Don'ts for Daily Use |

#### `user_manual.md` (1 flagged items)
| Line | Flagged Value | Classification | Context |
| :---: | :--- | :--- | :--- |
| 59 | `5` | Generic Procedural/Policy | ## 5. Basic Troubleshooting |

#### `warranty.md` (1 flagged items)
| Line | Flagged Value | Classification | Context |
| :---: | :--- | :--- | :--- |
| 50 | `5` | Generic Procedural/Policy | ## 5. Customer Support & Service Channels |

### P009 — Secretlab Titan Evo (Chairs)

No unlisted numeric values or spec tokens detected. All specs strictly match `products.json`.

### P010 — Autonomous ErgoChair Pro (Chairs)

#### `usage_guide.md` (1 flagged items)
| Line | Flagged Value | Classification | Context |
| :---: | :--- | :--- | :--- |
| 30 | `4` | Generic Procedural/Policy | ## 4. Recommended Use Cases & Scenarios |

#### `user_manual.md` (1 flagged items)
| Line | Flagged Value | Classification | Context |
| :---: | :--- | :--- | :--- |
| 61 | `4` | Generic Procedural/Policy | ## 4. Maintenance & Cleaning Instructions |

#### `warranty.md` (1 flagged items)
| Line | Flagged Value | Classification | Context |
| :---: | :--- | :--- | :--- |
| 29 | `4` | Generic Procedural/Policy | ## 4. How to File a Warranty Claim |

### P011 — IKEA Markus (Chairs)

#### `usage_guide.md` (2 flagged items)
| Line | Flagged Value | Classification | Context |
| :---: | :--- | :--- | :--- |
| 17 | `3` | Generic Procedural/Policy | ## 3. Best Practices for Product Longevity |
| 32 | `5` | Generic Procedural/Policy | ## 5. Do's and Don'ts for Daily Use |

#### `user_manual.md` (3 flagged items)
| Line | Flagged Value | Classification | Context |
| :---: | :--- | :--- | :--- |
| 36 | `3` | Generic Procedural/Policy | 3. Attach seat and back: Position the seat and back assembly onto the mounting column and secure using the included fasteners. Adjust and tighten all visible fasteners according to the leaflet, then sit gently to confirm stability. Set initial seat height and engage the synchronized tilt lock to a comfortable upright position. |
| 43 | `3` | Generic Procedural/Policy | ## 3. Core Controls & Daily Operation |
| 75 | `5` | Generic Procedural/Policy | ## 5. Basic Troubleshooting |

#### `warranty.md` (3 flagged items)
| Line | Flagged Value | Classification | Context |
| :---: | :--- | :--- | :--- |
| 21 | `3` | Generic Procedural/Policy | ## 3. What Is Excluded (Misuse, wear & tear, unauthorized modifications) |
| 37 | `3` | Generic Procedural/Policy | 3. Follow instructions from IKEA: IKEA will advise whether the item should be inspected in-store, returned, or scheduled for in-home service (where available). If a claim is accepted, IKEA will arrange repair, replacement, or refund according to this warranty. You may be required to return the product or make it available for inspection. |
| 41 | `5` | Generic Procedural/Policy | ## 5. Customer Support & Service Channels |

### P012 — Haworth Fern (Chairs)

No unlisted numeric values or spec tokens detected. All specs strictly match `products.json`.

### P013 — Humanscale Freedom (Chairs)

No unlisted numeric values or spec tokens detected. All specs strictly match `products.json`.

### P014 — Nike Air Max 270 (Shoes)

#### `usage_guide.md` (2 flagged items)
| Line | Flagged Value | Classification | Context |
| :---: | :--- | :--- | :--- |
| 23 | `4` | Generic Procedural/Policy | ## 4. Recommended Use Cases & Scenarios |
| 28 | `5` | Generic Procedural/Policy | ## 5. Do's and Don'ts for Daily Use |

#### `user_manual.md` (2 flagged items)
| Line | Flagged Value | Classification | Context |
| :---: | :--- | :--- | :--- |
| 38 | `4` | Generic Procedural/Policy | ## 4. Maintenance & Cleaning Instructions |
| 54 | `5` | Generic Procedural/Policy | ## 5. Basic Troubleshooting |

#### `warranty.md` (2 flagged items)
| Line | Flagged Value | Classification | Context |
| :---: | :--- | :--- | :--- |
| 28 | `4` | Generic Procedural/Policy | ## 4. How to File a Warranty Claim |
| 35 | `5` | Generic Procedural/Policy | ## 5. Customer Support & Service Channels |

### P015 — Adidas Ultraboost Light (Shoes)

#### `usage_guide.md` (1 flagged items)
| Line | Flagged Value | Classification | Context |
| :---: | :--- | :--- | :--- |
| 28 | `4` | Generic Procedural/Policy | ## 4. Recommended Use Cases & Scenarios |

#### `user_manual.md` (1 flagged items)
| Line | Flagged Value | Classification | Context |
| :---: | :--- | :--- | :--- |
| 47 | `4` | Generic Procedural/Policy | ## 4. Maintenance & Cleaning Instructions |

#### `warranty.md` (1 flagged items)
| Line | Flagged Value | Classification | Context |
| :---: | :--- | :--- | :--- |
| 27 | `4` | Generic Procedural/Policy | ## 4. How to File a Warranty Claim |

### P016 — New Balance 990v6 (Shoes)

#### `faq.md` (1 flagged items)
| Line | Flagged Value | Classification | Context |
| :---: | :--- | :--- | :--- |
| 4 | `GPS` | Unlisted spec tokens | A: No. The New Balance 990v6 are a heritage lifestyle and running shoe without built-in electronics, wireless connectivity, or batteries. If you want to track runs or gait data, use an external wearable (wrist GPS watch, phone app, or clip-on pod) designed to be attached to clothing or shoes — the 990v6 themselves do not provide electronic tracking. |

#### `usage_guide.md` (1 flagged items)
| Line | Flagged Value | Classification | Context |
| :---: | :--- | :--- | :--- |
| 32 | `5` | Generic Procedural/Policy | ## 5. Do's and Don'ts for Daily Use |

#### `user_manual.md` (1 flagged items)
| Line | Flagged Value | Classification | Context |
| :---: | :--- | :--- | :--- |
| 64 | `5` | Generic Procedural/Policy | ## 5. Basic Troubleshooting |

#### `warranty.md` (1 flagged items)
| Line | Flagged Value | Classification | Context |
| :---: | :--- | :--- | :--- |
| 37 | `5` | Generic Procedural/Policy | ## 5. Customer Support & Service Channels |

### P017 — On Cloudmonster (Shoes)

#### `usage_guide.md` (3 flagged items)
| Line | Flagged Value | Classification | Context |
| :---: | :--- | :--- | :--- |
| 3 | `1` | Generic Procedural/Policy | ## 1. Ergonomics & Ideal Fit / Placement |
| 25 | `3` | Generic Procedural/Policy | ## 3. Best Practices for Product Longevity |
| 32 | `4` | Generic Procedural/Policy | ## 4. Recommended Use Cases & Scenarios |

#### `user_manual.md` (5 flagged items)
| Line | Flagged Value | Classification | Context |
| :---: | :--- | :--- | :--- |
| 3 | `1` | Generic Procedural/Policy | ## 1. Product Overview & In the Box |
| 19 | `1` | Generic Procedural/Policy | 1. Inspect and fit |
| 26 | `3` | Generic Procedural/Policy | 3. Break-in routine |
| 29 | `3` | Generic Procedural/Policy | ## 3. Core Controls & Daily Operation |
| 44 | `4` | Generic Procedural/Policy | ## 4. Maintenance & Cleaning Instructions |

#### `warranty.md` (5 flagged items)
| Line | Flagged Value | Classification | Context |
| :---: | :--- | :--- | :--- |
| 7 | `1` | Generic Procedural/Policy | ## 1. Warranty Coverage & Duration |
| 26 | `3` | Generic Procedural/Policy | ## 3. What Is Excluded (Misuse, wear & tear, unauthorized modifications) |
| 36 | `4` | Generic Procedural/Policy | ## 4. How to File a Warranty Claim |
| 37 | `1` | Generic Procedural/Policy | 1. Gather documentation: Keep your original proof of purchase (receipt or order confirmation) and prepare clear photos that show the issue and the shoe’s overall condition. Note the product details (Product ID: P017, On Cloudmonster, Brand: On Running), size, and the date of purchase. |
| 39 | `3` | Generic Procedural/Policy | 3. Follow instructions: The support team will review your submission and advise whether you should ship the product for inspection, bring it to an authorized service location, or receive other instructions. If return shipping is required, On Running or the retailer will indicate whether shipping costs are the responsibility of the customer or covered due to a confirmed defect. |

### P018 — Hoka Clifton 9 (Shoes)

#### `usage_guide.md` (2 flagged items)
| Line | Flagged Value | Classification | Context |
| :---: | :--- | :--- | :--- |
| 3 | `1` | Generic Procedural/Policy | ## 1. Ergonomics & Ideal Fit / Placement |
| 24 | `3` | Generic Procedural/Policy | ## 3. Best Practices for Product Longevity |

#### `user_manual.md` (4 flagged items)
| Line | Flagged Value | Classification | Context |
| :---: | :--- | :--- | :--- |
| 3 | `1` | Generic Procedural/Policy | ## 1. Product Overview & In the Box |
| 19 | `1` | Generic Procedural/Policy | 1. Inspect the shoes |
| 25 | `3` | Generic Procedural/Policy | 3. Short indoor test |
| 28 | `3` | Generic Procedural/Policy | ## 3. Core Controls & Daily Operation |

#### `warranty.md` (4 flagged items)
| Line | Flagged Value | Classification | Context |
| :---: | :--- | :--- | :--- |
| 5 | `1` | Generic Procedural/Policy | ## 1. Warranty Coverage & Duration |
| 17 | `3` | Generic Procedural/Policy | ## 3. What Is Excluded |
| 29 | `1` | Generic Procedural/Policy | 1. Gather information: retain your original proof of purchase (receipt or order confirmation), note the purchase date, and prepare clear photographs showing the issue (multiple angles of the affected area and an overall view of the shoe). Include product details (model name: Hoka Clifton 9) and the size if relevant. |
| 31 | `3` | Generic Procedural/Policy | 3. Follow evaluation instructions: after submission, Hoka or the retailer will acknowledge receipt and may request additional information or return of the product for inspection. Pack the product securely (original packaging if available) and follow shipping instructions provided by support. Do not modify or attempt unauthorized repairs while a claim is pending. |

### P019 — Salomon XT-6 (Shoes)

#### `usage_guide.md` (3 flagged items)
| Line | Flagged Value | Classification | Context |
| :---: | :--- | :--- | :--- |
| 3 | `1` | Generic Procedural/Policy | ## 1. Ergonomics & Ideal Fit / Placement |
| 11 | `2` | Generic Procedural/Policy | ## 2. Optimal Performance & Environmental Recommendations |
| 25 | `4` | Generic Procedural/Policy | ## 4. Recommended Use Cases & Scenarios |

#### `user_manual.md` (5 flagged items)
| Line | Flagged Value | Classification | Context |
| :---: | :--- | :--- | :--- |
| 3 | `1` | Generic Procedural/Policy | ## 1. Product Overview & In the Box |
| 15 | `2` | Generic Procedural/Policy | ## 2. Setup & Initial Configuration |
| 18 | `1` | Generic Procedural/Policy | 1. Inspect: Remove shoes from the box and inspect for any shipping damage. Verify both left and right shoes are present and the Quicklace system functions by pulling the lace to tighten and releasing the toggle to lock. |
| 19 | `2` | Generic Procedural/Policy | 2. Fit check: Put each shoe on and ensure the EndoFit internal sleeve comfortably hugs your foot. Walk a few steps on a flat surface while standing to confirm there are no pressure points. Adjust the Quicklace until fit feels secure but not constrictive. |
| 47 | `4` | Generic Procedural/Policy | ## 4. Maintenance & Cleaning Instructions |

#### `warranty.md` (5 flagged items)
| Line | Flagged Value | Classification | Context |
| :---: | :--- | :--- | :--- |
| 5 | `1` | Generic Procedural/Policy | ## 1. Warranty Coverage & Duration |
| 10 | `2` | Generic Procedural/Policy | ## 2. What Is Covered |
| 31 | `4` | Generic Procedural/Policy | ## 4. How to File a Warranty Claim |
| 32 | `1` | Generic Procedural/Policy | 1. Gather documentation and evidence: |
| 36 | `2` | Generic Procedural/Policy | 2. Contact the place of purchase or Salomon customer support: |

### P020 — Apple Watch Ultra 2 (Watches)

No unlisted numeric values or spec tokens detected. All specs strictly match `products.json`.

### P021 — Garmin Fenix 7 Pro Solar (Watches)

No unlisted numeric values or spec tokens detected. All specs strictly match `products.json`.

### P022 — Seiko Prospex Speedtimer Solar Chronograph (Watches)

#### `usage_guide.md` (1 flagged items)
| Line | Flagged Value | Classification | Context |
| :---: | :--- | :--- | :--- |
| 31 | `4` | Generic Procedural/Policy | ## 4. Recommended Use Cases & Scenarios |

#### `user_manual.md` (1 flagged items)
| Line | Flagged Value | Classification | Context |
| :---: | :--- | :--- | :--- |
| 53 | `4` | Generic Procedural/Policy | ## 4. Maintenance & Cleaning Instructions |

#### `warranty.md` (1 flagged items)
| Line | Flagged Value | Classification | Context |
| :---: | :--- | :--- | :--- |
| 30 | `4` | Generic Procedural/Policy | ## 4. How to File a Warranty Claim |

### P023 — Samsung Galaxy Watch 6 Classic (Watches)

#### `usage_guide.md` (2 flagged items)
| Line | Flagged Value | Classification | Context |
| :---: | :--- | :--- | :--- |
| 9 | `2` | Generic Procedural/Policy | ## 2. Optimal Performance & Environmental Recommendations |
| 19 | `3` | Generic Procedural/Policy | ## 3. Best Practices for Product Longevity |

#### `user_manual.md` (4 flagged items)
| Line | Flagged Value | Classification | Context |
| :---: | :--- | :--- | :--- |
| 21 | `2` | Generic Procedural/Policy | ## 2. Setup & Initial Configuration |
| 24 | `2` | Generic Procedural/Policy | 2. Pair with your phone |
| 26 | `3` | Generic Procedural/Policy | 3. Complete initial configuration |
| 33 | `3` | Generic Procedural/Policy | ## 3. Core Controls & Daily Operation |

#### `warranty.md` (4 flagged items)
| Line | Flagged Value | Classification | Context |
| :---: | :--- | :--- | :--- |
| 10 | `2` | Generic Procedural/Policy | ## 2. What Is Covered |
| 25 | `3` | Generic Procedural/Policy | ## 3. What Is Excluded |
| 37 | `2` | Generic Procedural/Policy | 2. Contact Samsung support: Reach out to Samsung Customer Support via the official regional support channels (website or authorized support centers). Provide the purchase information, serial number, and a description of the fault to receive initial troubleshooting and eligibility confirmation. |
| 38 | `3` | Generic Procedural/Policy | 3. Follow return instructions: If instructed to return the device, follow Samsung’s packaging and shipping guidelines. Use original packaging if available and remove personal data. You may be provided with an authorized service center location or shipping label. Do not send accessories unless requested. Service timelines, shipping responsibilities, and any charges for out-of-warranty service will be communicated during the claim process. |

### P024 — Tissot PRX Powermatic 80 (Watches)

#### `usage_guide.md` (2 flagged items)
| Line | Flagged Value | Classification | Context |
| :---: | :--- | :--- | :--- |
| 8 | `2` | Generic Procedural/Policy | ## 2. Optimal Performance & Environmental Recommendations |
| 25 | `5` | Generic Procedural/Policy | ## 5. Do's and Don'ts for Daily Use |

#### `user_manual.md` (3 flagged items)
| Line | Flagged Value | Classification | Context |
| :---: | :--- | :--- | :--- |
| 19 | `2` | Generic Procedural/Policy | ## 2. Setup & Initial Configuration |
| 24 | `2` | Generic Procedural/Policy | 2. Set the time: |
| 53 | `5` | Generic Procedural/Policy | ## 5. Basic Troubleshooting |

#### `warranty.md` (3 flagged items)
| Line | Flagged Value | Classification | Context |
| :---: | :--- | :--- | :--- |
| 8 | `2` | Generic Procedural/Policy | ## 2. What Is Covered |
| 30 | `2` | Generic Procedural/Policy | 2. Contact the point of sale or an authorized Tissot service center: present your documentation and a description of the problem. If instructed, ship the watch in secure packaging with a copy of proof of purchase and the warranty card. Retain copies of all shipping receipts and tracking information. |
| 35 | `5` | Generic Procedural/Policy | ## 5. Customer Support & Service Channels |

### P025 — Casio G-Shock GA-2100 'CasiOak' (Watches)

No unlisted numeric values or spec tokens detected. All specs strictly match `products.json`.

