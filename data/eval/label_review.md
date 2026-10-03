# VisionIQ RAG Evaluation — Label Review Sheet

> **Labels are LLM-proposed from full product docs (no retrieval used) and must be human-reviewed.**

- **Total Rows**: 40
- **Total LLM Tokens Used**: 189,701 (Prompt: 171,934, Completion: 17,767)

## 1. Flagged Rows Requiring Immediate Review

The following **13 rows** contain flags (`RELABELED`, `CHECK-OOD`, `CHECK-KW`, `CHECK-NAME`, `VERIFY`):

| ID | Split | QType | Question | Flags / Notes | Reason Summary |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Q03** | `dev` | `out_of_docs` | Is the charging cable Type-C or Micro-USB? | `VERIFY RELABELED` | Not answerable from the provided catalog or document chunks. None of the chunks or the PRODUCTS.JSON entry explicitly state whether the charging cable is Type‑C or Micro‑USB. The FAQ and user manual note to consult the included documentation or Audio‑Technica support for charging connector details (see P005_faq_001 and P005_user_manual_001), but do not specify the connector type. |
| **Q07** | `dev` | `out_of_docs` | Are these shoes waterproof or just water-resistant? | `VERIFY RELABELED` | The provided catalog and document chunks do not explicitly state whether the shoes are 'waterproof' or 'water-resistant'. Related statements (e.g., 'Continental Better Rubber outsole provides grip on wet and dry surfaces' and that the 'PRIMEKNIT+ upper is a textile—prolonged exposure to heavy rain or standing water may affect comfort and drying time' and 'Don’t subject the shoes to prolonged immersion') appear in the docs but do not directly use or define 'waterproof' or 'water-resistant', so the question cannot be answered directly from the materials. |
| **Q08** | `test` | `spec` | What is the heel drop of these shoes in millimeters? | `VERIFY` | The product specifications in the catalog list the drop as "6mm", and chunk P017_user_manual_001 explicitly includes "Drop: 6mm" in the product overview. |
| **Q09** | `dev` | `out_of_docs` | Do these shoes have a carbon fiber plate in the sole? | `VERIFY RELABELED` | The product catalog and all document chunks do not explicitly state whether the XT-6 includes or excludes a carbon fiber plate. The specifications list the chassis as "Agile Chassis System (ACS) with EVA cushioning" and other chunks describe ACS/EVA and outsole features, but none explicitly mention a carbon fiber plate (or explicitly state its absence). Therefore the question cannot be answered directly from the provided documents. |
| **Q12** | `test` | `out_of_docs` | Is the watch glass made of sapphire? | `VERIFY RELABELED` | The provided PRODUCTS.JSON and all corpus chunks do not state the crystal/glass material or use the term 'sapphire' (nor any alternative like 'mineral' or 'hesalite'). The exact answer is not explicitly present, so it cannot be answered from the supplied documents without inference. |
| **Q13** | `dev` | `out_of_docs` | How do I reset these headphones to factory settings? | `RELABELED` | None of the provided catalog entry or document chunks include a procedure or mention for performing a factory reset / "reset to factory settings." The documents only show basic troubleshooting (power off/on, re-pairing, remove device from Bluetooth list, restart devices) (e.g. P002_user_manual_002, P002_faq_001) but do not provide any explicit factory-reset steps or the phrase "factory reset" or "reset to factory settings." Therefore the exact procedural answer is not present in the corpus. |
| **Q21** | `dev` | `out_of_docs` | Flat feet ke liye laces baandhne ka koi specific technique hai? | `hinglish VERIFY RELABELED` | The provided catalog and document chunks give general lacing and fit guidance (e.g., loosen laces, tighten progressively from forefoot to ankle, re-lace to relieve pressure, tighten midfoot for heel slip) but do not explicitly mention any lacing technique or specific instructions for 'flat feet' (flatfoot/overpronation). The exact question—whether there is a specific lacing technique for flat feet—is not directly answered in the documents, so it is not answerable from the provided material. |
| **Q22** | `test` | `out_of_docs` | How do I change the time format from 12-hour to 24-hour? | `RELABELED` | The provided product catalog and all document chunks do not include any instructions or information about changing the time format (12-hour vs 24-hour). Settings and controls are mentioned (e.g., Action Button in Settings → Action Button), but no chunk states how to change the watch's time format, so the question cannot be answered from the given documents. |
| **Q24** | `test` | `out_of_docs` | My screen is stuck on the logo how do I restart the watch? | `RELABELED` | The documents mention restarting the watch as a general troubleshooting step (see P023_faq_003, P023_user_manual_003, P023_faq_001), but none of the provided chunks give explicit, step-by-step instructions for restarting or force-restarting the watch when it is stuck on the logo. The exact method to restart the device is not stated in the corpus, so the question is not directly answerable from the provided content. |
| **Q34** | `test` | `unknown_product` | Is the Sony FX3 camera good for low light shooting? | `CHECK-NAME` | Unknown product question evaluated without catalog docs. |
| **Q35** | `dev` | `unknown_product` | Does the Sony WH-1000XM4 support multipoint Bluetooth? | `near-neighbor CHECK-NAME` | Unknown product question evaluated without catalog docs. |
| **Q36** | `dev` | `unknown_product` | How long is the warranty on the Bose QuietComfort 45? | `near-neighbor CHECK-NAME` | Unknown product question evaluated without catalog docs. |
| **Q40** | `dev` | `unknown_product` | How do I adjust the lumbar support on the Herman Miller Embody? | `near-neighbor CHECK-NAME` | Unknown product question evaluated without catalog docs. |

---

## 2. Complete Evaluation Dataset Review (All 40 Rows)

### [Q01] What is the maximum battery life on a single charge?
- **Split**: `dev`
- **Question Type**: `spec`
- **Product**: P001 (Sony WH-1000XM5)
- **Flags / Notes**: `None`
- **Model Reason**: *The product specifications explicitly list battery life as "30 hours" in the catalog; chunk P001_user_manual_001 contains the direct statement "Battery life: 30 hours." This single chunk directly answers the question.*
- **Gold Keywords**: `30 hours`
- **Gold Chunk IDs**: `P001_user_manual_001`

**Proposed Chunk Snippets (first 300 chars):**
  * **`P001_user_manual_001`** (user_manual - Setup & Initial Configuration): "## 1. Product Overview & In the Box  Overview - The Sony WH-1000XM5 are industry-leading wireless noise-canceling over-ear headphones. They combine Active Noise Cancellation (ANC), two processors and 8 microphones to deliver exceptional sound quality and call clarity. - Key features include Auto NC ..."

---

### [Q02] Do these headphones support active noise cancellation (ANC)?
- **Split**: `test`
- **Question Type**: `spec`
- **Product**: P003 (Apple AirPods Max)
- **Flags / Notes**: `None`
- **Model Reason**: *The product catalog explicitly lists noise_cancellation as "Active Noise Cancellation" in the specifications, and chunk P003_user_manual_001 directly states the AirPods Max are designed with Active Noise Cancellation.*
- **Gold Keywords**: `Active Noise Cancellation`
- **Gold Chunk IDs**: `P003_user_manual_001`

