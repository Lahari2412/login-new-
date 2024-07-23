import streamlit as st
from streamlit_modal import Modal
import requests
from pymongo import MongoClient
from streamlit_extras.switch_page_button import switch_page
import pandas as pd
import time
import urllib.parse

# MongoDB configuration
MONGO_URI = "mongodb://localhost:27017/"
client = MongoClient(MONGO_URI)
db = client["recruiter_ai"]
collection = db["job_descriptions"]

st.title("HR Recruiter AI")

if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    switch_page("login")

# Define modal
modal = Modal("Job Description", key="Job_Description", max_width=1000, padding=20)

# Initialize session state variables
if 'current_job_description' not in st.session_state:
    st.session_state['current_job_description'] = ""
if 'selected_job_id' not in st.session_state:
    st.session_state['selected_job_id'] = None
if 'modal_open' not in st.session_state:
    st.session_state['modal_open'] = False
if 'modal_content' not in st.session_state:
    st.session_state['modal_content'] = ""
if 'job_submitted' not in st.session_state:
    st.session_state['job_submitted'] = False
if 'job_updated' not in st.session_state:
    st.session_state['job_updated'] = False
if 'JD_success_flag' not in st.session_state:
    st.session_state['JD_success_flag'] = False
if 'JD_retrieve_error_flag' not in st.session_state:
    st.session_state['JD_retrieve_error_flag'] = False
if 'JD_create_error_flag' not in st.session_state:
    st.session_state['JD_create_error_flag'] = False
if 'JD_warning_flag' not in st.session_state:
    st.session_state['JD_warning_flag'] = False
if 'update_success_flag' not in st.session_state:
    st.session_state['update_success_flag'] = False
if 'update_error_flag' not in st.session_state:
    st.session_state['update_error_flag'] = False
if 'update_fetch_error_flag' not in st.session_state:
    st.session_state['update_fetch_error_flag'] = False
if 'update_warning_flag' not in st.session_state:
    st.session_state['update_warning_flag'] = False
if 'view_candidates' not in st.session_state:
    st.session_state['view_candidates'] = False
if 'selected_candidates' not in st.session_state:
    st.session_state['selected_candidates'] = []
if 'creating_new_job' not in st.session_state:
    st.session_state['creating_new_job'] = False

if 'selected_candidates' not in st.session_state:
    st.session_state['selected_candidates'] = []
if 'checked_candidates' not in st.session_state:
    st.session_state['checked_candidates'] = []

# Alert boxes

# Display success message at the top if the flag is set
if st.session_state['JD_success_flag']:
    st.success("Job description created successfully!")
    st.session_state['success_flag'] = False 


if st.session_state['JD_retrieve_error_flag']:
    st.error("Failed to retrieve job ID or job description from response.")
    st.session_state['JD_retrieve_error_flag'] = False 

if st.session_state['JD_create_error_flag']:
    st.error("Failed to create job description. Please try again.")
    st.session_state['JD_create_error_flag'] = False 
    

if st.session_state['JD_warning_flag']:
    st.warning("Please enter a job description before submitting.")
    st.session_state['JD_warning_flag'] = False   

# Function to fetch job descriptions from MongoDB
def fetch_job_descriptions():
    return list(collection.find({}, {"_id": 1, "prompt": 1, "job_description": 1}).sort([('_id', -1)]))

# Function to handle New Job Description button
def new_job_description():
    st.session_state['current_job_description'] = ""
    st.session_state['selected_job_id'] = None
    st.session_state['job_submitted'] = False
    st.session_state['job_updated'] = False
    st.session_state['creating_new_job'] = True
    st.session_state['view_candidates'] = False  # Hide candidates when creating a new job description

# Function to handle logout
def logout():
    st.session_state.logged_in = False
    st.session_state['current_job_description'] = ""
    st.session_state['selected_job_id'] = None
    st.session_state['modal_open'] = False
    st.session_state['modal_content'] = ""
    st.session_state['job_submitted'] = False
    st.session_state['job_updated'] = False
    st.session_state['view_candidates'] = False
    st.session_state['selected_candidates'] = []
    st.session_state['creating_new_job'] = False
    switch_page("login")

# Sidebar
with st.sidebar:
    # Fetch job descriptions from MongoDB
    job_descriptions = fetch_job_descriptions()

    # New Job Description button
    st.sidebar.button("New Job Description", on_click=new_job_description)

    # Logout button
    st.sidebar.button("Logout", on_click=logout)

    st.sidebar.markdown("---")  # Separator

    st.sidebar.markdown("### Job Id's")

    # Display existing job descriptions as clickable links
    for job in job_descriptions:
        job_id = job['_id']
        job_label = f"Job ID: {job_id}"

        # Show button and handle job ID selection
        is_selected = st.session_state['selected_job_id'] == job_id
        button_text = f"{job_label} {'(Selected)' if is_selected else ''}"

        if st.sidebar.button(button_text, key=f"job_{job_id}"):
            st.session_state['selected_job_id'] = job_id
            st.session_state['current_job_description'] = job.get('prompt', '')  # Use .get() to safely access dictionary keys
            st.session_state['job_submitted'] = True
            st.session_state['job_updated'] = False
            st.session_state['creating_new_job'] = False  # Reset creating_new_job flag
            st.session_state['view_candidates'] = False  # Hide candidates when selecting a job description
            
            # Refresh the page to reflect changes
            st.experimental_rerun()

# Job description input
job_description = st.text_area("Describe the Job Profile", value=st.session_state['current_job_description'])

# Create columns for buttons
col1, col2 = st.columns(2)

