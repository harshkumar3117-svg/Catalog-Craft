import base64
import json
from io import BytesIO
import ollama
import pandas as pd
from PIL import Image
from pydantic import BaseModel, Field
import streamlit as st

class ProductListing(BaseModel):
    title: str = Field(description="Marketplace-specific high-converting product title")
    bullet_points: list[str] = Field(description="5 targeted bullet points")
    seo_keywords: list[str] = Field(description="Search tags and keywords")
    meta_description: str = Field(description="150-160 character meta description")
    suggested_price_strategy: str = Field(description="Psychological pricing tip or price band")
    long_description_html: str = Field(description="Clean HTML description with formatting")

PLATFORM_PROMPTS = {
    "Amazon": "Follow strict Amazon guidelines: Title under 200 chars including brand/material/size. Exactly 5 bullets, each starting with a capitalized benefit header (e.g., 'DURABLE BUILD: ...'). Dense SEO keywords.",
    "Etsy": "Adopt a warm, artisanal, story-focused tone highlighting handcrafted value and gifting potential. Produce 13 specific Etsy-friendly tags under 20 characters.",
    "Shopify": "Write engaging D2C brand copy with conversion-oriented hook, clean feature benefits, and meta description ready for Google indexing.",
    "Meesho": "Focus on high value-for-money, fabric/material clarity, daily-use practicality, and simple conversational terms."
}

def prepare_image_bytes(img: Image.Image, max_size: int = 512) -> bytes:
    img = img.convert("RGB")  # ensure no alpha channel issues
    img.thumbnail((max_size, max_size), Image.LANCZOS)
    buf = BytesIO()
    img.save(buf, format="JPEG", quality=85, optimize=True)
    return buf.getvalue()

def generate_listing(
    image_bytes: bytes | None,
    product_notes: str,
    target_platform: str,
    target_audience: str,
    language: str,
    model_name: str = "llama3.2-vision",
) -> dict:
    platform_rule = PLATFORM_PROMPTS.get(target_platform, "Create an e-commerce listing.")

    system_prompt = f"""
    You are an expert e-commerce copywriter.
    Platform: {target_platform}.
    Platform Rule: {platform_rule}
    Target Audience: {target_audience}
    Output Language: {language}

    STRICT: Output ONLY raw JSON matching this schema, no markdown wrapping, no explanation:
    {{
      "title": "string",
      "bullet_points": ["string", "string", "string", "string", "string"],
      "seo_keywords": ["string", "string", "string"],
      "meta_description": "string",
      "suggested_price_strategy": "string",
      "long_description_html": "string"
    }}
    """

    user_prompt = f"Product details: {product_notes if product_notes else 'Inspect the provided product image and extract features automatically.'}"
    messages = [{"role": "system", "content": system_prompt}]
    
    user_msg = {"role": "user", "content": user_prompt}
    if image_bytes:
        user_msg["images"] = [image_bytes]
    messages.append(user_msg)

    try:
        response = ollama.chat(
            model=model_name,
            messages=messages,
            format="json",
            options={"temperature": 0.25},
        )
        return json.loads(response["message"]["content"])
    except Exception as e:
        st.error(f"Inference error: {str(e)}")
        return None

st.set_page_config(page_title="CatalogCraft AI", page_icon="🛍️", layout="wide")

st.title("🛍️ CatalogCraft AI")
st.caption("Local, Zero-Token-Cost Autonomous E-Commerce Engine for Independent Sellers")

# Sidebar
with st.sidebar:
    st.header("⚙️ Settings")
    selected_model = st.selectbox("Local Open-Weight Model", ["llama3.2-vision", "llama3.2"])
    platform = st.selectbox("Target Platform", list(PLATFORM_PROMPTS.keys()))
    language = st.selectbox("Language", ["English", "Hindi"])
    target_audience = st.text_input("Target Audience", value="Value-conscious online buyers")
    
    st.markdown("---")
    st.markdown("🔒 **100% On-Device Compute**")
    st.markdown("💰 **Token Cost: ₹0 / $0**")

mode_tab1, mode_tab2 = st.tabs(["Single Product Generator", "📦 Bulk Batch Generator (Multi-Upload)"])