**Proposed Chunk Snippets (first 300 chars):**
  * **`P003_user_manual_001`** (user_manual - Setup & Initial Configuration (include numbered procedural steps 1., 2., 3.)): "## 1. Product Overview & In the Box  Apple AirPods Max are over-ear headphones designed for high-fidelity audio with Active Noise Cancellation, Transparency mode, and personalized spatial audio with dynamic head tracking. Key elements and materials include a knit-mesh canopy and memory foam ear cush..."

---

### [Q03] Is the charging cable Type-C or Micro-USB?
- **Split**: `dev`
- **Question Type**: `out_of_docs` (RELABELED from `spec`)
- **Product**: P005 (Audio-Technica ATH-M50xBT2)
- **Flags / Notes**: `VERIFY RELABELED`
- **Model Reason**: *Not answerable from the provided catalog or document chunks. None of the chunks or the PRODUCTS.JSON entry explicitly state whether the charging cable is Type‑C or Micro‑USB. The FAQ and user manual note to consult the included documentation or Audio‑Technica support for charging connector details (see P005_faq_001 and P005_user_manual_001), but do not specify the connector type.*
- **Gold Keywords**: `None`
- **Gold Chunk IDs**: `None`

---

### [Q04] What is the maximum weight capacity of this chair?
- **Split**: `dev`
- **Question Type**: `spec`
- **Product**: P007 (Herman Miller Aeron Chair)
- **Flags / Notes**: `None`
- **Model Reason**: *The PRODUCTS.JSON specifications include "max_load": "159 kg (350 lbs)" and user manual chunk P007_user_manual_001 explicitly states "Maximum load capacity: 159 kg (350 lbs)." These directly answer the question.*
- **Gold Keywords**: `159 kg (350 lbs)`
- **Gold Chunk IDs**: `P007_user_manual_001`

**Proposed Chunk Snippets (first 300 chars):**
  * **`P007_user_manual_001`** (user_manual - Setup & Initial Configuration): "## 1. Product Overview & In the Box  The Herman Miller Aeron Chair is an ergonomic seating solution engineered for human body support. Key product characteristics (from manufacturer specifications): - Material: 8Z Pellicle elastomeric mesh, recycled aluminum base. - Support system: PostureFit SL sac..."

---

### [Q05] Are the armrests adjustable in 4D or just height?
- **Split**: `test`
- **Question Type**: `spec`
- **Product**: P012 (Haworth Fern)
- **Flags / Notes**: `None`
- **Model Reason**: *The product specifications explicitly list '4D armrests' (see PRODUCTS.JSON) and the FAQ chunk P012_faq_001 states the chair includes '4D armrests', directly answering that the armrests are 4D adjustable rather than only height-adjustable.*
- **Gold Keywords**: `4D armrests`
- **Gold Chunk IDs**: `P012_faq_001`

**Proposed Chunk Snippets (first 300 chars):**
  * **`P012_faq_001`** (faq - Q: What are the weight and load limits?): "## Q: What is the Haworth Fern designed for?  A: The Haworth Fern is a nature-inspired ergonomic executive chair built around a Wave Suspension back system that responds to subtle torso movement. Its edgeless flex-back design and Frond and Stem flexible back spine support are intended to provide con..."

---

### [Q06] What material is the seat made of?
- **Split**: `dev`
- **Question Type**: `spec`
- **Product**: P010 (Autonomous ErgoChair Pro)
- **Flags / Notes**: `None`
- **Model Reason**: *The product materials are explicitly listed in the catalog/chunks; P010_user_manual_001 states: "Materials: Breathable woven mesh, molded foam seat, nylon frame." The verbatim spec phrase in PRODUCTS.JSON is "molded foam seat."*
- **Gold Keywords**: `molded foam seat`
- **Gold Chunk IDs**: `P010_user_manual_001`

**Proposed Chunk Snippets (first 300 chars):**
  * **`P010_user_manual_001`** (user_manual - Setup & Initial Configuration): "## 1. Product Overview & In the Box  Product: Autonomous ErgoChair Pro   Brand: Autonomous   Category: Chairs  Overview - Fully customizable ergonomic office chair designed for active lumbar support. - Responsive Korean mesh back and adjustable lumbar cushion for dynamic comfort. - Materials: Breath..."

---

### [Q07] Are these shoes waterproof or just water-resistant?
- **Split**: `dev`
- **Question Type**: `out_of_docs` (RELABELED from `spec`)
- **Product**: P015 (Adidas Ultraboost Light)
- **Flags / Notes**: `VERIFY RELABELED`
- **Model Reason**: *The provided catalog and document chunks do not explicitly state whether the shoes are 'waterproof' or 'water-resistant'. Related statements (e.g., 'Continental Better Rubber outsole provides grip on wet and dry surfaces' and that the 'PRIMEKNIT+ upper is a textile—prolonged exposure to heavy rain or standing water may affect comfort and drying time' and 'Don’t subject the shoes to prolonged immersion') appear in the docs but do not directly use or define 'waterproof' or 'water-resistant', so the question cannot be answered directly from the materials.*
- **Gold Keywords**: `None`
- **Gold Chunk IDs**: `None`

---

### [Q08] What is the heel drop of these shoes in millimeters?
- **Split**: `test`
- **Question Type**: `spec`
- **Product**: P017 (On Cloudmonster)
- **Flags / Notes**: `VERIFY`
- **Model Reason**: *The product specifications in the catalog list the drop as "6mm", and chunk P017_user_manual_001 explicitly includes "Drop: 6mm" in the product overview.*
- **Gold Keywords**: `6mm`
- **Gold Chunk IDs**: `P017_user_manual_001`

**Proposed Chunk Snippets (first 300 chars):**
  * **`P017_user_manual_001`** (user_manual - Core Controls & Daily Operation): "## 1. Product Overview & In the Box  On Cloudmonster is a maximum-cushioning road running shoe engineered for big rebound and a pronounced forward roll. Key construction highlights: - Upper: Recycled polyester engineered mesh - Midsole: Helion superfoam with CloudTec pods - Speedboard: Snappy polypr..."

---

### [Q09] Do these shoes have a carbon fiber plate in the sole?
- **Split**: `dev`
- **Question Type**: `out_of_docs` (RELABELED from `spec`)
- **Product**: P019 (Salomon XT-6)
- **Flags / Notes**: `VERIFY RELABELED`
- **Model Reason**: *The product catalog and all document chunks do not explicitly state whether the XT-6 includes or excludes a carbon fiber plate. The specifications list the chassis as "Agile Chassis System (ACS) with EVA cushioning" and other chunks describe ACS/EVA and outsole features, but none explicitly mention a carbon fiber plate (or explicitly state its absence). Therefore the question cannot be answered directly from the provided documents.*
- **Gold Keywords**: `None`
- **Gold Chunk IDs**: `None`