with col1:
    # Submit button
    submit_disabled = st.session_state['selected_job_id'] is not None
    if st.button("Submit", disabled=submit_disabled):
        if job_description:
            # API endpoint
            api_url = "http://localhost:8081/api/v1/jd"
            
            # Payload to send to the API
            payload = {"prompt": job_description}
            
            # Make the POST request
            response = requests.post(api_url, json=payload)

            if response.status_code == 201:
                # Parse the response
                jd_response = response.json()
                
                # Extract the job ID, prompt, and job description
                job_id = jd_response.get("id")
                prompt_saved = job_description
                job_description_created = jd_response.get("job_description")
                
                if job_id and job_description_created:
                    # Store job ID, prompt, and job description in MongoDB
                    collection.insert_one({"_id": job_id, "prompt": prompt_saved, "job_description": job_description_created})
                    
                    # Update session state to select the newly created job
                    st.session_state['selected_job_id'] = job_id
                    st.session_state['current_job_description'] = prompt_saved
                    st.session_state['job_submitted'] = True
                    
                    # Display success message
                    st.session_state['JD_success_flag'] = True
                    
                    # Update job descriptions in sidebar
                    st.experimental_rerun()
                else:
                    st.session_state['JD_retrieve_error_flag'] = True
            else:
                st.session_state['JD_create_error_flag'] = True
        else:
            st.session_state['JD_warning_flag'] = True

with col2:
    # Only show these buttons if a job is submitted
    if st.session_state['job_submitted']:
        if st.session_state['selected_job_id']:
            col1, col2 = st.columns(2)
            
            with col1:
                open_modal = st.button("View Job Description")
                if open_modal:
                    modal.open()
            
            with col2:
                view_candidates_button = st.button("View Candidates")
                if view_candidates_button:
                    st.session_state['view_candidates'] = True

if modal.is_open():
    with modal.container():
        
        if st.session_state['update_success_flag']:
            st.success("Job description updated successfully!")
            st.session_state['update_success_flag'] = False  # Reset the flag

        if st.session_state['update_error_flag']:
            st.error("Failed to update job description. Please try again.")
            st.session_state['update_error_flag'] = False  # Reset the flag
        
        if st.session_state['update_fetch_error_flag']:
            st.error("Failed to fetch job description. Please try again.")
            st.session_state['update_fetch_error_flag'] = False  # Reset the flag

        if st.session_state['update_warning_flag']:
            st.warning("No job description selected.")
            st.session_state['update_warning_flag'] = False  # Reset the flag


        if st.session_state['selected_job_id'] is not None:
            api_url = f"http://localhost:8081/api/v1/jd/{st.session_state['selected_job_id']}"
          
            response = requests.get(api_url)

            if response.status_code == 200:
                jd_response = response.json()

                job_description = st.text_area("Job Description", value=jd_response.get('job_description', ''), height=250, disabled=not st.session_state['job_updated'])

                col1, col2 = st.columns(2)

                with col1:
                    edit_button = st.button("Edit")
                    if edit_button:
                        st.session_state['job_updated'] = True
                        st.experimental_rerun()

                with col2:
                    if st.session_state['job_updated']:
                        update_button = st.button("Update")
                        if update_button:
                            update_url = api_url
                            payload = {
                                "job_description": job_description
                            }
                            update_response = requests.put(update_url, json=payload)

                            if update_response.status_code == 200:
                                st.session_state['update_success_flag'] = True
                                st.session_state['job_updated'] = False
                                st.experimental_rerun()
                            else:
                                st.session_state['update_error_flag'] = True
            else:
                st.session_state['update_fetch_error_flag'] = True
        else:
            st.session_state['update_warning_flag'] = True



# Display candidates if the flag is set
if st.session_state['view_candidates']:
    st.subheader("Candidates")
    
    col1, col2, col3, col4, col5 = st.columns([1, 3, 3, 3, 3])
    with col1:
        st.markdown("**Select**")
    with col2:
        st.markdown("**Name**")
    with col3:
        st.markdown("**Email**")
    with col4:
        st.markdown("**Mobile**")
    with col5:
        st.markdown("**Status**")

    candidates_api_url = "http://localhost:8084/api/v1/candidate/"
    response = requests.get(candidates_api_url)
    
    if response.status_code == 200:
        candidates = response.json()
        
        df_candidates = pd.DataFrame(candidates)
        df_candidates['Select'] = False
        
        for idx, row in df_candidates.iterrows():
            col1, col2, col3, col4, col5 = st.columns([1, 3, 3, 3, 3])
            
            with col1:
                # Use a unique key for each checkbox to store its state
                if st.checkbox("", key=f"candidate_{idx}"):
                    if row.to_dict() not in st.session_state['checked_candidates']:
                        st.session_state['checked_candidates'].append(row.to_dict())
            with col2:
                st.write(row['name'])
            with col3:
                st.write(row['email'])
            with col4:
                st.write(row['mobile'])
            with col5:
                st.write("Yes" if row['status'] else "No")
        
        # Schedule Interview button
        if st.button("Schedule Interview"):
            for candidate in st.session_state['checked_candidates']:
                phone_number = candidate['mobile']
                # Replace with your WhatsApp API URL
                whatsapp_api_url = "https://api.whatsapp.com/send"
                message = "Hello! We would like to schedule an interview with you."
                encoded_message = urllib.parse.quote(message)
                whatsapp_url = f"{whatsapp_api_url}?phone={phone_number}&text={encoded_message}"
                
                st.write(f"Sending message to {phone_number}: {whatsapp_url}")
                # You can use requests to send an actual API request if needed
                response = requests.get(whatsapp_url)
                if response.status_code == 200:
                    st.success(f"Message sent to {phone_number}")
                else:
                    st.error(f"Failed to send message to {phone_number}")
            
            # Clear selected candidates after scheduling interviews
            st.session_state['checked_candidates'] = []
        
    else:
        st.error("Failed to fetch candidates.")