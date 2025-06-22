import streamlit as st
import requests
import json
from datetime import datetime

# Configuration
API_BASE_URL = "http://localhost:8000"

st.set_page_config(
    page_title="LLM-Powered Grievance System",
    page_icon="",
    layout="wide"
)

st.title("LLM-Powered Grievance Management System")
st.markdown("---")

# Sidebar for navigation
page = st.sidebar.selectbox(
    "Choose an action:",
    ["Collect Complaint", "Retrieve Complaints", "View All Complaints"]
)

if page == "Collect Complaint":
    st.header("Collect and Store Complaint")
    st.markdown("Use LLM to extract complaint details from natural language and store in database")
    
    # Complaint collection form
    with st.form("complaint_collection"):
        user_message = st.text_area(
            "Describe your complaint (include your name, mobile number, and complaint details):",
            placeholder="Example: My name is John Doe, mobile number 9876543210. I'm having issues with the billing service. The charges are incorrect and customer support is not helpful.",
            height=150
        )
        
        submitted = st.form_submit_button("Process with LLM")
        
        if submitted and user_message:
            with st.spinner("Processing with LLM..."):
                try:
                    response = requests.post(
                        f"{API_BASE_URL}/collect-complaint",
                        json={"message": user_message},
                        timeout=30
                    )
                    
                    if response.status_code == 200:
                        complaint_data = response.json()
                        st.success("Complaint successfully processed and stored!")
                        
                        # Display extracted data
                        col1, col2 = st.columns(2)
                        with col1:
                            st.subheader("Extracted Information")
                            st.write(f"**Name:** {complaint_data['name']}")
                            st.write(f"**Mobile:** {complaint_data['mobile_number']}")
                            st.write(f"**Category:** {complaint_data['category']}")
                            st.write(f"**Priority:** {complaint_data['priority']}")
                        
                        with col2:
                            st.subheader("Complaint Details")
                            st.write(f"**Complaint ID:** {complaint_data['complaint_id']}")
                            st.write(f"**Status:** {complaint_data['status']}")
                            st.write(f"**Created:** {complaint_data['created_at']}")
                            st.write(f"**Updated:** {complaint_data['updated_at']}")
                        
                        st.subheader("Complaint Text")
                        st.write(complaint_data['complaint_text'])
                        
                    elif response.status_code == 400:
                        error_data = response.json()
                        st.error(f"Incomplete data: {error_data['detail']}")
                        st.info("Please include your name, mobile number, and complaint description in your message.")
                    
                    else:
                        st.error(f"Error: {response.status_code} - {response.text}")
                        
                except requests.exceptions.RequestException as e:
                    st.error(f"Connection error: {e}")
                    st.info("Make sure the FastAPI server is running on http://localhost:8000")

elif page == "Retrieve Complaints":
    st.header("Retrieve Complaint Information")
    st.markdown("Use LLM to intelligently search and present complaint information")
    
    # Complaint retrieval form
    with st.form("complaint_retrieval"):
        user_query = st.text_area(
            "Ask about complaints (include mobile number, name, or general query):",
            placeholder="Example: Show me complaints for mobile number 9876543210\nOR\nWhat complaints does John Doe have?\nOR\nShow me recent complaints",
            height=100
        )
        
        submitted = st.form_submit_button("Search with LLM")
        
        if submitted and user_query:
            with st.spinner("Searching with LLM..."):
                try:
                    response = requests.post(
                        f"{API_BASE_URL}/retrieve-complaints",
                        json={"message": user_query},
                        timeout=30
                    )
                    
                    if response.status_code == 200:
                        result_data = response.json()
                        st.success(f"Found {result_data['complaints_found']} complaint(s)")
                        
                        # Display LLM response
                        st.subheader("LLM Response")
                        st.write(result_data['response'])
                        
                        # Display complaints if any found
                        if result_data['complaints']:
                            st.subheader(f"Complaint Details ({len(result_data['complaints'])})")
                            
                            for i, complaint in enumerate(result_data['complaints'], 1):
                                with st.expander(f"Complaint {i}: {complaint['complaint_id']} - {complaint['name']}"):
                                    col1, col2 = st.columns(2)
                                    with col1:
                                        st.write(f"**Name:** {complaint['name']}")
                                        st.write(f"**Mobile:** {complaint['mobile_number']}")
                                        st.write(f"**Category:** {complaint['category']}")
                                        st.write(f"**Priority:** {complaint['priority']}")
                                    
                                    with col2:
                                        st.write(f"**Status:** {complaint['status']}")
                                        st.write(f"**Created:** {complaint['created_at']}")
                                        st.write(f"**Updated:** {complaint['updated_at']}")
                                    
                                    st.write("**Complaint:**")
                                    st.write(complaint['complaint_text'])
                        else:
                            st.info("No complaints found matching your query.")
                    
                    else:
                        st.error(f"Error: {response.status_code} - {response.text}")
                        
                except requests.exceptions.RequestException as e:
                    st.error(f"Connection error: {e}")
                    st.info("Make sure the FastAPI server is running on http://localhost:8000")

elif page == "View All Complaints":
    st.header("All Complaints")
    st.markdown("View all complaints in the database")
    
    if st.button("Refresh Data"):
        try:
            response = requests.get(f"{API_BASE_URL}/complaints", timeout=10)
            
            if response.status_code == 200:
                complaints = response.json()
                st.success(f"Loaded {len(complaints)} complaints")
                
                if complaints:
                    # Create a DataFrame-like display
                    for complaint in complaints:
                        with st.expander(f"{complaint['complaint_id']} - {complaint['name']} ({complaint['status']})"):
                            col1, col2 = st.columns(2)
                            with col1:
                                st.write(f"**Name:** {complaint['name']}")
                                st.write(f"**Mobile:** {complaint['mobile_number']}")
                                st.write(f"**Category:** {complaint['category']}")
                                st.write(f"**Priority:** {complaint['priority']}")
                            
                            with col2:
                                st.write(f"**Status:** {complaint['status']}")
                                st.write(f"**Created:** {complaint['created_at']}")
                                st.write(f"**Updated:** {complaint['updated_at']}")
                            
                            st.write("**Complaint:**")
                            st.write(complaint['complaint_text'])
                else:
                    st.info("No complaints found in the database.")
            
            else:
                st.error(f"Error: {response.status_code} - {response.text}")
                
        except requests.exceptions.RequestException as e:
            st.error(f"Connection error: {e}")
            st.info("Make sure the FastAPI server is running on http://localhost:8000")