---

### [Q10] Does the smartwatch have built-in GPS or does it use connected GPS?
- **Split**: `dev`
- **Question Type**: `spec`
- **Product**: P021 (Garmin Fenix 7 Pro Solar)
- **Flags / Notes**: `None`
- **Model Reason**: *The product overview in the user manual (chunk P021_user_manual_001) explicitly calls the device a "Multisport GPS smartwatch" and lists "Multi-band GNSS with SatIQ" as a sensor, which directly indicates built-in GPS. Those phrases also appear verbatim in the catalog entry.*
- **Gold Keywords**: `Multisport GPS smartwatch|Multi-band GNSS with SatIQ`
- **Gold Chunk IDs**: `P021_user_manual_001`

**Proposed Chunk Snippets (first 300 chars):**
  * **`P021_user_manual_001`** (user_manual - Setup & Initial Configuration): "## 1. Product Overview & In the Box  Overview - The Garmin Fenix 7 Pro Solar is a multisport GPS smartwatch featuring a Power Glass solar charging lens, a built-in multi-LED variable intensity flashlight, and advanced endurance training analytics. - Case: 47mm fiber-reinforced polymer with titanium ..."

---

### [Q11] What is the screen size and resolution of this watch?
- **Split**: `test`
- **Question Type**: `spec`
- **Product**: P023 (Samsung Galaxy Watch 6 Classic)
- **Flags / Notes**: `None`
- **Model Reason**: *The product catalog explicitly lists the display as "1.5-inch Super AMOLED (480x480), Sapphire Crystal". The same specification is stated verbatim in chunk P023_user_manual_001 under Product overview, so the screen size and resolution are directly answerable from the provided documents.*
- **Gold Keywords**: `1.5-inch|480x480|Super AMOLED`
- **Gold Chunk IDs**: `P023_user_manual_001`

**Proposed Chunk Snippets (first 300 chars):**
  * **`P023_user_manual_001`** (user_manual - Setup & Initial Configuration): "## 1. Product Overview & In the Box  Product overview - Model: Samsung Galaxy Watch 6 Classic - Case: 47mm Stainless Steel - Display: 1.5-inch Super AMOLED (480x480) with Sapphire Crystal - Battery Life: Up to 40 hours - Water & durability: 5ATM + IP68, MIL-STD-810H certified - Sensors: Samsung BioA..."

---

### [Q12] Is the watch glass made of sapphire?
- **Split**: `test`
- **Question Type**: `out_of_docs` (RELABELED from `spec`)
- **Product**: P025 (Casio G-Shock GA-2100 'CasiOak')
- **Flags / Notes**: `VERIFY RELABELED`
- **Model Reason**: *The provided PRODUCTS.JSON and all corpus chunks do not state the crystal/glass material or use the term 'sapphire' (nor any alternative like 'mineral' or 'hesalite'). The exact answer is not explicitly present, so it cannot be answered from the supplied documents without inference.*
- **Gold Keywords**: `None`
- **Gold Chunk IDs**: `None`

---

### [Q13] How do I reset these headphones to factory settings?
- **Split**: `dev`
- **Question Type**: `out_of_docs` (RELABELED from `procedural`)
- **Product**: P002 (Bose QuietComfort Ultra)
- **Flags / Notes**: `RELABELED`
- **Model Reason**: *None of the provided catalog entry or document chunks include a procedure or mention for performing a factory reset / "reset to factory settings." The documents only show basic troubleshooting (power off/on, re-pairing, remove device from Bluetooth list, restart devices) (e.g. P002_user_manual_002, P002_faq_001) but do not provide any explicit factory-reset steps or the phrase "factory reset" or "reset to factory settings." Therefore the exact procedural answer is not present in the corpus.*
- **Gold Keywords**: `None`
- **Gold Chunk IDs**: `None`

---

### [Q14] Headphones phone se connect nahi ho rahe pair kaise karu?
- **Split**: `test`
- **Question Type**: `procedural`
- **Product**: P004 (Sennheiser Momentum 4 Wireless)
- **Flags / Notes**: `hinglish`
- **Model Reason**: *P004_user_manual_001 gives explicit pairing steps (power on, enter pairing mode, enable Bluetooth on phone, select 'Sennheiser Momentum 4 Wireless'). P004_user_manual_002 provides troubleshooting if pairing fails (ensure pairing mode/visibility, toggle Bluetooth, remove previous pairing and re-scan). These chunks directly answer how to pair when not connecting.*
- **Gold Keywords**: `None`
- **Gold Chunk IDs**: `P004_user_manual_001, P004_user_manual_002`

**Proposed Chunk Snippets (first 300 chars):**
  * **`P004_user_manual_001`** (user_manual - Setup & Initial Configuration): "## 1. Product Overview & In the Box  Product overview - Model: Sennheiser Momentum 4 Wireless - Type: Over-Ear - Driver size: 42mm transducer system designed for superior dynamics and clarity - Connectivity: Bluetooth 5.2 with aptX Adaptive support - Noise cancellation: Adaptive Hybrid ANC - Battery..."
  * **`P004_user_manual_002`** (user_manual - Basic Troubleshooting): "Tips - For best results, ensure your source device’s Bluetooth software is up to date and aptX Adaptive is enabled if supported. - If your source device prompts for any permissions, allow them to ensure full functionality of call microphones and control features.  ## 3. Core Controls & Daily Operati..."

---

### [Q15] How do I replace the ear cushions when they tear?
- **Split**: `dev`
- **Question Type**: `procedural`
- **Product**: P006 (Bowers & Wilkins Px7 S2e)
- **Flags / Notes**: `None`
- **Model Reason**: *The product manual chunk P006_user_manual_002 explicitly states: 'Service: For repairs or replacement parts, contact an authorized Bowers & Wilkins service center or your retailer.' The corpus contains no step-by-step ear-cushion removal or replacement instructions, so the documented procedure is to contact an authorized service center or your retailer for replacement parts or service.*
- **Gold Keywords**: `None`
- **Gold Chunk IDs**: `P006_user_manual_002`

**Proposed Chunk Snippets (first 300 chars):**
  * **`P006_user_manual_002`** (user_manual - Maintenance & Cleaning Instructions): "3. Configure using the app and audio settings    - Download and install the Bowers & Wilkins Music App where available to access advanced settings, firmware updates, and sound customization. Use the app to confirm codec selection and to adjust any available sound tuning, noise-cancellation options, ..."

---

