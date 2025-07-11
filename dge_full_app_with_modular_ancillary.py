import streamlit as st
import json
import os
import pandas as pd
from datetime import datetime, timedelta

DATA_FILE = "dge_goods_data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                data = json.load(f)
                # Filter out any invalid records
                valid_data = []
                for record in data:
                    if isinstance(record, dict) and 'Item Name' in record and 'Port' in record:
                        valid_data.append(record)
                return valid_data
        except (json.JSONDecodeError, Exception) as e:
            st.error(f"Error loading data: {e}")
            return []
    return []

def save_data(data):
    try:
        with open(DATA_FILE, "w") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        st.error(f"Error saving data: {e}")

def generate_unique_id():
    """Generate a unique ID for each record"""
    return f"DGE-{datetime.now().strftime('%Y%m%d%H%M%S')}"

def calculate_scf_metrics(data):
    """Calculate SCF investment metrics"""
    scf_items = [d for d in data if d.get("Needs SCF") and d.get("SCF Details", {}).get("Requested", 0) > 0]
    
    if not scf_items:
        return None
    
    total_requested = sum(d.get("SCF Details", {}).get("Requested", 0) for d in scf_items)
    avg_interest_rate = sum(d.get("SCF Details", {}).get("Interest Rate (%)", 0) for d in scf_items) / len(scf_items)
    avg_duration = sum(d.get("SCF Details", {}).get("Duration (days)", 0) for d in scf_items) / len(scf_items)
    
    return {
        "total_opportunities": len(scf_items),
        "total_requested": total_requested,
        "avg_interest_rate": avg_interest_rate,
        "avg_duration": avg_duration
    }

# Enhanced category valuations with more categories
CATEGORY_VALUATION = {
    "Electronics": 50, "Automobile": 55, "Textiles": 40, "Furniture": 60, "Machinery": 45,
    "Plastic Goods": 35, "Chemicals": 30, "Food & Beverage": 25, "Metals": 50, "Paper": 30,
    "Pharmaceuticals": 70, "Cosmetics": 45, "Toys": 35, "Books": 25, "Jewelry": 80,
    "Sports Equipment": 40, "Home Appliances": 55, "Construction Materials": 35
}

ANCILLARY_OPTIONS = [
    "Inspection", "Certification Verification", "Buyer Swap Discovery",
    "Warehousing", "Packaging", "Trucking", "Insurance", "Legal Documentation"
]

# Port options for better data consistency
PORT_OPTIONS = [
    "Mumbai", "Chennai", "Kolkata", "Kandla", "Cochin", "Visakhapatnam", 
    "Paradip", "Tuticorin", "Mangalore", "Jawaharlal Nehru Port", "Other"
]

st.set_page_config(page_title="DGE SCM Intake System", layout="wide", initial_sidebar_state="expanded")

# Enhanced sidebar with metrics
st.sidebar.title("🏢 DGE SCM Navigation")
data = load_data()
metrics = calculate_scf_metrics(data)

if metrics:
    st.sidebar.metric("Total SCF Opportunities", metrics["total_opportunities"])
    st.sidebar.metric("Total SCF Requested", f"${metrics['total_requested']:,.0f}")
    st.sidebar.metric("Avg Interest Rate", f"{metrics['avg_interest_rate']:.1f}%")

section = st.sidebar.radio(
    "Go to Section", 
    ("Goods Intake & Ancillary Services", "SCF Investment Opportunities", "Admin Dashboard"),
    label_visibility="collapsed"
)

