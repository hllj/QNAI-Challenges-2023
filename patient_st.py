# Library
import json
import openai
import requests
import streamlit as st
import pandas as pd
from datetime import datetime

# Get content
def open_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as infile:
        return infile.read()
    
def get_summary(history_context):
    prompt = open_file('prompt/system_summary.txt').format(history_context=history_context)
    print("Summary", prompt)
    response = openai.ChatCompletion.create(
        model='gpt-3.5-turbo',  # Use the selected model name
        messages=[
            {"role": "system", "content": prompt}
        ],
        temperature=0.0,  # Set temperature
        max_tokens=2048,  # Set max tokens
        stream=False,
    )
    summary = response.choices[0].message.content
    return summary

# Custom Streamlit app title and icon
st.set_page_config(
    page_title="Trợ lý ảo",
    page_icon=":robot_face:",
)

st.title("🤖 Trợ lý ảo")

# Sidebar Configuration
st.sidebar.title("FPT AI CHALLENGE 2023")

html_code = """
<div style="display: flex; justify-content: space-between;">
    <img src="https://inkythuatso.com/uploads/thumbnails/800/2021/11/logo-fpt-inkythuatso-1-01-01-14-33-35.jpg" width="35%">
    <img src="https://hackathon.quynhon.ai/QAI-QuyNhon.c9fe9a3855f9b592.png" width="65%">
</div>
"""

st.sidebar.markdown(html_code, unsafe_allow_html=True)

# Enhance the sidebar styling
st.sidebar.subheader("Mô tả")
st.sidebar.write("Đây là một trợ lý y tế ảo giúp kết nối người dùng và dược sĩ\
    giúp người dùng có thể được điều trị các bệnh thông thường từ xa")

openai.api_key = st.secrets["OPENAI_API_KEY"]

system_text= open_file('prompt/system_patient.txt')

# CHAT MODEL
# Initialize DataFrame to store chat history
chat_history_df = pd.DataFrame(columns=["Timestamp", "Chat"])

st.sidebar.subheader("Làm mới cuộc trò chuyện")
# Reset Button
if st.sidebar.button(":arrows_counterclockwise: Làm mới"):
    # Save the chat history to the DataFrame before clearing it
    if st.session_state.messages:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        chat_history = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages])
        new_entry = pd.DataFrame({"Timestamp": [timestamp], "Chat": [chat_history]})
        chat_history_df = pd.concat([chat_history_df, new_entry], ignore_index=True)

        # Save the DataFrame to a CSV file
        chat_history_df.to_csv("chat_history.csv", index=False)

    # Clear the chat messages and reset the full response
    st.session_state.messages = []
    st.session_state.messages.append({"role": "system", "content": system_text})
    full_response = ""
    


# Initialize Chat Messages
if "messages" not in st.session_state:
    st.session_state.messages = []
    # Optional
    st.session_state.messages.append({"role": "system", "content": system_text})

# Initialize full_response outside the user input check
full_response = ""

# Display Chat History
for message in st.session_state.messages:
    if message["role"] != "system":
        with st.chat_message(message["role"]):
            st.markdown(message["content"]) 

# User Input and AI Response
if prompt := st.chat_input("Bạn cần hỗ trợ điều gì?"):
    # User Message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    print('chat', st.session_state.messages)
    # Assistant Message
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        
        # Initialize st.status for the task
        with st.status("Processing...", expanded=True) as status:
            for response in openai.ChatCompletion.create(
                model='gpt-3.5-turbo-0613',  # Use the selected model name
                messages=[
                    {"role": m["role"], "content": m["content"]}
                    for m in st.session_state.messages
                ],
                temperature=0.2,  # Set temperature
                max_tokens=2048,  # Set max tokens
                stream=True,
            ):
                full_response += response.choices[0].delta.get("content", "")
                message_placeholder.markdown(full_response + "▌")
            
            # Update st.status to show that the task is complete
            status.update(label="Complete!", state="complete", expanded=False)
            # st.status("Completed!").update("Response generated.")
        
        message_placeholder.markdown(full_response)
    
    # Append assistant's response to messages
    st.session_state.messages.append({"role": "assistant", "content": full_response})

    history_context = "\n"
    for m in st.session_state.messages[:-1]:
        if m["role"] == "user":
            history_context += "Câu trả lời: " + m["content"] + "\n"
        if m["role"] == "assistant":
            history_context += "Câu hỏi: " + m["content"] + "\n"
    history_context += "\n"

    if 'Tôi đã thu thập đủ thông tin' in full_response:
        st.markdown("Tôi đang xử lý thông tin và gửi thông tin tới cho bác sĩ.")
        
        with st.status("Đang tổng hợp thông tin ...", expanded=True) as status:
            st.session_state.summary = get_summary(history_context)
            # Update st.status to show that the task is complete
            status.update(label="Complete!", state="complete", expanded=False)
            # st.status("Completed!").update("Response generated.")
        
        st.markdown("Đây là một số thông tin mà tôi đã cung cấp được\n" + st.session_state.summary)
        
        with st.status("Đang gửi tới bác sĩ để chẩn đoán ...", expanded=True) as status:
            url = "http://0.0.0.0:8001/doctor"
            payload = json.dumps({
                "summary": st.session_state.summary
            })
            headers = {
                'Content-Type': 'application/json'
            }

            response = requests.request("POST", url, headers=headers, data=payload)

            doctor_response = 'Đơn thuốc của bác sĩ:' + response.json()['data']['response']['response']
            # Update st.status to show that the task is complete
            status.update(label="Complete!", state="complete", expanded=False)
            # st.status("Completed!").update("Response generated.")
    
        print('Đơn thuốc của bác sĩ:', doctor_response)

        st.markdown(doctor_response)