### [Q16] The tilt mechanism is stuck how do I unlock it?
- **Split**: `dev`
- **Question Type**: `procedural`
- **Product**: P008 (Steelcase Gesture)
- **Flags / Notes**: `None`
- **Model Reason**: *The troubleshooting chunk (P008_user_manual_003) explicitly advises to "Adjust the tilt tension (Core Equalizer or tilt control) to a neutral position" and states that "If the mechanism does not respond, stop use and seek support from your dealer," which directly addresses how to unlock/resolve a stuck tilt mechanism.*
- **Gold Keywords**: `None`
- **Gold Chunk IDs**: `P008_user_manual_003`

**Proposed Chunk Snippets (first 300 chars):**
  * **`P008_user_manual_003`** (user_manual - Basic Troubleshooting): "- Wipe reinforced polymer frame and hard surfaces with a soft, damp cloth. Dry immediately. Spot cleaning - For fabric spots, test a mild detergent on an inconspicuous area first. Use a damp cloth to blot — do not saturate the fabric. Rinse by blotting with clean water and allow to air dry. - Avoid ..."

---

### [Q17] What is the correct way to assemble the wheelbase?
- **Split**: `test`
- **Question Type**: `procedural`
- **Product**: P011 (IKEA Markus)
- **Flags / Notes**: `None`
- **Model Reason**: *The user_manual_002 chunk explicitly describes how to assemble the wheelbase: “Install castors and base: Insert each castor into the sockets of the steel star base until fully seated. Place the base on the floor and insert the gas lift (if provided) or mounting column into the base.” This directly answers the procedural question about assembling the wheelbase.*
- **Gold Keywords**: `None`
- **Gold Chunk IDs**: `P011_user_manual_002`

**Proposed Chunk Snippets (first 300 chars):**
  * **`P011_user_manual_002`** (user_manual - Maintenance & Cleaning Instructions): "Before you begin - Clear a flat, stable workspace large enough for assembly. - Keep the instruction leaflet and hardware within reach.  Assembly and initial configuration (numbered steps) 1. Unpack and align parts: Remove all protective packaging and lay out components. Confirm you have the chair co..."

---

### [Q18] Chair height adjust nahi ho rahi cylinder kaise theek karu?
- **Split**: `dev`
- **Question Type**: `procedural`
- **Product**: P012 (Haworth Fern)
- **Flags / Notes**: `hinglish`
- **Model Reason**: *The user question asks how to fix a chair cylinder (seat height/pneumatic lift). The manual provides direct, actionable guidance: P012_user_manual_002 describes inserting/sliding the gas lift into the base and chair mechanism (reinstalling the cylinder), and P012_user_manual_003 (Basic Troubleshooting) explicitly addresses 'Problem: Seat will not raise or lower'—it advises to confirm correct use of the pneumatic lift lever, ensure the gas lift is fully seated in the base and chair mechanism, check load limits, and contact an authorized Haworth dealer if the mechanism remains unresponsive. These chunks directly answer the procedural question.*
- **Gold Keywords**: `None`
- **Gold Chunk IDs**: `P012_user_manual_002, P012_user_manual_003`

**Proposed Chunk Snippets (first 300 chars):**
  * **`P012_user_manual_002`** (user_manual - Core Controls & Daily Operation): "2. Base, casters, and gas lift - Insert casters into the aluminum base by pressing each caster stem firmly into the base sockets until they click into place. - Insert the gas lift into the center of the aluminum base. Slide the gas lift cover over the cylinder if provided.  3. Attach seat, back, and..."
  * **`P012_user_manual_003`** (user_manual - Basic Troubleshooting): "Daily ergonomics tips - Adjust seat height so your feet rest flat on the floor and knees form approximately a right angle. - Keep armrests adjusted so shoulders are relaxed and forearms rest lightly. - Use tilt and forward tilt to vary posture throughout the day and reduce static loading.  ## 4. Mai..."

---

### [Q19] Can I wash these shoes in the washing machine?
- **Split**: `dev`
- **Question Type**: `procedural`
- **Product**: P014 (Nike Air Max 270)
- **Flags / Notes**: `None`
- **Model Reason**: *The product's maintenance & cleaning instructions explicitly state 'Do not machine wash or tumble dry.' in P014_user_manual_002, which directly answers the procedural question.*
- **Gold Keywords**: `None`
- **Gold Chunk IDs**: `P014_user_manual_002`

**Proposed Chunk Snippets (first 300 chars):**
  * **`P014_user_manual_002`** (user_manual - Maintenance & Cleaning Instructions): "Follow these steps before first use to ensure proper fit and comfort.  ## 3. Core Controls & Daily Operation  Putting On and Taking Off - Use the heel pull tab to assist with putting the shoe on. Loosen the asymmetrical lacing if additional space is needed. - The inner sleeve bootie provides a slip-..."

---

### [Q20] How should I clean the suede material without ruining it?
- **Split**: `test`
- **Question Type**: `procedural`
- **Product**: P016 (New Balance 990v6)
- **Flags / Notes**: `None`
- **Model Reason**: *The user_manual maintenance & cleaning instructions (P016_user_manual_002) explicitly states how to clean pigskin suede: use a suede brush or soft cloth, use a suede-specific cleaner for stubborn marks, avoid saturating suede with water, air dry at room temperature, do not use direct heat, and do not machine wash or tumble dry.*
- **Gold Keywords**: `None`
- **Gold Chunk IDs**: `P016_user_manual_002`

**Proposed Chunk Snippets (first 300 chars):**
  * **`P016_user_manual_002`** (user_manual - Maintenance & Cleaning Instructions): "Putting on and using your 990v6:  - Putting on:   - Loosen the laces sufficiently, slide your foot in, then tighten the laces to a comfortable level. Ensure the heel tab lies flat and the reflective heel tab faces outward. - Lace adjustment:   - For more forefoot room, use a wider lacing pattern or ..."

---

### [Q21] Flat feet ke liye laces baandhne ka koi specific technique hai?
- **Split**: `dev`
- **Question Type**: `out_of_docs` (RELABELED from `procedural`)
- **Product**: P018 (Hoka Clifton 9)
- **Flags / Notes**: `hinglish VERIFY RELABELED`
- **Model Reason**: *The provided catalog and document chunks give general lacing and fit guidance (e.g., loosen laces, tighten progressively from forefoot to ankle, re-lace to relieve pressure, tighten midfoot for heel slip) but do not explicitly mention any lacing technique or specific instructions for 'flat feet' (flatfoot/overpronation). The exact question—whether there is a specific lacing technique for flat feet—is not directly answered in the documents, so it is not answerable from the provided material.*
- **Gold Keywords**: `None`
- **Gold Chunk IDs**: `None`

---

### [Q22] How do I change the time format from 12-hour to 24-hour?
- **Split**: `test`
- **Question Type**: `out_of_docs` (RELABELED from `procedural`)
- **Product**: P020 (Apple Watch Ultra 2)
- **Flags / Notes**: `RELABELED`
- **Model Reason**: *The provided product catalog and all document chunks do not include any instructions or information about changing the time format (12-hour vs 24-hour). Settings and controls are mentioned (e.g., Action Button in Settings → Action Button), but no chunk states how to change the watch's time format, so the question cannot be answered from the given documents.*
- **Gold Keywords**: `None`
- **Gold Chunk IDs**: `None`

