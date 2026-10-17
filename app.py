import json
from io import BytesIO
import ollama
import pandas as pd
import streamlit as st
from PIL import Image
from pydantic import BaseModel, Field


class ProductListing(BaseModel):
    title: str = Field(description="Marketplace-specific high-converting product title")
    bullet_points: list[str] = Field(description="5 targeted bullet points")
    seo_keywords: list[str] = Field(description="Search tags and keywords")
    meta_description: str = Field(description="150-160 character meta description")
    suggested_price_strategy: str = Field(description="Concrete price recommendation with currency (e.g. ₹499–₹699 or $12–$18) and a one-line rationale")
    long_description_html: str = Field(description="Clean HTML description with formatting")


PLATFORM_PROMPTS = {
    "Amazon": "Follow strict Amazon guidelines: Title under 200 chars including brand/material/size. Exactly 5 bullets, each starting with a capitalized benefit header (e.g., 'DURABLE BUILD: ...'). Dense SEO keywords.",
    "Etsy": "Adopt a warm, artisanal, story-focused tone highlighting handcrafted value and gifting potential. Produce 13 specific Etsy-friendly tags under 20 characters.",
    "Shopify": "Write engaging D2C brand copy with conversion-oriented hook, clean feature benefits, and meta description ready for Google indexing.",
    "Meesho": "Focus on high value-for-money, fabric/material clarity, daily-use practicality, and simple conversational terms."
}


def resize_image(img, max_size=512):
    img = img.convert("RGB")
    img.thumbnail((max_size, max_size), Image.LANCZOS)
    buf = BytesIO()
    img.save(buf, format="JPEG", quality=85, optimize=True)
    return buf.getvalue()


def describe_image_moondream(image_bytes):
    """Step 1: Use moondream ONLY for vision — describe what's in the image."""
    if not image_bytes:
        return None
    try:
        resp = ollama.chat(
            model="moondream",
            messages=[{
                "role": "user",
                "content": "Describe this product in detail: its type, color, material, design, features, and any visible text or branding. Be thorough.",
                "images": [image_bytes]  
            }]
        )
        return resp.message.content
    except Exception as e:
        st.warning(f"⚠️ Moondream image description failed: {e}")
        return None


def generate_listing(image_bytes, notes, platform, audience, language, text_model="llama3.2"):
    """Step 2: Use a text LLM to generate the structured JSON listing."""
    platform_rule = PLATFORM_PROMPTS.get(platform, "Create an e-commerce listing.")

    context_parts = []
    if image_bytes:
        with st.spinner("🔍 Step 1/2: Moondream analyzing image..."):
            vision_desc = describe_image_moondream(image_bytes)
        if vision_desc:
            context_parts.append(f"Image Analysis: {vision_desc}")
    if notes.strip():
        context_parts.append(f"Seller Notes: {notes.strip()}")

    if not context_parts:
        st.warning("Please upload an image or add some notes.")
        return None

    product_context = "\n".join(context_parts)

    hindi_rule = ""
    if language == "Hindi":
        hindi_rule = """
CRITICAL HINDI LANGUAGE RULE: Write ALL text in pure Devanagari Hindi script. Do NOT use any English words or Latin characters anywhere in the output. Transliterate English terms into Hindi Devanagari (e.g., "mesh upper" → "मेश अपर", "running shoes" → "रनिंग शूज़", "breathable" → "ब्रेथेबल", "EVA sole" → "ईवीए सोल"). Every single word must be in Devanagari script. No mixing of English and Hindi."""

    system_prompt = f"""You are an expert e-commerce copywriter.
Platform: {platform}
Rule: {platform_rule}
Target Audience: {audience}
Output Language: {language}
{hindi_rule}

For 'suggested_price_strategy': Give the actual specific price range with correct currency symbol (use ₹ for Indian products, $ for US/global). Example format: ₹799–₹1299. Then add one short sentence explaining why. Do NOT copy examples, generate real numbers based on product type and quality.

Output ONLY raw JSON with this structure, no markdown, no explanation:
{{
  "title": "string",
  "bullet_points": ["string", "string", "string", "string", "string"],
  "seo_keywords": ["string", "string", "string"],
  "meta_description": "string",
  "suggested_price_strategy": "string",
  "long_description_html": "string"
}}"""

    try:
        with st.spinner(f"✍️ Step 2/2: {text_model} writing listing..."):
            resp = ollama.chat(
                model=text_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Create a listing for this product:\n\n{product_context}"}
                ],
                format="json",
                options={"temperature": 0.25}
            )
        return json.loads(resp.message.content)
    except Exception as e:
        st.error(f"Error generating listing: {e}")
        return None