# === GOODS INTAKE & ANCILLARY SERVICES ===
if section == "Goods Intake & Ancillary Services":
    st.title("📦 Damaged & Rejected Goods Intake System")
    
    # Add summary statistics at the top
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Items Registered", len(data))
    with col2:
        total_value = sum(d.get('Valued Price', 0) for d in data)
        st.metric("Total Valued Amount", f"${total_value:,.0f}")
    with col3:
        scf_count = len([d for d in data if d.get("Needs SCF")])
        st.metric("SCF Requests", scf_count)
    with col4:
        unique_ports = len(set(d.get('Port', '') for d in data if d.get('Port')))
        st.metric("Unique Ports", unique_ports)
    
    st.header("📋 Goods Intake Form")
    
    with st.form("goods_intake_form", clear_on_submit=False):
        # Basic Information
        st.subheader("1️⃣ Basic Information")
        col1, col2 = st.columns(2)
        
        with col1:
            item_name = st.text_input("Item Name *", help="Enter the name of the damaged/rejected item")
            hs_code = st.text_input("HS Code", help="Harmonized System code for the item")
            quantity = st.number_input("Quantity *", min_value=1, value=1)
            port = st.selectbox("Port of Rejection *", PORT_OPTIONS)
            if port == "Other":
                port = st.text_input("Specify Other Port")
            
        with col2:
            reason = st.text_area("Reason for Rejection", help="Detailed reason for rejection")
            category = st.selectbox("Category *", list(CATEGORY_VALUATION.keys()))
            rejection_date = st.date_input("Rejection Date", datetime.now())
            urgency = st.selectbox("Urgency Level", ["Low", "Medium", "High", "Critical"])
        
        # Valuation Section
        st.subheader("💰 Valuation")
        col1, col2 = st.columns(2)
        
        with col1:
            original_price = st.number_input("Original Price (USD) *", min_value=1.0, value=1000.0, step=1.0)
            valuation_percent = st.number_input(
                "Valuation % (auto from category)", min_value=1.0, max_value=100.0,
                value=float(CATEGORY_VALUATION[category]), step=1.0,
                help="Override auto valuation if needed"
            )
            
        with col2:
            valued_price = original_price * valuation_percent / 100
            st.metric("Valued Price", f"${valued_price:,.2f}")
            uploaded_file = st.file_uploader("Upload goods photo or doc", type=["jpg", "jpeg", "png", "pdf"])

        # Ancillary Services Section
        st.subheader("2️⃣ Ancillary Services Required")
        ancillary_selected = st.multiselect("Choose services", ANCILLARY_OPTIONS)
        ancillary_details = {}
        
        if ancillary_selected:
            for service in ancillary_selected:
                with st.expander(f"📋 {service} Details"):
                    if service == "Inspection":
                        ancillary_details["Inspection"] = {
                            "Inspector ID": st.text_input("Inspector ID", key="insp_id"),
                            "Inspection Type": st.selectbox("Inspection Type", ["Visual", "Technical", "Quality", "Compliance"], key="insp_type"),
                            "Inspection Notes": st.text_area("Inspection Notes", key="insp_notes"),
                            "Estimated Cost": st.number_input("Estimated Cost (USD)", min_value=0.0, value=100.0, key="insp_cost")
                        }
                    elif service == "Certification Verification":
                        ancillary_details["Certification Verification"] = {
                            "Certification Type": st.text_input("Certification Type (ISO, BIS, etc.)", key="cert_type"),
                            "Certification Authority": st.text_input("Certification Authority", key="cert_auth"),
                            "Verified": st.selectbox("Verification Status", ["Pending", "Verified", "Failed"], key="cert_status")
                        }
                    elif service == "Buyer Swap Discovery":
                        ancillary_details["Buyer Swap Discovery"] = {
                            "Alternative Buyer": st.text_input("Alternative Buyer Name", key="buyer_name"),
                            "Contact Info": st.text_input("Contact Info", key="buyer_contact"),
                            "Negotiated Price": st.number_input("Negotiated Price (USD)", min_value=0.0, key="buyer_price")
                        }
                    elif service == "Warehousing":
                        ancillary_details["Warehousing"] = {
                            "Warehouse Location": st.text_input("Warehouse Location", key="warehouse_loc"),
                            "Storage Duration (days)": st.number_input("Storage Duration (days)", min_value=1, value=10, key="warehouse_days"),
                            "Storage Cost per Day": st.number_input("Storage Cost per Day (USD)", min_value=0.0, value=10.0, key="warehouse_cost")
                        }
                    elif service == "Packaging":
                        ancillary_details["Packaging"] = {
                            "Package Type": st.selectbox("Type of Packaging", ["Box", "Crate", "Pallet", "Custom"], key="pack_type"),
                            "Special Handling": st.checkbox("Special Handling Required?", key="pack_special"),
                            "Packaging Cost": st.number_input("Packaging Cost (USD)", min_value=0.0, value=50.0, key="pack_cost")
                        }
                    elif service == "Trucking":
                        ancillary_details["Trucking"] = {
                            "Pickup Location": st.text_input("Pickup Location", key="truck_pickup"),
                            "Drop Location": st.text_input("Drop Location", key="truck_drop"),
                            "Transporter": st.text_input("Transporter Name", key="truck_name"),
                            "Transport Cost": st.number_input("Transport Cost (USD)", min_value=0.0, value=200.0, key="truck_cost")
                        }
                    elif service == "Insurance":
                        ancillary_details["Insurance"] = {
                            "Insurance Type": st.selectbox("Insurance Type", ["Transit", "Storage", "Comprehensive"], key="ins_type"),
                            "Coverage Amount": st.number_input("Coverage Amount (USD)", min_value=0.0, value=valued_price, key="ins_coverage"),
                            "Premium": st.number_input("Premium (USD)", min_value=0.0, value=valued_price*0.02, key="ins_premium")
                        }
                    elif service == "Legal Documentation":
                        ancillary_details["Legal Documentation"] = {
                            "Document Type": st.multiselect("Document Type", ["Bill of Lading", "Commercial Invoice", "Packing List", "Certificate of Origin"], key="legal_docs"),
                            "Legal Compliance": st.selectbox("Legal Compliance Status", ["Compliant", "Non-Compliant", "Under Review"], key="legal_compliance")
                        }

        # SCF Section
        st.subheader("3️⃣ Supply Chain Finance (SCF) Request")
        needs_scf = st.checkbox("Request Supply Chain Finance?")
        scf_dict = {}
        
        if needs_scf:
            scf_max = valued_price * 0.6
            st.info(f"💡 Max SCF allowed: **${scf_max:,.2f}** (60% of valuation)")
            
            col1, col2 = st.columns(2)
            with col1:
                scf_requested = st.number_input("SCF Amount Requested (USD)", min_value=0.0, max_value=float(scf_max), value=0.0, step=1.0)
                scf_interest_rate = st.number_input("Proposed Interest Rate (%)", min_value=0.01, max_value=50.0, value=12.0, step=0.01)
                scf_days = st.number_input("Repayment Duration (days)", min_value=1, max_value=180, value=30, step=1)
                
            with col2:
                scf_interest = scf_requested * (scf_interest_rate/100) * (scf_days/365)
                st.metric("Estimated Interest", f"${scf_interest:,.2f}")
                st.metric("Total Repayment", f"${scf_requested + scf_interest:,.2f}")
                
                # Risk assessment
                risk_score = "Low" if scf_interest_rate < 15 else "Medium" if scf_interest_rate < 25 else "High"
                st.metric("Risk Assessment", risk_score)
                
            scf_dict = {
                "Requested": scf_requested,
                "Interest Rate (%)": scf_interest_rate,
                "Duration (days)": scf_days,
                "Total Interest": scf_interest,
                "Total Repayment": scf_requested + scf_interest,
                "Risk Score": risk_score
            }

        # Submit button
        submitted = st.form_submit_button("🚀 Submit Intake", use_container_width=True)
        
        if submitted:
            # Enhanced validation
            errors = []
            if not item_name:
                errors.append("Item Name is required")
            if not port:
                errors.append("Port of Rejection is required")
            if quantity <= 0:
                errors.append("Quantity must be greater than 0")
            if original_price <= 0:
                errors.append("Original Price must be greater than 0")
                
            if errors:
                st.error("Please fix the following errors:\n" + "\n".join(f"• {error}" for error in errors))
            else:
                # Create record with enhanced fields
                record = {
                    "ID": generate_unique_id(),
                    "Item Name": item_name,
                    "HS Code": hs_code,
                    "Quantity": quantity,
                    "Port": port,
                    "Reason": reason,
                    "Category": category,
                    "Rejection Date": rejection_date.isoformat(),
                    "Urgency": urgency,
                    "Original Price": original_price,
                    "Valuation %": valuation_percent,
                    "Valued Price": valued_price,
                    "File": uploaded_file.name if uploaded_file else "",
                    "Ancillary Services": ancillary_details,
                    "Needs SCF": needs_scf,
                    "SCF Details": scf_dict,
                    "Status": "Pending",
                    "Created At": datetime.now().isoformat()
                }
                
                data = load_data()
                data.append(record)
                save_data(data)
                
                st.success("✅ Item successfully submitted!")
                st.balloons()
                
                # Show summary
                with st.expander("📊 Submission Summary"):
                    st.json(record)

    # Enhanced Summary View
    st.header("📁 Submitted Items")
    
    if data:
        # Filter options
        col1, col2, col3 = st.columns(3)
        with col1:
            category_filter = st.selectbox("Filter by Category", ["All"] + list(CATEGORY_VALUATION.keys()))
        with col2:
            port_filter = st.selectbox("Filter by Port", ["All"] + list(set(d.get('Port', '') for d in data if d.get('Port'))))
        with col3:
            scf_filter = st.selectbox("Filter by SCF Status", ["All", "SCF Requested", "No SCF"])
        
        # Apply filters
        filtered_data = data
        if category_filter != "All":
            filtered_data = [d for d in filtered_data if d.get('Category') == category_filter]
        if port_filter != "All":
            filtered_data = [d for d in filtered_data if d.get('Port') == port_filter]
        if scf_filter == "SCF Requested":
            filtered_data = [d for d in filtered_data if d.get('Needs SCF')]
        elif scf_filter == "No SCF":
            filtered_data = [d for d in filtered_data if not d.get('Needs SCF')]
        
        # Display filtered results
        if filtered_data:
            options = []
            for d in filtered_data:
                try:
                    item_name = d.get('Item Name', 'Unknown Item')
                    port = d.get('Port', 'Unknown Port')
                    status = d.get('Status', 'Pending')
                    options.append(f"{item_name} | {port} | {status}")
                except Exception as e:
                    st.warning(f"Error processing record: {e}")
                    continue
            
            if options:
                selected = st.selectbox("Select Item to View Details", options)
                selected_index = options.index(selected)
                rec = filtered_data[selected_index]
                
                # Enhanced display with tabs
                tab1, tab2, tab3 = st.tabs(["📋 Basic Info", "🛠️ Services", "💰 Finance"])
                
                with tab1:
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Item Name", rec.get('Item Name', 'N/A'))
                        st.metric("HS Code", rec.get('HS Code', 'N/A'))
                        st.metric("Quantity", rec.get('Quantity', 'N/A'))
                        st.metric("Port", rec.get('Port', 'N/A'))
                        st.metric("Category", rec.get('Category', 'N/A'))
                    
                    with col2:
                        st.metric("Original Price", f"${rec.get('Original Price', 0):,.2f}")
                        st.metric("Valuation %", f"{rec.get('Valuation %', 0)}%")
                        st.metric("Valued Price", f"${rec.get('Valued Price', 0):,.2f}")
                        st.metric("Urgency", rec.get('Urgency', 'N/A'))
                        st.metric("Status", rec.get('Status', 'Pending'))
                    
                    if rec.get('Reason'):
                        st.text_area("Reason for Rejection", rec.get('Reason'), disabled=True)
                
                with tab2:
                    if rec.get("Ancillary Services"):
                        for service, details in rec["Ancillary Services"].items():
                            with st.expander(f"🔧 {service}"):
                                if isinstance(details, dict):
                                    for k, v in details.items():
                                        st.write(f"**{k}:** {v}")
                                else:
                                    st.write(details)
                    else:
                        st.info("No ancillary services requested")
                
                with tab3:
                    if rec.get("Needs SCF") and rec.get("SCF Details"):
                        scf_details = rec["SCF Details"]
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.metric("SCF Requested", f"${scf_details.get('Requested', 0):,.2f}")
                            st.metric("Interest Rate", f"{scf_details.get('Interest Rate (%)', 0)}%")
                            st.metric("Duration", f"{scf_details.get('Duration (days)', 0)} days")
                        
                        with col2:
                            st.metric("Total Interest", f"${scf_details.get('Total Interest', 0):,.2f}")
                            st.metric("Total Repayment", f"${scf_details.get('Total Repayment', 0):,.2f}")
                            st.metric("Risk Score", scf_details.get('Risk Score', 'N/A'))
                    else:
                        st.info("No SCF requested for this item")
            else:
                st.info("No items match the selected filters.")
        else:
            st.info("No items match the selected filters.")
    else:
        st.info("No items submitted yet.")