---

### [Q23] Smartwatch ka strap kaise detach karte hain?
- **Split**: `dev`
- **Question Type**: `procedural`
- **Product**: P022 (Seiko Prospex Speedtimer Solar Chronograph)
- **Flags / Notes**: `hinglish`
- **Model Reason**: *The user assumes this is a 'smartwatch' whose strap can be detached. The docs state the product is an analog Seiko Prospex Speedtimer Solar Chronograph and "does not include wireless or smart connectivity features" (P022_faq_001). This corrects the false premise; the corpus does not provide instructions for detaching a smartwatch strap, so the single FAQ chunk that clarifies the device type is the minimal supporting document.*
- **Gold Keywords**: `None`
- **Gold Chunk IDs**: `P022_faq_001`

**Proposed Chunk Snippets (first 300 chars):**
  * **`P022_faq_001`** (faq - Q: How do I use and read the chronograph and the power reserve indicator?): "## Q: Does this watch connect to smartphones or other devices?  A: No. The Seiko Prospex Speedtimer Solar Chronograph is an analog solar quartz chronograph driven by the Seiko Caliber V192. It does not include wireless or smart connectivity features, and it is not compatible with smartphone apps or ..."

---

### [Q24] My screen is stuck on the logo how do I restart the watch?
- **Split**: `test`
- **Question Type**: `out_of_docs` (RELABELED from `procedural`)
- **Product**: P023 (Samsung Galaxy Watch 6 Classic)
- **Flags / Notes**: `RELABELED`
- **Model Reason**: *The documents mention restarting the watch as a general troubleshooting step (see P023_faq_003, P023_user_manual_003, P023_faq_001), but none of the provided chunks give explicit, step-by-step instructions for restarting or force-restarting the watch when it is stuck on the logo. The exact method to restart the device is not stated in the corpus, so the question is not directly answerable from the provided content.*
- **Gold Keywords**: `None`
- **Gold Chunk IDs**: `None`

---

### [Q25] Will using these headphones for 10 hours a day cause hearing loss?
- **Split**: `dev`
- **Question Type**: `out_of_docs`
- **Product**: P001 (Sony WH-1000XM5)
- **Flags / Notes**: `None`
- **Model Reason**: *Not answerable: none of the provided product catalog entry or document chunks mention hearing loss, safe-listening limits, volume recommendations, or medical/health guidance. The documents only reference comfort and taking breaks for long sessions, but do not state whether using the headphones 10 hours a day causes hearing loss.*
- **Gold Keywords**: `None`
- **Gold Chunk IDs**: `None`

---

### [Q26] Can I use these headphones as a mic for recording ASMR videos?
- **Split**: `test`
- **Question Type**: `out_of_docs`
- **Product**: P004 (Sennheiser Momentum 4 Wireless)
- **Flags / Notes**: `None`
- **Model Reason**: *The documents list "crystal-clear call microphones" and "onboard microphones" (e.g., P004_user_manual_001, P004_faq_002, P004_usage_guide_001) and describe call use, but they do not explicitly state whether the headphones can be used as a microphone for recording videos or for ASMR specifically, nor do they state recording quality, stereo/ASMR capability, or guidance for using them as an external recording mic. Because the catalog/chunks do not directly answer the ASMR-recording capability, this question is out-of-docs and not answerable from the provided materials.*
- **Gold Keywords**: `None`
- **Gold Chunk IDs**: `None`

---

### [Q27] Is this ergonomic chair guaranteed to fix my lower back pain?
- **Split**: `dev`
- **Question Type**: `out_of_docs`
- **Product**: P009 (Secretlab Titan Evo)
- **Flags / Notes**: `None`
- **Model Reason**: *Not answerable: Nowhere in the product catalog entry or document chunks does Secretlab state the Titan Evo is guaranteed to fix lower back pain. The docs describe adjustable lumbar support (e.g., 4-way L-ADAPT Lumbar System) and give setup/usage guidance, and the warranty covers defects, but there is no explicit medical or therapeutic guarantee in the provided materials.*
- **Gold Keywords**: `None`
- **Gold Chunk IDs**: `None`

---

### [Q28] Meri height 6 foot 5 hai kya ye chair mere liye comfortable rahegi?
- **Split**: `dev`
- **Question Type**: `out_of_docs`
- **Product**: P007 (Herman Miller Aeron Chair)
- **Flags / Notes**: `hinglish`
- **Model Reason**: *The documents and product entry do not state any height ranges or explicitly say whether a 6'5" (195 cm) person will be comfortable. The catalog only notes the chair is available in sizes A, B, and C and recommends selecting the size that matches your body proportions and trying sizes with a dealer, but it gives no explicit guidance or height-to-size mapping to answer this question directly.*
- **Gold Keywords**: `None`
- **Gold Chunk IDs**: `None`

---

### [Q29] Will these running shoes help me reduce my 5K race time?
- **Split**: `test`
- **Question Type**: `out_of_docs`
- **Product**: P015 (Adidas Ultraboost Light)
- **Flags / Notes**: `None`
- **Model Reason**: *The catalog and document chunks describe features (Light BOOST midsole, Linear Energy Push, lightweight 299g, suitability for race preparation) that may support performance (see e.g. P015_user_manual_001, P015_usage_guide_001, P015_usage_guide_003), but none of the provided texts explicitly state that the shoes will reduce a user's 5K race time. The question requires a direct, stated claim or measurable outcome from the docs, which is not present, so it is not directly answerable from the supplied materials.*
- **Gold Keywords**: `None`
- **Gold Chunk IDs**: `None`

---

### [Q30] Can I wear these trail running shoes to a formal office party?
- **Split**: `dev`
- **Question Type**: `out_of_docs`
- **Product**: P019 (Salomon XT-6)
- **Flags / Notes**: `None`
- **Model Reason**: *The product catalog and document chunks describe intended uses (trail running, technical terrain, gorpcore/urban-outdoor activities) but do not state whether the Salomon XT-6 is appropriate for a formal office party. The question asks for a style/social suitability judgement that is not directly or explicitly addressed in the provided documents, so it cannot be answered from the corpus without making inferences.*
- **Gold Keywords**: `None`
- **Gold Chunk IDs**: `None`

---

### [Q31] Does the heart rate sensor accurately detect incoming heart attacks?
- **Split**: `test`
- **Question Type**: `out_of_docs`
- **Product**: P021 (Garmin Fenix 7 Pro Solar)
- **Flags / Notes**: `None`
- **Model Reason**: *Not answerable: neither the PRODUCTS.JSON entry nor any corpus chunk makes any claim that the watch or its Elevate v5 optical heart rate sensor can detect incoming heart attacks or medical emergencies. The documents only list sensors and provide wear/accuracy guidance, so this specific medical-detection capability is not stated and cannot be inferred.*
- **Gold Keywords**: `None`
- **Gold Chunk IDs**: `None`

