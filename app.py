import streamlit as st
import requests
import json
import os
import re
import anthropic
import pandas as pd
from PIL import Image
from io import BytesIO
import datetime
import base64
from dotenv import load_dotenv
from auth_original import authenticated_layout
from database import init_db, get_user_limits, increment_image_count, delete_user, get_all_users, update_user_limit, is_admin, save_report, get_user_reports
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Image as PDFImage, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from streamlit.components.v1 import html
import time as t
import openpyxl
from openpyxl.drawing.image import Image as XLImage

st.set_page_config(page_title="EstateGenius AI", page_icon="🔍", layout="wide")

load_dotenv()
init_db()

ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
SEARCH_API_KEY = os.getenv('SEARCH_API_KEY')

def create_pdf_report(results, output_file):
    """Create PDF report with images and analyses"""
    doc = SimpleDocTemplate(output_file, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()

    elements.append(Paragraph("EstateGenius AI Report", styles['Title']))

    data = [["Image", "File Name", "Analysis"]]

    for result in results:
        try:
            img = PDFImage(result['temp_image_path'], width=150, height=150)
            row = [
                img,
                Paragraph(result['name'], styles['BodyText']),
                Paragraph(result['analysis'], styles['BodyText'])
            ]
            data.append(row)
        except Exception as e:
            st.error(f"PDF error: {str(e)}")

    table = Table(data, colWidths=[160, 160, 260])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.grey),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('FONTSIZE', (0,0), (-1,0), 12),
        ('BOTTOMPADDING', (0,0), (-1,0), 12),
        ('BACKGROUND', (0,1), (-1,-1), colors.beige),
        ('GRID', (0,0), (-1,-1), 1, colors.black),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))

    elements.append(table)

    try:
        doc.build(elements)
        return True
    except Exception as e:
        st.error(f"PDF creation failed: {str(e)}")
        return False

def create_excel_report(results, output_file):
    """Create Excel report with images and analyses"""
    wb = openpyxl.Workbook()
    ws = wb.active

    # Headers
    headers = ['Image', 'File Name', 'Analysis']
    for col, header in enumerate(headers, 1):
        ws.cell(row=1, column=col, value=header).font = openpyxl.styles.Font(bold=True)

    # Add data
    for row_idx, result in enumerate(results, 2):
        try:
            if os.path.exists(result['temp_image_path']):
                img = XLImage(result['temp_image_path'])
                img.width, img.height = 200, 200
                ws.add_image(img, f'A{row_idx}')
            
            ws.cell(row=row_idx, column=2, value=result['name'])
            analysis_cell = ws.cell(row=row_idx, column=3, value=result['analysis'])
            analysis_cell.alignment = openpyxl.styles.Alignment(wrap_text=True, vertical='top')
            ws.row_dimensions[row_idx].height = max(120, len(result['analysis'].split('\n')) * 15)
            
        except Exception as e:
            st.error(f"Excel error: {str(e)}")

    # Formatting
    ws.column_dimensions['A'].width = 30
    ws.column_dimensions['B'].width = 30
    ws.column_dimensions['C'].width = 50

    try:
        wb.save(output_file)
        return True
    except Exception as e:
        st.error(f"Save error: {str(e)}")
        return False

def create_basic_report(images):
    """Create report data without API processing and analysis"""
    results = []
    temp_files = []
    
    for image in images:
        try:
            response = requests.get(image['url'])
            if response.status_code != 200:
                continue
                
            img_path = f"temp_{image['id']}.jpg"
            with Image.open(BytesIO(response.content)) as img:
                img.convert('RGB').save(img_path)
            temp_files.append(img_path)

            results.append({
                'name': image['name'],
                'temp_image_path': img_path,
                'analysis': ''  # Empty analysis column
            })
            
        except Exception as e:
            st.error(f"Basic processing error: {str(e)}")
            
    return results, temp_files

