import os
import zipfile
import fitz
from pyrogram import Client, filters
from dotenv import load_dotenv

load_dotenv()

API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

app = Client("pdf_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

DOWNLOAD_DIR = "downloads"

if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)


@app.on_message(filters.document & filters.private)
async def handle_zip(client, message):
    """Handles zip files uploaded by the user"""
    file = message.document

    if not file.file_name.endswith(".zip"):
        await message.reply("Please upload a .zip file.")
        return

    # Download the ZIP file
    file_path = os.path.join(DOWNLOAD_DIR, file.file_name)
    await message.reply("Downloading the ZIP file...")
    await message.download(file_path)

    # Extract the ZIP file
    extract_folder = os.path.join(DOWNLOAD_DIR, file.file_name.replace(".zip", ""))
    os.makedirs(extract_folder, exist_ok=True)

    try:
        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            zip_ref.extractall(extract_folder)
        await message.reply("Extracted ZIP file successfully.")
    except Exception as e:
        await message.reply(f"Error extracting ZIP: {e}")
        return

    # Find all PDF files inside the extracted folder
    pdf_files = []
    for root, _, files in os.walk(extract_folder):
        for f in files:
            if f.endswith(".pdf"):
                pdf_files.append(os.path.join(root, f))

    if not pdf_files:
        await message.reply("No PDF files found inside the ZIP.")
        return

    processed_pdfs = []

    for pdf_file in pdf_files:
        # Extract odd-numbered pages from each PDF
        output_pdf = os.path.join(DOWNLOAD_DIR, f"{os.path.basename(pdf_file)}")
        
        try:
            doc = fitz.open(pdf_file)
            new_doc = fitz.open()

            for page_num in range(len(doc)):
                if (page_num) % 2 == 0:
                    new_doc.insert_pdf(doc, from_page=page_num, to_page=page_num)

            new_doc.save(output_pdf)
            new_doc.close()
            processed_pdfs.append(output_pdf)
        except Exception as e:
            await message.reply(f"Error processing {pdf_file}: {e}")

    # Send the processed PDFs back to the user
    if processed_pdfs:
        for processed_pdf in processed_pdfs:
            await message.reply_document(processed_pdf, caption=f"Processed: {os.path.basename(processed_pdf)}")
    
    # Cleanup: Delete files
    os.remove(file_path)
    for pdf in processed_pdfs:
        os.remove(pdf)
    for root, dirs, files in os.walk(extract_folder, topdown=False):
        for f in files:
            os.remove(os.path.join(root, f))
        for d in dirs:
            os.rmdir(os.path.join(root, d))
    os.rmdir(extract_folder)


# Run the bot
app.run()