---

### [Q32] Kya main is smartwatch par PUBG jaise heavy games khel sakta hu?
- **Split**: `dev`
- **Question Type**: `out_of_docs`
- **Product**: P023 (Samsung Galaxy Watch 6 Classic)
- **Flags / Notes**: `hinglish`
- **Model Reason**: *Not answerable from the provided docs: none of the catalog entry or chunks explicitly state whether heavy games (e.g., PUBG) can be played on the Galaxy Watch 6 Classic. The documents only note it runs 'Wear OS 4' and can run watch apps, but they do not mention gaming support, performance, or PUBG specifically, so the question is out-of-docs.*
- **Gold Keywords**: `None`
- **Gold Chunk IDs**: `None`

---

### [Q33] Can I connect my PlayStation 5 to this projector?
- **Split**: `dev`
- **Question Type**: `unknown_product`
- **Product**:  (N/A (Unknown Product))
- **Flags / Notes**: `None`
- **Model Reason**: *Unknown product question evaluated without catalog docs.*
- **Gold Keywords**: `None`
- **Gold Chunk IDs**: `None`

---

### [Q34] Is the Sony FX3 camera good for low light shooting?
- **Split**: `test`
- **Question Type**: `unknown_product`
- **Product**:  (N/A (Unknown Product))
- **Flags / Notes**: `CHECK-NAME`
- **Model Reason**: *Unknown product question evaluated without catalog docs.*
- **Gold Keywords**: `None`
- **Gold Chunk IDs**: `None`

---

### [Q35] Does the Sony WH-1000XM4 support multipoint Bluetooth?
- **Split**: `dev`
- **Question Type**: `unknown_product`
- **Product**:  (N/A (Unknown Product))
- **Flags / Notes**: `near-neighbor CHECK-NAME`
- **Model Reason**: *Unknown product question evaluated without catalog docs.*
- **Gold Keywords**: `None`
- **Gold Chunk IDs**: `None`

---

### [Q36] How long is the warranty on the Bose QuietComfort 45?
- **Split**: `dev`
- **Question Type**: `unknown_product`
- **Product**:  (N/A (Unknown Product))
- **Flags / Notes**: `near-neighbor CHECK-NAME`
- **Model Reason**: *Unknown product question evaluated without catalog docs.*
- **Gold Keywords**: `None`
- **Gold Chunk IDs**: `None`

---

### [Q37] Mere purane HP laptop ki battery kahan aur kitne ki milegi?
- **Split**: `test`
- **Question Type**: `unknown_product`
- **Product**:  (N/A (Unknown Product))
- **Flags / Notes**: `hinglish`
- **Model Reason**: *Unknown product question evaluated without catalog docs.*
- **Gold Keywords**: `None`
- **Gold Chunk IDs**: `None`

---

### [Q38] What is the exact thread count on these Egyptian cotton bedsheets?
- **Split**: `dev`
- **Question Type**: `unknown_product`
- **Product**:  (N/A (Unknown Product))
- **Flags / Notes**: `None`
- **Model Reason**: *Unknown product question evaluated without catalog docs.*
- **Gold Keywords**: `None`
- **Gold Chunk IDs**: `None`

---

### [Q39] Can I safely use this hair straightener on wet hair?
- **Split**: `test`
- **Question Type**: `unknown_product`
- **Product**:  (N/A (Unknown Product))
- **Flags / Notes**: `None`
- **Model Reason**: *Unknown product question evaluated without catalog docs.*
- **Gold Keywords**: `None`
- **Gold Chunk IDs**: `None`

---

### [Q40] How do I adjust the lumbar support on the Herman Miller Embody?
- **Split**: `dev`
- **Question Type**: `unknown_product`
- **Product**:  (N/A (Unknown Product))
- **Flags / Notes**: `near-neighbor CHECK-NAME`
- **Model Reason**: *Unknown product question evaluated without catalog docs.*
- **Gold Keywords**: `None`
- **Gold Chunk IDs**: `None`

---

## 3. LLM-Drafted Questions (Q41–Q55)

> **Notice**: These 15 questions were LLM-drafted with casual customer phrasing, verified for 0 4-gram overlap with product chunks, and verified as directly answerable via strict labeling logic against local product documents.

### [Q41] Ek baar full charge karne par yeh kitne ghante tak chal sakte hain?
- **Split**: `dev`
- **Question Type**: `spec`
- **Product**: P005 (Audio-Technica ATH-M50xBT2)
- **Notes**: `LLM-DRAFTED hinglish`
- **Model Annotation Reason**: *The product specification explicitly lists battery_life as "50 hours" in the catalog. The user manual chunk P005_user_manual_001 also states "Battery life: 50 hours", so the question is directly answerable from the provided documents.*
- **Gold Keywords**: `50 hours`
- **Gold Chunk IDs**: `P005_user_manual_001`

**Proposed Chunk Snippets (first 300 chars):**
  * **`P005_user_manual_001`** (user_manual - Setup & Initial Configuration): "## 1. Product Overview & In the Box  Overview - The Audio-Technica ATH-M50xBT2 delivers the legendary studio monitor sonic signature in a wireless Bluetooth design with exceptional clarity across an extended frequency range. - Type: Over-Ear Closed-back - Connectivity: Bluetooth 5.0, LDAC, AAC, SBC ..."

---

### [Q42] How many hours will these play on a single charge?
- **Split**: `test`
- **Question Type**: `spec`
- **Product**: P006 (Bowers & Wilkins Px7 S2e)
- **Notes**: `LLM-DRAFTED`
- **Model Annotation Reason**: *The product specifications explicitly state the battery life as 'Battery life: 30 hours' in the user manual/specifications (chunk P006_user_manual_001). This directly answers the question.*
- **Gold Keywords**: `30 hours`
- **Gold Chunk IDs**: `P006_user_manual_001`

**Proposed Chunk Snippets (first 300 chars):**
  * **`P006_user_manual_001`** (user_manual - Setup & Initial Configuration): "## 1. Product Overview & In the Box  Product overview: - Model: Bowers & Wilkins Px7 S2e - Category: Headphones (Over-Ear) - Description: Refined wireless noise-canceling headphones tuned by Abbey Road studio engineers with 24-bit DSP audio processing. - Key specifications:   - Type: Over-Ear   - Co..."

---

### [Q43] Ye chair kitna wajan support kar sakta hai?
- **Split**: `dev`
- **Question Type**: `spec`
- **Product**: P013 (Humanscale Freedom)
- **Notes**: `LLM-DRAFTED hinglish`
- **Model Annotation Reason**: *The product specification in the catalog and user_manual chunk P013_user_manual_001 explicitly states the maximum load: "136 kg (300 lbs)", which directly answers the question.*
- **Gold Keywords**: `136 kg (300 lbs)`
- **Gold Chunk IDs**: `P013_user_manual_001`