with mode_tab1:
    col1, col2 = st.columns([1, 1], gap="medium")
    
    with col1:
        st.subheader("Input Product")
        uploaded_file = st.file_uploader("Upload Product Image", type=["jpg", "png", "jpeg"], key="single_img")
        img_bytes = None
        if uploaded_file:
            img = Image.open(uploaded_file)
            st.image(img, use_container_width=True)
            img_bytes = prepare_image_bytes(img) 

        notes = st.text_area("Product Specs / Raw Notes", placeholder="e.g. Wireless noise cancelling earbuds, 40hr battery, IPX5 waterproof...", height=120)
        btn_single = st.button("Generate Listing", type="primary", use_container_width=True)

    with col2:
        st.subheader("Optimized Listing")
        if btn_single:
            if not uploaded_file and not notes.strip():
                st.warning("Please provide an image or rough notes.")
            else:
                with st.spinner("Generating locally via Ollama..."):
                    res = generate_listing(img_bytes, notes, platform, target_audience, language, selected_model)
                    if res:
                        st.session_state["single_res"] = res

        if "single_res" in st.session_state:
            res = st.session_state["single_res"]
            st.markdown(f"### **{res.get('title', '')}**")
            
            st.markdown("#### **Key Bullets:**")
            for b in res.get("bullet_points", []):
                st.markdown(f"- {b}")
                
            st.info(f"💡 **Pricing Strategy:** {res.get('suggested_price_strategy', 'N/A')}")
            
            with st.expander("SEO Meta & Tags"):
                st.write(f"**Meta Description:** {res.get('meta_description', '')}")
                st.write("**Tags:** " + ", ".join([f"`{k}`" for k in res.get("seo_keywords", [])]))

            # Single CSV Download
            csv_data = pd.DataFrame([{
                "Title": res.get("title", ""),
                "Platform": platform,
                "Bullets": "\n".join(res.get("bullet_points", [])),
                "Keywords": ", ".join(res.get("seo_keywords", [])),
                "Meta": res.get("meta_description", ""),
                "HTML": res.get("long_description_html", "")
            }]).to_csv(index=False).encode('utf-8')
            
            st.download_button("📥 Download Listing (CSV)", data=csv_data, file_name="listing.csv", mime="text/csv")

with mode_tab2:
    st.subheader("Process Multiple Items in One Go")
    st.caption("Upload multiple product images. CatalogCraft will process each item sequentially and output a master CSV.")

    batch_files = st.file_uploader("Upload Product Photos", type=["jpg", "png", "jpeg"], accept_multiple_files=True, key="bulk_imgs")
    
    if batch_files:
        st.write(f"Selected **{len(batch_files)}** items.")
        if st.button("🚀 Run Batch Processing", type="primary"):
            results_list = []
            progress_bar = st.progress(0)
            
            for idx, file in enumerate(batch_files):
                img = Image.open(file)
                item_bytes = prepare_image_bytes(img) 

                item_res = generate_listing(
                    image_bytes=item_bytes,
                    product_notes=f"Filename: {file.name}",
                    target_platform=platform,
                    target_audience=target_audience,
                    language=language,
                    model_name=selected_model
                )

                if item_res:
                    results_list.append({
                        "File Name": file.name,
                        "Title": item_res.get("title", ""),
                        "Bullets": " | ".join(item_res.get("bullet_points", [])),
                        "Keywords": ", ".join(item_res.get("seo_keywords", [])),
                        "Meta Description": item_res.get("meta_description", ""),
                        "Price Strategy": item_res.get("suggested_price_strategy", "")
                    })
                
                progress_bar.progress((idx + 1) / len(batch_files))

            if results_list:
                df_batch = pd.DataFrame(results_list)
                st.success("Batch processing complete!")
                st.dataframe(df_batch, use_container_width=True)

                master_csv = df_batch.to_csv(index=False).encode('utf-8')
                st.download_button(
                    "📥 Download Master Batch Catalog (CSV)",
                    data=master_csv,
                    file_name="master_catalog.csv",
                    mime="text/csv",
                    use_container_width=True
                )