# === SCF INVESTMENT OPPORTUNITIES ===
elif section == "SCF Investment Opportunities":
    st.title("💰 SCF Investment Opportunities")
    
    data = load_data()
    scf_items = [d for d in data if d.get("Needs SCF") and d.get("SCF Details", {}).get("Requested", 0) > 0]
    
    if not scf_items:
        st.warning("🚫 No SCF opportunities currently available.")
        st.info("Check back later for new investment opportunities!")
    else:
        # Investment dashboard
        st.header("📊 Investment Dashboard")
        
        col1, col2, col3, col4 = st.columns(4)
        metrics = calculate_scf_metrics(data)
        
        with col1:
            st.metric("Available Opportunities", metrics["total_opportunities"])
        with col2:
            st.metric("Total Investment Required", f"${metrics['total_requested']:,.0f}")
        with col3:
            st.metric("Average Interest Rate", f"{metrics['avg_interest_rate']:.1f}%")
        with col4:
            st.metric("Average Duration", f"{metrics['avg_duration']:.0f} days")
        
        # Analytics using built-in Streamlit charts
        st.subheader("📈 Investment Analytics")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Investment by category
            category_investments = {}
            for item in scf_items:
                category = item.get('Category', 'Unknown')
                scf_amount = item.get('SCF Details', {}).get('Requested', 0)
                if category in category_investments:
                    category_investments[category] += scf_amount
                else:
                    category_investments[category] = scf_amount
            
            if category_investments:
                st.write("**Investment Distribution by Category**")
                category_df = pd.DataFrame(list(category_investments.items()), 
                                         columns=['Category', 'Total Investment'])
                st.bar_chart(category_df.set_index('Category'))
        
        with col2:
            # Interest rate summary
            interest_rates = [d.get('SCF Details', {}).get('Interest Rate (%)', 0) for d in scf_items]
            if interest_rates:
                st.write("**Interest Rate Summary**")
                st.metric("Minimum Rate", f"{min(interest_rates):.1f}%")
                st.metric("Maximum Rate", f"{max(interest_rates):.1f}%")
                st.metric("Average Rate", f"{sum(interest_rates)/len(interest_rates):.1f}%")
        
        # Investment filters
        st.subheader("🔍 Filter Investment Opportunities")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            min_amt = st.slider("Minimum SCF Amount", 0.0, 50000.0, 0.0, step=100.0)
        with col2:
            max_rate = st.slider("Maximum Interest Rate (%)", 0.01, 50.0, 20.0, step=0.01)
        with col3:
            max_duration = st.slider("Maximum Duration (days)", 1, 180, 90, step=1)
        
        # Apply filters
        filtered_scf = [
            d for d in scf_items
            if (d.get("SCF Details", {}).get("Requested", 0) >= min_amt and
                d.get("SCF Details", {}).get("Interest Rate (%)", 0) <= max_rate and
                d.get("SCF Details", {}).get("Duration (days)", 0) <= max_duration)
        ]
        
        st.subheader(f"💼 Investment Opportunities ({len(filtered_scf)} available)")
        
        if filtered_scf:
            for idx, opp in enumerate(filtered_scf):
                with st.expander(f"🎯 Opportunity {idx+1}: {opp.get('Item Name', 'Unknown')} ({opp.get('Category', 'Unknown')})"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write("**Investment Details:**")
                        scf_details = opp.get('SCF Details', {})
                        st.write(f"• SCF Amount: ${scf_details.get('Requested', 0):,.2f}")
                        st.write(f"• Interest Rate: {scf_details.get('Interest Rate (%)', 0)}%")
                        st.write(f"• Duration: {scf_details.get('Duration (days)', 0)} days")
                        st.write(f"• Expected Return: ${scf_details.get('Total Interest', 0):,.2f}")
                        st.write(f"• Risk Level: {scf_details.get('Risk Score', 'N/A')}")
                    
                    with col2:
                        st.write("**Asset Details:**")
                        st.write(f"• Port: {opp.get('Port', 'Unknown')}")
                        st.write(f"• Asset Value: ${opp.get('Valued Price', 0):,.2f}")
                        st.write(f"• Quantity: {opp.get('Quantity', 'N/A')}")
                        st.write(f"• Urgency: {opp.get('Urgency', 'N/A')}")
                        st.write(f"• Status: {opp.get('Status', 'Pending')}")
                    
                    if st.button(f"💸 Express Interest (ID: {opp.get('ID', idx)})", key=f"fund_{idx}"):
                        st.success(f"✅ You have expressed interest in funding '{opp.get('Item Name', 'Unknown')}' at {opp.get('Port', 'Unknown')}!")
                        st.info("🔄 Our team will contact you within 24 hours to proceed with the investment.")
        else:
            st.info("🔍 No opportunities match your current filters. Try adjusting the criteria above.")

# === ADMIN DASHBOARD ===
elif section == "Admin Dashboard":
    st.title("🛠️ Admin Dashboard")
    
    data = load_data()
    
    if not data:
        st.info("📊 No data available. Start by adding some goods intake records.")
    else:
        # Admin metrics
        st.header("📈 System Overview")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Records", len(data))
        with col2:
            total_value = sum(d.get('Valued Price', 0) for d in data)
            st.metric("Total Asset Value", f"${total_value:,.0f}")
        with col3:
            scf_count = len([d for d in data if d.get("Needs SCF")])
            st.metric("SCF Requests", scf_count)
        with col4:
            pending_count = len([d for d in data if d.get("Status", "Pending") == "Pending"])
            st.metric("Pending Items", pending_count)
        
        # Data table with search and filter
        st.header("📋 All Records")
        
        # Convert to DataFrame for better display
        df_data = pd.DataFrame(data)
        
        # Search functionality
        search_term = st.text_input("🔍 Search records (by item name, port, or category)")
        
        if search_term:
            mask = (df_data['Item Name'].str.contains(search_term, case=False, na=False) |
                   df_data['Port'].str.contains(search_term, case=False, na=False) |
                   df_data['Category'].str.contains(search_term, case=False, na=False))
            filtered_df = df_data[mask]
        else:
            filtered_df = df_data
        
        # Display table
        if not filtered_df.empty:
            # Select columns to display
            display_columns = ['Item Name', 'Category', 'Port', 'Valued Price', 'Needs SCF', 'Status']
            available_columns = [col for col in display_columns if col in filtered_df.columns]
            
            st.dataframe(
                filtered_df[available_columns],
                use_container_width=True,
                hide_index=True
            )
            
            # Detailed view
            st.subheader("📋 Detailed Record View")
            
            selected_item = st.selectbox(
                "Select item for detailed view",
                options=range(len(filtered_df)),
                format_func=lambda x: f"{filtered_df.iloc[x]['Item Name']} - {filtered_df.iloc[x]['Port']}"
            )
            
            if selected_item is not None:
                selected_record = filtered_df.iloc[selected_item]
                
                # Display detailed information
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("🏷️ Basic Information")
                    st.json(selected_record[['Item Name', 'Category', 'Port', 'Quantity', 'Valued Price']].to_dict())
                
                with col2:
                    st.subheader("💰 Financial Information")
                    financial_info = {
                        'Original Price': selected_record.get('Original Price', 0),
                        'Valuation %': selected_record.get('Valuation %', 0),
                        'Valued Price': selected_record.get('Valued Price', 0),
                        'Needs SCF': selected_record.get('Needs SCF', False)
                    }
                    st.json(financial_info)