**Proposed Chunk Snippets (first 300 chars):**
  * **`P013_user_manual_001`** (user_manual - Setup & Initial Configuration): "## 1. Product Overview & In the Box  Product: Humanscale Freedom   Brand: Humanscale   Category: Chairs   Designer note: Niels Diffrient-designed self-adjusting recline chair utilizing body weight and physics to eliminate manual knobs and tension dials.  Key specifications (from product data) - Mate..."

---

### [Q44] How much weight can this chair support?
- **Split**: `test`
- **Question Type**: `spec`
- **Product**: P008 (Steelcase Gesture)
- **Notes**: `LLM-DRAFTED`
- **Model Annotation Reason**: *The product specifications explicitly list the maximum load as "181 kg (400 lbs)". This exact value appears in the catalog entry and is stated in chunk P008_faq_001 under fit and weight limits.*
- **Gold Keywords**: `181 kg (400 lbs)`
- **Gold Chunk IDs**: `P008_faq_001`

**Proposed Chunk Snippets (first 300 chars):**
  * **`P008_faq_001`** (faq - Q: How do I adjust the chair for daily use and different postures?): "## Q: Does the Steelcase Gesture have any connectivity or electronics I should be aware of?  A: No — the Steelcase Gesture is a mechanical office chair and does not include electronic components, wireless radios, or batteries. Its design is inspired by interactions with modern touchscreen devices an..."

---

### [Q45] About how heavy are these sneakers in a men's size 9?
- **Split**: `dev`
- **Question Type**: `spec`
- **Product**: P014 (Nike Air Max 270)
- **Notes**: `LLM-DRAFTED`
- **Model Annotation Reason**: *The product specification explicitly lists the weight as "310g (Size 9)" in the catalog and the user manual chunk P014_user_manual_001 also states "Weight: 310g (Size 9)".*
- **Gold Keywords**: `310g (Size 9)`
- **Gold Chunk IDs**: `P014_user_manual_001`

**Proposed Chunk Snippets (first 300 chars):**
  * **`P014_user_manual_001`** (user_manual - Setup & Initial Configuration): "## 1. Product Overview & In the Box  Product Overview - The Nike Air Max 270 is a lifestyle sneaker that features Nike's largest heel Air unit designed for soft heel cushioning and an energetic, lightweight stride. - Upper: Engineered knit mesh and synthetic overlays for breathability and structure...."

---

### [Q46] How heavy is a size 9 pair of these?
- **Split**: `test`
- **Question Type**: `spec`
- **Product**: P016 (New Balance 990v6)
- **Notes**: `LLM-DRAFTED`
- **Model Annotation Reason**: *The product specs explicitly list the weight as "374g (Size 9)" in the catalog and P016_user_manual_001 contains the identical line: 'Weight: 374g (Size 9).' This directly answers the question.*
- **Gold Keywords**: `374g (Size 9)`
- **Gold Chunk IDs**: `P016_user_manual_001`

**Proposed Chunk Snippets (first 300 chars):**
  * **`P016_user_manual_001`** (user_manual - Core Controls & Daily Operation): "## 1. Product Overview & In the Box  Product: New Balance 990v6   Brand: New Balance   Category: Shoes  Overview: - The New Balance 990v6 is a Made in USA heritage lifestyle and running shoe featuring FuelCell foam cushioning and premium pigskin suede overlays. - Upper material: Pigskin suede and br..."

---

### [Q47] Is watch ko full wind karne ke baad kitne ghante tak chal sakta hai?
- **Split**: `dev`
- **Question Type**: `spec`
- **Product**: P024 (Tissot PRX Powermatic 80)
- **Notes**: `LLM-DRAFTED hinglish`
- **Model Annotation Reason**: *The product specs explicitly state an 80-hour power reserve. Chunk P024_user_manual_001 lists 'Power reserve: 80 hours' (matches the catalog entry).*
- **Gold Keywords**: `80 hours|80-hour power reserve`
- **Gold Chunk IDs**: `P024_user_manual_001`

**Proposed Chunk Snippets (first 300 chars):**
  * **`P024_user_manual_001`** (user_manual - Setup & Initial Configuration): "## 1. Product Overview & In the Box  Product overview: - Model: Tissot PRX Powermatic 80 - Case: 40mm 316L stainless steel - Movement: Powermatic 80.111 automatic movement with Nivachron balance spring - Power reserve: 80 hours - Crystal (front): Scratch-resistant sapphire crystal with anti-reflecti..."

---

### [Q48] About how long will the batteries keep this running before needing a replacement?
- **Split**: `test`
- **Question Type**: `spec`
- **Product**: P025 (Casio G-Shock GA-2100 'CasiOak')
- **Notes**: `LLM-DRAFTED`
- **Model Annotation Reason**: *The product specifications and user manual explicitly state the battery life as "3 years on SR726W x 2" (see P025_user_manual_001), which directly answers the question.*
- **Gold Keywords**: `3 years on SR726W x 2|SR726W x 2`
- **Gold Chunk IDs**: `P025_user_manual_001`

**Proposed Chunk Snippets (first 300 chars):**
  * **`P025_user_manual_001`** (user_manual - Setup & Initial Configuration): "## 1. Product Overview & In the Box  Product overview - Model: Casio G-Shock GA-2100 'CasiOak' - Ultra-tough analog-digital timepiece with Carbon Core Guard shock resistant case. - Case size: 45.4mm (Carbon and Resin). - Movement: Quartz module 5611 (Accuracy: ±15 seconds per month). - Battery life:..."

---

### [Q49] AirPods Max mere phone se connect nahi ho rahe — pehle kaunse simple steps try karun?
- **Split**: `dev`
- **Question Type**: `procedural`
- **Product**: P003 (Apple AirPods Max)
- **Notes**: `LLM-DRAFTED hinglish`
- **Model Annotation Reason**: *Chunk P003_faq_002 explicitly lists simple troubleshooting steps for pairing failures: ensure sufficient battery, restart Bluetooth on the source device and retry pairing, try storing/removing the headphones from the Smart Case to trigger reconnect, and further actions if needed. These steps directly answer the user's request for initial steps to try.*
- **Gold Chunk IDs**: `P003_faq_002`

**Proposed Chunk Snippets (first 300 chars):**
  * **`P003_faq_002`** (faq - Q: What should I do if I experience common issues like pairing failures or uneven audio?): "The listed product weight is 384.8g. Comfort will depend on individual head shape and preferred clamp force; taking short breaks during long sessions can help reduce fatigue. If you experience pressure points or discomfort, adjust the positioning on your head and ensure the ear cushions are seated c..."

---