def get_anthropic_analysis(json_data):
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    prompt = f"""Analyze product search results and provide structured summary following these guidelines:
    1. Name: If there are multiple listings with same name or almost similar name then the item must be exactly 
    the same item as that in image. then assertively say the item: "Name", if there all the item listings  mutually exclusive
    then the first listing is likely the item similar to the image then say item: "likely- first listing item name"
    2. ebay prices: give the prices seen in the all the ebay listings seperated by commas, just the prices
    3. etsy prices:give the prices seen in the all the etsy listings seperated by commas, just the prices
    4. invaluable prices:give the prices seen in the all the invaluable listings seperated by commas, just the prices
    5. other auctions houses:give the prices seen in the all the other auction houses listings seperated by commas, just the prices
    6. opinion: tell succintly what you know about the item, its collector market and trends.
    7. give all the above bullet points for clear reading.

    Data: {json.dumps(json_data, indent=2)}"""

    try:
        message = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}]
        )
        return message.content[0].text if message.content else "No analysis generated"
    except Exception as e:
        st.error(f"Analysis error: {str(e)}")
        return "Analysis failed"

def search_google_lens(image_url):
    try:
        response = requests.get(
            "https://www.searchapi.io/api/v1/search",
            params={
                "engine": "google_lens",
                "url": image_url,
                "api_key": SEARCH_API_KEY
            }
        )
        return response.json().get("visual_matches", [])[:15]
    except Exception as e:
        st.error(f"Lens search failed: {str(e)}")
        return []

def extract_file_ids_from_folder(folder_url):
    try:
        folder_id = folder_url.split('/')[-1]
        files_url = f"https://drive.google.com/drive/folders/{folder_id}"
        response = requests.get(files_url)
        
        pattern = r"https://drive\.google\.com/file/d/([a-zA-Z0-9_-]+)"
        file_ids = list(set(re.findall(pattern, response.text)))
        
        return [{'id': fid, 'url': f"https://drive.google.com/uc?id={fid}", 'name': f"image_{fid}.jpg"} for fid in file_ids]
    except Exception as e:
        st.error(f"Error extracting files: {str(e)}")
        return []

def admin_panel():
    st.header("🛠️ Admin Dashboard")
    st.subheader("User Management")
    users = get_all_users()
    df = pd.DataFrame(users, columns=["ID", "Username", "Email", "Role", "Max Images", "Processed Images"])
    st.dataframe(df)

    st.markdown("---")
    st.subheader("Delete User")
    del_id = st.number_input("Enter User ID to delete", min_value=1)
    if st.button("Delete User"):
        if delete_user(del_id):
            st.success("User deleted successfully")
            st.rerun()
        else:
            st.error("Failed to delete user")

    st.markdown("---")
    st.subheader("Set Processing Limits")
    limit_user_id = st.number_input("User ID for limit update", min_value=1)
    new_limit = st.number_input("New maximum images", min_value=1, value=100)
    if st.button("Update Limit"):
        if update_user_limit(limit_user_id, new_limit):
            st.success("Image limit updated")
            st.rerun()
        else:
            st.error("Failed to update limit")