st.set_page_config(page_title="CatalogCraft AI", page_icon="🛍️", layout="wide")
st.title("🛍️ CatalogCraft AI")
st.caption("Local, Zero-Token-Cost Autonomous E-Commerce Engine for Independent Sellers")

with st.sidebar:
    st.header("⚙️ Settings")
    st.markdown("🔭 **Vision:** `moondream`  \n📝 **Listing:** `llama3.2`")
    platform = st.selectbox("Platform", list(PLATFORM_PROMPTS.keys()))
    language = st.selectbox("Language", ["English", "Hindi"])
    audience = st.text_input("Target Audience", value="Value-conscious online buyers")
    st.markdown("---")
    st.markdown("🔒 **100% On-Device**  \n💰 **Cost: ₹0 / $0**")

tab1, tab2 = st.tabs(["Single Product", "📦 Bulk Batch"])
with tab1:
    col1, col2 = st.columns(2, gap="medium")

    with col1:
        st.subheader("Input")
        uploaded = st.file_uploader("Product Image", type=["jpg", "png", "jpeg"], key="single")
        img_bytes = None
        if uploaded:
            img = Image.open(uploaded)
            st.image(img, use_container_width=True)
            img_bytes = resize_image(img)

        notes = st.text_area("Notes / Specs", placeholder="e.g. Wireless earbuds, 40hr battery, IPX5...", height=120)
        generate = st.button("Generate Listing", type="primary", use_container_width=True)

    with col2:
        st.subheader("Output")
        if generate:
            if not uploaded and not notes.strip():
                st.warning("Please upload an image or add some notes.")
            else:
                result = generate_listing(img_bytes, notes, platform, audience, language)
                if result:
                    st.session_state["result"] = result

        if "result" in st.session_state:
            r = st.session_state["result"]
            st.markdown(f"### {r.get('title', '')}")

            st.markdown("**Bullet Points:**")
            for b in r.get("bullet_points", []):
                st.markdown(f"- {b}")

            st.info(f"💡 **Pricing:** {r.get('suggested_price_strategy', '')}")

            with st.expander("SEO & Meta"):
                st.write(f"**Meta:** {r.get('meta_description', '')}")
                st.write("**Tags:** " + ", ".join(f"`{k}`" for k in r.get("seo_keywords", [])))

            csv = pd.DataFrame([{
                "Title": r.get("title", ""),
                "Platform": platform,
                "Bullets": "\n".join(r.get("bullet_points", [])),
                "Keywords": ", ".join(r.get("seo_keywords", [])),
                "Meta": r.get("meta_description", ""),
                "HTML": r.get("long_description_html", "")
            }]).to_csv(index=False).encode()

            st.download_button("📥 Download CSV", data=csv, file_name="listing.csv", mime="text/csv")


with tab2:
    st.subheader("Bulk Processing")
    files = st.file_uploader("Upload Multiple Images", type=["jpg", "png", "jpeg"], accept_multiple_files=True, key="bulk")

    if files:
        st.write(f"{len(files)} items selected")
        if st.button("🚀 Run Batch", type="primary"):
            rows = []
            bar = st.progress(0)

            for i, f in enumerate(files):
                img = Image.open(f)
                res = generate_listing(resize_image(img), f"Filename: {f.name}", platform, audience, language)

                if res:
                    rows.append({
                        "File": f.name,
                        "Title": res.get("title", ""),
                        "Bullets": " | ".join(res.get("bullet_points", [])),
                        "Keywords": ", ".join(res.get("seo_keywords", [])),
                        "Meta": res.get("meta_description", ""),
                        "Price Strategy": res.get("suggested_price_strategy", "")
                    })

                bar.progress((i + 1) / len(files))

            if rows:
                df = pd.DataFrame(rows)
                st.success("Done!")
                st.dataframe(df, use_container_width=True)
                st.download_button("📥 Download Master CSV", data=df.to_csv(index=False).encode(), file_name="catalog.csv", mime="text/csv", use_container_width=True)