### [Q50] My phone won’t show the headphones after I power them on — how do I make the headphones discoverable so I can pair them via Bluetooth?
- **Split**: `test`
- **Question Type**: `procedural`
- **Product**: P004 (Sennheiser Momentum 4 Wireless)
- **Notes**: `LLM-DRAFTED`
- **Model Annotation Reason**: *The user manual (P004_user_manual_001) explicitly states how to enter pairing: 'Power on the headphones. If they do not automatically enter pairing mode, use the dedicated Bluetooth control to enter pairing until the indicator shows the headphones are discoverable.' It also gives pairing steps for the source device, so this chunk directly answers how to make the headphones discoverable and pair them.*
- **Gold Chunk IDs**: `P004_user_manual_001`

**Proposed Chunk Snippets (first 300 chars):**
  * **`P004_user_manual_001`** (user_manual - Setup & Initial Configuration): "## 1. Product Overview & In the Box  Product overview - Model: Sennheiser Momentum 4 Wireless - Type: Over-Ear - Driver size: 42mm transducer system designed for superior dynamics and clarity - Connectivity: Bluetooth 5.2 with aptX Adaptive support - Noise cancellation: Adaptive Hybrid ANC - Battery..."

---

### [Q51] When I try to lean back the chair it feels stiff and won't recline — what quick checks can I do to try to get the recline working before I contact support?
- **Split**: `dev`
- **Question Type**: `procedural`
- **Product**: P013 (Humanscale Freedom)
- **Notes**: `LLM-DRAFTED`
- **Model Annotation Reason**: *The product documentation's Basic Troubleshooting (chunk P013_user_manual_003) explicitly lists quick checks for a stiff/non‑reclining chair: sit fully in the seat to engage the weight‑sensitive mechanism; check floor surface and caster condition; tighten visible fasteners; verify the chair is not overloaded (136 kg/300 lbs); confirm no obstructions at pivot points and remove debris; gently move the backrest to observe binding — and contact your dealer if binding persists. These steps directly answer the user's procedural question.*
- **Gold Chunk IDs**: `P013_user_manual_003`

**Proposed Chunk Snippets (first 300 chars):**
  * **`P013_user_manual_003`** (user_manual - Basic Troubleshooting): "- Getting in and out: Use the armrests or seat edge for support. Avoid sudden or off-centered loading that could stress components. - Load safety: Do not exceed 136 kg (300 lbs). The chair is designed and tested to support up to the listed maximum load.  ## 4. Maintenance & Cleaning Instructions  - ..."

---

### [Q52] Mesh back aur molded foam seat ko ghar par safely kaise clean karun? Kya mesh ko zyada paani se bhigona safe hai aur foam par daag padne par kya karna chahiye?
- **Split**: `test`
- **Question Type**: `procedural`
- **Product**: P010 (Autonomous ErgoChair Pro)
- **Notes**: `LLM-DRAFTED hinglish`
- **Model Annotation Reason**: *Chunk P010_faq_001 explicitly gives home-cleaning instructions: it says to "Spot-clean with a damp cloth and mild detergent; avoid saturating the mesh." and for the seat: "Wipe spills promptly with a damp cloth and mild soap. Avoid harsh solvents and do not soak the foam. For stubborn stains follow manufacturer-approved upholstery cleaners." These lines directly answer the questions about soaking mesh and treating foam stains.*
- **Gold Chunk IDs**: `P010_faq_001`

**Proposed Chunk Snippets (first 300 chars):**
  * **`P010_faq_001`** (faq - Q: How do I clean and maintain the materials used in this chair?): "## Q: Does the Autonomous ErgoChair Pro have wireless connectivity or need batteries to operate?  A: The published product specifications do not list any battery, power, or wireless connectivity features. The specification set provided focuses on mechanical and material attributes (for example, "Bre..."

---

### [Q53] Can I wash my XT-6s in a washing machine or put them in a tumble dryer to dry them faster?
- **Split**: `test`
- **Question Type**: `procedural`
- **Product**: P019 (Salomon XT-6)
- **Notes**: `LLM-DRAFTED`
- **Model Annotation Reason**: *The user manual chunk P019_user_manual_003 explicitly states: “Avoid machine washing and drying to preserve welded TPU film and integrated features.” and “Air dry at room temperature away from direct heat or sunlight. Do not tumble dry or place near heaters.” These lines directly answer both parts of the question.*
- **Gold Chunk IDs**: `P019_user_manual_003`

**Proposed Chunk Snippets (first 300 chars):**
  * **`P019_user_manual_003`** (user_manual - Basic Troubleshooting): "Cleaning - Remove loose dirt by gently tapping soles together or using a soft brush. - Hand wash with lukewarm water and a mild soap. Use a soft brush or cloth to clean upper, midsole, and outsole. - Rinse thoroughly to remove soap residue.  Drying and care - Air dry at room temperature away from di..."

---

### [Q54] My PRX has stopped — can I restart it myself by winding the crown, and how far should I wind it so I don’t damage the movement?
- **Split**: `dev`
- **Question Type**: `procedural`
- **Product**: P024 (Tissot PRX Powermatic 80)
- **Notes**: `LLM-DRAFTED`
- **Model Annotation Reason**: *The usage guidance (P024_usage_guide_002) explicitly says you can restart a stopped PRX by 'gently winding the crown or by wearing it' and instructs to 'Wind carefully until slight resistance is felt—do not force,' which directly answers both parts of the question.*
- **Gold Chunk IDs**: `P024_usage_guide_002`

**Proposed Chunk Snippets (first 300 chars):**
  * **`P024_usage_guide_002`** (usage_guide - Do's and Don'ts for Daily Use): "- Water exposure: The watch is water resistant to 10 bar (100 meters). It is suitable for everyday use including washing hands and swimming. After exposure to salt water or chlorinated water, rinse the bracelet and case with fresh water and dry thoroughly.  ## 3. Best Practices for Product Longevity..."

---

### [Q55] If I wear the watch while swimming in the ocean or a pool, should I rinse it afterward and what's the proper way to dry it?
- **Split**: `test`
- **Question Type**: `procedural`
- **Product**: P020 (Apple Watch Ultra 2)
- **Notes**: `LLM-DRAFTED`
- **Model Annotation Reason**: *Chunk P020_user_manual_002 explicitly states: 'Rinse the watch with fresh water after exposure to saltwater, chlorine, or sweat. Use a soft, lint‑free cloth to dry.' This directly answers both parts (rinse after ocean/pool use and how to dry).*
- **Gold Chunk IDs**: `P020_user_manual_002`

**Proposed Chunk Snippets (first 300 chars):**
  * **`P020_user_manual_002`** (user_manual - Maintenance & Cleaning Instructions): "## 2. Setup & Initial Configuration  ## 3. Core Controls & Daily Operation  - Display and viewing   - The Always‑On Retina OLED display provides a bright view with up to 3000 nits peak brightness for outdoor visibility. - Action button   - The Customizable Action button can be assigned to a specific..."

---