def main_application():
    st.title("🔍 EstateGenius AI")
    st.markdown("---")

    with st.sidebar:
        st.header("User Controls")
        st.write(f"Logged in as: **{st.session_state.authenticated_user}**")
        
        if is_admin(st.session_state.authenticated_user):
            if st.checkbox("Show Admin Panel"):
                admin_panel()
                return
        
        current_count, max_allowed = get_user_limits(st.session_state.authenticated_user)
        st.metric("Processed Images", f"{current_count}/{max_allowed}")
        st.markdown("---")
        st.button("Logout", on_click=lambda: st.session_state.pop("authenticated_user"), key="logout_button")
        
        # Find this section in main_application() and update it:
        st.subheader("📚 Past Reports")
        reports = get_user_reports(st.session_state.authenticated_user)

        # Group reports by timestamp
        report_groups = {}
        for report in reports:
            try:
                full_path = report[0]
                # Update the path to use the mounted volume path
                if not full_path.startswith('/var/lib/estateai/reports'):
                    full_path = os.path.join('/var/lib/estateai/reports', os.path.basename(full_path))
                
                base_name = os.path.basename(full_path).split('.')[0]
                
                parts = base_name.split('_')
                if len(parts) >= 3:
                    timestamp_str = f"{parts[1]}_{parts[2]}"
                    report_groups.setdefault(timestamp_str, []).append(full_path)
            except Exception as e:
                st.error(f"Error processing report {full_path}: {str(e)}")

        # Display grouped reports
        for timestamp_str, report_paths in report_groups.items():
            try:
                report_date = datetime.datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
                
                with st.expander(f"📅 {report_date.strftime('%Y-%m-%d %H:%M')}"):
                    for path in report_paths:
                        try:
                            if path.endswith('.pdf'):
                                btn_label = "📄 PDF Version"
                                mime_type = "application/pdf"
                            elif path.endswith('.xlsx'):
                                btn_label = "📊 Excel Version"
                                mime_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                            else:
                                continue
                            
                            with open(path, "rb") as f:
                                st.download_button(
                                    label=btn_label,
                                    data=f.read(),
                                    file_name=os.path.basename(path),
                                    mime=mime_type
                                )
                        except Exception as e:
                            st.error(f"Error loading file {path}: {str(e)}")
            except Exception as e:
                st.error(f"Error loading report {timestamp_str}: {str(e)}")

    folder_url = st.text_input("Google Drive Folder URL", 
                              placeholder="https://drive.google.com/drive/folders/...")

    col1, col2 = st.columns(2)
    with col1:
        process_button = st.button("Process Images with Analysis", type="primary")
    with col2:
        basic_process_button = st.button("Process without Appraisal", type="secondary")

    if process_button or basic_process_button:
        if not folder_url:
            st.error("Please enter a valid folder URL")
            return

        with st.status("🔍 Processing images...", expanded=True) as status:
            st.write("Initializing...")
            start_time = datetime.datetime.now()
            
            images = extract_file_ids_from_folder(folder_url)
            image_count = len(images)
            
            if image_count > 25:
                st.warning("Processing first 25 images of the folder")
                images = images[:25]

            current_count, max_allowed = get_user_limits(st.session_state.authenticated_user)
            if current_count + image_count > max_allowed:
                st.error(f"Image limit exceeded: {current_count + image_count}/{max_allowed}")
                return

            progress_bar = st.progress(0)
            status_text = st.empty()

            if basic_process_button:
                # Process without analysis
                results, temp_files = create_basic_report(images)
                status.update(label="📄 Creating basic reports...", state="running")
            else:
                # Full processing with analysis
                results = []
                temp_files = []
                
                for idx, image in enumerate(images):
                    try:
                        progress = (idx + 1) / len(images)
                        progress_bar.progress(progress)
                        status_text.write(f"Processing image {idx + 1} of {len(images)}")

                        response = requests.get(image['url'])
                        if response.status_code != 200:
                            continue
                            
                        img_path = f"temp_{image['id']}.jpg"
                        with Image.open(BytesIO(response.content)) as img:
                            img.convert('RGB').save(img_path)
                        temp_files.append(img_path)

                        lens_results = search_google_lens(image['url'])
                        if lens_results:
                            analysis = get_anthropic_analysis(lens_results)
                            results.append({
                                'name': image['name'],
                                'temp_image_path': img_path,
                                'analysis': analysis
                            })

                    except Exception as e:
                        st.error(f"Image {idx+1} error: {str(e)}")

            # Find this section in main_application() and update it:
            if results:
                base_name = f"report_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
                # Update the reports path to use the persistent volume
                reports_dir = "/var/lib/estateai/reports"
                os.makedirs(reports_dir, exist_ok=True)
                
                pdf_report_name = os.path.join(reports_dir, f"{base_name}.pdf")
                excel_report_name = os.path.join(reports_dir, f"{base_name}.xlsx")
                
                pdf_success = create_pdf_report(results, pdf_report_name)
                excel_success = create_excel_report(results, excel_report_name)
                
                if pdf_success and excel_success:
                    save_report(st.session_state.authenticated_user, pdf_report_name)
                    save_report(st.session_state.authenticated_user, excel_report_name)
                    increment_image_count(st.session_state.authenticated_user, image_count)
                    
                    status.update(label="✅ Processing complete!", state="complete")
                    
                    with open(pdf_report_name, "rb") as f_pdf, open(excel_report_name, "rb") as f_xlsx:
                        col1, col2 = st.columns(2)
                        with col1:
                            st.download_button(
                                label="📥 Download PDF Report",
                                data=f_pdf.read(),
                                file_name=os.path.basename(pdf_report_name),
                                mime="application/pdf"
                            )
                        with col2:
                            st.download_button(
                                label="📥 Download Excel Report",
                                data=f_xlsx.read(),
                                file_name=os.path.basename(excel_report_name),
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                            )

            # Cleanup temp files
            for temp_file in temp_files:
                try:
                    os.remove(temp_file)
                except Exception as e:
                    st.warning(f"Failed to remove temporary file {temp_file}: {str(e)}")

if __name__ == "__main__":
    authenticated_layout(main_application)