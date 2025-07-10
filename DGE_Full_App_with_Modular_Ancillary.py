# DGE Full App with Modular Ancillary Services & SCF
Complete DGE Module/
├── DGE_Full_App_with_Modular_Ancillary.py   ✅ <– This is your main file
├── dge_goods_data.json                      ✅ <– For storing data
├── uploads/                                 ✅ <– For uploaded item files
├── requirements.txt                         ✅ <– For dependencies


import streamlit as st
import json


# ---------- Setup ----------
os.makedirs("uploads", exist_ok=True)
DATA_FILE = "dge_goods_data.json"
CATEGORY_VALUATION = {
    "Electronics": 50,
    "Automobile": 55,
    "Textiles": 40,
    "Furniture": 60,
    "Machinery": 45,
    "Plastic Goods": 35,
    "Chemicals": 30,
    "Food & Beverage": 25,
    "Metals": 50,
    "Paper": 30,
    "Pharmaceuticals": 40,
    "Toys": 35,
    "Glassware": 45,
    "Footwear": 38,
    "Leather Products": 42
}

# ---------- Helpers ----------
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return []

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

# ---------- UI Starts ----------
st.title("📦 Damaged & Rejected Goods Full Intake System")

# ---------- Basic Inputs ----------
st.subheader("📝 Goods Intake")
item_name = st.text_input("Item Name")
hs_code = st.text_input("HS Code")
quantity = st.number_input("Quantity", min_value=1)
port = st.text_input("Port of Rejection")
reason = st.text_area("Reason for Rejection")
image = st.file_uploader("Upload Item Image (optional)", type=["jpg", "png", "jpeg"])

# ---------- Valuation Section ----------
st.subheader("💰 Valuation")
category = st.selectbox("Select Category", list(CATEGORY_VALUATION.keys()))
original_price = st.number_input("Original Price (USD)", min_value=0.0, step=1.0)
override_percent = st.number_input("Override Valuation % (optional)", min_value=0.0, max_value=100.0, value=float(CATEGORY_VALUATION[category]), step=1.0)
valuation_percent = override_percent if override_percent != CATEGORY_VALUATION[category] else CATEGORY_VALUATION[category]
valued_price = (valuation_percent / 100.0) * original_price
st.markdown(f"**📉 Valued Price**: ${valued_price:,.2f} based on {valuation_percent}% valuation")

# ---------- Service Module Selector ----------
st.subheader("🔧 Select Required Services")
services_selected = st.multiselect("Choose Ancillary Services", [
    "Inspection",
    "Certification Verification",
    "Buyer Swap Discovery",
    "Warehousing",
    "Packaging",
    "Trucking",
    "SCF (Supply Chain Finance)"
])

# ---------- Service Forms ----------
services_data = {}

if "Inspection" in services_selected:
    st.subheader("🔍 Inspection Details")
    services_data["inspection"] = {
        "inspector_id": st.text_input("Inspector ID"),
        "inspection_notes": st.text_area("Inspection Notes")
    }

if "Certification Verification" in services_selected:
    st.subheader("📄 Certification Verification")
    services_data["certification"] = {
        "cert_type": st.text_input("Type of Certification (e.g., ISO, BIS)"),
        "cert_verified": st.checkbox("Verified?", value=True)
    }

if "Buyer Swap Discovery" in services_selected:
    st.subheader("🔄 Buyer Swap Details")
    services_data["buyer_swap"] = {
        "alternative_buyer": st.text_input("Alternative Buyer Name"),
        "contact": st.text_input("Contact Info")
    }

if "Warehousing" in services_selected:
    st.subheader("🏬 Warehousing")
    services_data["warehousing"] = {
        "warehouse_location": st.text_input("Warehouse Location"),
        "duration_days": st.number_input("Storage Duration (days)", min_value=0)
    }

if "Packaging" in services_selected:
    st.subheader("📦 Packaging")
    services_data["packaging"] = {
        "package_type": st.selectbox("Type of Packaging", ["Box", "Pallet", "Bubble Wrap", "Crate"]),
        "special_handling": st.checkbox("Special Handling Required?")
    }

if "Trucking" in services_selected:
    st.subheader("🚛 Transportation")
    services_data["trucking"] = {
        "pickup_location": st.text_input("Pickup Location"),
        "drop_location": st.text_input("Drop Location"),
        "transporter_name": st.text_input("Transporter")
    }

if "SCF (Supply Chain Finance)" in services_selected:
    st.subheader("💸 Supply Chain Finance (SCF)")
    wants_scf = st.radio("Do you want SCF?", ["Yes", "No"], index=0)
    if wants_scf == "Yes":
        max_scf_allowed = valued_price * 0.6
        scf_requested = st.number_input("SCF Amount Requested (Max 60% of Valued Price)", min_value=0.0, max_value=max_scf_allowed, value=0.0, step=10.0)
        scf_interest = st.number_input("SCF Interest Rate (%)", min_value=0.0, max_value=100.0, value=12.0)
        scf_days = st.number_input("SCF Duration (in days)", min_value=1, value=30)
        scf_total_interest = (scf_requested * scf_interest * scf_days) / (100 * 365)
        st.markdown(f"📈 **Interest Payable**: ${scf_total_interest:,.2f}")
        services_data["scf"] = {
            "scf_requested": scf_requested,
            "scf_interest_rate": scf_interest,
            "scf_days": scf_days,
            "scf_total_interest": scf_total_interest
        }

# ---------- Submit ----------
if st.button("Submit Item"):
    entry = {
        "item_name": item_name,
        "hs_code": hs_code,
        "quantity": quantity,
        "port": port,
        "reason": reason,
        "category": category,
        "original_price": original_price,
        "valuation_percent": valuation_percent,
        "valued_price": valued_price,
        "services": services_data
    }
    if image:
        entry["image_name"] = image.name
        with open(os.path.join("uploads", image.name), "wb") as f:
            f.write(image.read())
    data = load_data()
    data.append(entry)
    save_data(data)
    st.success("✅ Item successfully submitted!")

# ---------- Display Section ----------
st.subheader("📂 Submitted Items")
search_term = st.text_input("Search Items by Name or Port")
data = load_data()
filtered_data = [d for d in data if search_term.lower() in d["item_name"].lower() or search_term.lower() in d["port"].lower()]

for idx, item in enumerate(filtered_data):
    with st.expander(f"{item['item_name']} | Port: {item['port']}"):
        st.markdown(f"**HS Code**: {item['hs_code']}")
        st.markdown(f"**Quantity**: {item['quantity']}")
        st.markdown(f"**Category**: {item['category']}")
        st.markdown(f"**Original Price**: ${item['original_price']}")
        st.markdown(f"**Valuation %**: {item['valuation_percent']}%")
        st.markdown(f"**Valued Price**: ${item['valued_price']}")
        st.markdown(f"**Reason**: {item['reason']}")
        for module, info in item.get("services", {}).items():
            st.markdown(f"**{module.upper()}**: {info}")
        if item.get("image_name"):
            st.image(os.path.join("uploads", item["image_name"]), width=200)
        if st.button("🗑️ Delete", key=f"delete_{idx}"):
            data.remove(item)
            save_data(data)
            st.success("Item deleted.")
            st.experimental_rerun()
