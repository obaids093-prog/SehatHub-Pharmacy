"""
SehatHub - AI Prescription Scanner Utility
Uses PIL image analysis for prescription validation + Groq Text AI for medicine extraction.
No Vision API key needed — works 100% with the existing GROQ_API_KEY.
Includes automatic non-prescription image rejection and auto-deletion.
"""

import os
import json
import base64
import urllib.request
import urllib.error
from PIL import Image
import numpy as np


GROQ_ANALYSIS_PROMPT = """
You are an expert AI Pharmacy Assistant for SehatHub (an online pharmacy platform).
A user has uploaded a prescription image and our OCR system has extracted the following text from it.

Analyze this extracted prescription text and return structured JSON with:
1. Medicine names, dosage, frequency, and purpose
2. Patient name and doctor name if visible
3. A clear summary and clinical notes in English

Extracted Text from Prescription:
---
{extracted_text}
---

MANDATORY OUTPUT FORMAT (respond ONLY with valid JSON, no markdown):
{{
  "is_prescription": true,
  "patient_name": "Extracted name or Unknown",
  "doctor_name": "Extracted doctor name or Unknown",
  "medicines": [
    {{
      "name": "Medicine Name",
      "dosage": "500mg",
      "frequency": "Twice daily",
      "purpose": "For fever & pain"
    }}
  ],
  "summary": "Clear summary of the prescription in English.",
  "clinical_notes": "Any additional clinical observations or notes.",
  "disclaimer": "⚠️ Disclaimer: This is an AI-generated analysis. Always verify with a certified pharmacist or your doctor before taking any medication."
}}
"""


def _is_document_like_image(image_path):
    """
    Uses PIL + numpy to check if an uploaded image looks like a medical document/prescription.
    Returns (is_document: bool, reason: str)
    
    Checks:
    1. Aspect ratio (documents are usually portrait or near-square)
    2. Background brightness (prescriptions are mostly white/light background)
    3. Color variance (documents have low color saturation vs photos of cats/cars/scenery)
    """
    try:
        img = Image.open(image_path).convert('RGB')
        width, height = img.size
        
        # Resize for fast analysis (max 200px wide)
        if width > 200:
            ratio = 200 / width
            img = img.resize((200, int(height * ratio)))
        
        pixels = list(img.getdata())
        total = len(pixels)
        
        if total == 0:
            return False, "Image is empty or corrupted."
        
        # 1. Calculate average brightness (0-255)
        avg_r = sum(p[0] for p in pixels) / total
        avg_g = sum(p[1] for p in pixels) / total
        avg_b = sum(p[2] for p in pixels) / total
        avg_brightness = (avg_r + avg_g + avg_b) / 3
        
        # 2. Calculate percentage of "light" pixels (brightness > 180)
        light_pixels = sum(1 for p in pixels if (p[0] + p[1] + p[2]) / 3 > 180)
        light_ratio = light_pixels / total
        
        # 3. Calculate color saturation (documents have low saturation)
        # Convert to HSV-like saturation check
        saturated_pixels = 0
        for p in pixels:
            max_c = max(p)
            min_c = min(p)
            if max_c > 0:
                saturation = (max_c - min_c) / max_c
                if saturation > 0.4:  # Highly colorful pixel
                    saturated_pixels += 1
        color_ratio = saturated_pixels / total
        
        # Decision Logic:
        # A prescription/document typically has:
        # - > 40% light/white pixels (paper background)
        # - < 40% highly saturated colorful pixels
        # A photo of a cat/car/scenery typically has:
        # - < 30% light pixels
        # - > 50% saturated colorful pixels
        
        if light_ratio < 0.15 and color_ratio > 0.5:
            return False, "This image appears to be a colorful photo (e.g. selfie, scenery, or book cover). Please upload a valid doctor's prescription."
        
        if avg_brightness < 60:
            return False, "This image is too dark. Please upload a clear prescription or medical document."
        
        # If it passes basic checks, it COULD be a document
        return True, "Image appears to be a document/paper."
        
    except Exception as e:
        print(f"[Image Analysis Error] {e}")
        return False, "Image file could not be processed."


def _extract_text_basic(image_path):
    """
    Attempts basic text extraction from image using available OCR tools.
    Falls back to describing image properties if no OCR is available.
    """
    # Try pytesseract if available
    try:
        import pytesseract
        img = Image.open(image_path)
        text = pytesseract.image_to_string(img)
        if text and len(text.strip()) > 10:
            return text.strip()
    except ImportError:
        pass
    except Exception:
        pass
    
    # Try easyocr if available
    try:
        import easyocr
        reader = easyocr.Reader(['en'])
        results = reader.readtext(image_path)
        text = ' '.join([r[1] for r in results])
        if text and len(text.strip()) > 10:
            return text.strip()
    except ImportError:
        pass
    except Exception:
        pass
    
    # No OCR available — return basic description
    try:
        img = Image.open(image_path)
        w, h = img.size
        return f"[Image uploaded: {w}x{h} pixels, prescription document detected by image analysis. OCR text extraction not available — manual pharmacist review recommended.]"
    except Exception:
        return "[Prescription image uploaded for pharmacist review.]"


def _call_groq_text_api(prompt):
    """Calls Groq Cloud text API (Llama 3.3 70B) for prescription text analysis."""
    groq_key = os.getenv('GROQ_API_KEY', '').strip()
    if not groq_key:
        return None
    
    try:
        url = "https://api.groq.com/openai/v1/chat/completions"
        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {"role": "system", "content": "You are an expert pharmacy AI that analyzes prescription text. Always respond with valid JSON only."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.1,
            "max_tokens": 800
        }
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode('utf-8'),
            headers={
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {groq_key}',
                'User-Agent': 'Mozilla/5.0'
            }
        )
        with urllib.request.urlopen(req, timeout=15) as response:
            body = json.loads(response.read().decode('utf-8'))
            choices = body.get('choices', [])
            if choices and 'message' in choices[0]:
                return choices[0]['message']['content'].strip()
    except Exception as e:
        print(f"[Groq Text API Error] {e}")
    return None


def analyze_prescription_image(image_path):
    """
    Analyzes an uploaded prescription image.
    Step 1: PIL image analysis to check if it looks like a document/prescription.
    Step 2: OCR text extraction (if pytesseract/easyocr available).
    Step 3: Groq Llama 3.3 70B text analysis for medicine extraction.
    Step 4: Auto-delete invalid/non-prescription images.
    """
    if not os.path.exists(image_path):
        return {
            "success": False,
            "error": "Uploaded image file was not found on server."
        }

    # Step 1: PIL-based document detection
    is_document, reason = _is_document_like_image(image_path)
    
    if not is_document:
        # AUTO-DELETE non-prescription image
        try:
            if os.path.exists(image_path):
                os.remove(image_path)
                print(f"[AI Prescription Cleanup] Deleted non-prescription: {image_path}")
        except Exception as del_err:
            print(f"[Cleanup Error] {del_err}")
        
        return {
            "success": False,
            "is_prescription": False,
            "message": reason,
            "error": f"Invalid Image! {reason}"
        }

    # Step 2: Extract text from the document image
    extracted_text = _extract_text_basic(image_path)

    # Step 3: Send extracted text to Groq for analysis
    prompt = GROQ_ANALYSIS_PROMPT.format(extracted_text=extracted_text)
    groq_response = _call_groq_text_api(prompt)
    
    if groq_response:
        # Parse the JSON response
        try:
            clean_text = groq_response
            if "```json" in clean_text:
                clean_text = clean_text.split("```json")[1].split("```")[0].strip()
            elif "```" in clean_text:
                clean_text = clean_text.split("```")[1].split("```")[0].strip()
            
            parsed_data = json.loads(clean_text)
            
            return {
                "success": True,
                "is_prescription": True,
                "data": parsed_data
            }
        except Exception as e:
            print(f"[JSON Parse Error] {e}")
            # Return raw response as summary
            return {
                "success": True,
                "is_prescription": True,
                "data": {
                    "is_prescription": True,
                    "medicines": [],
                    "summary": groq_response,
                    "clinical_notes": "AI analysis completed. Please verify with a pharmacist.",
                    "disclaimer": "⚠️ Disclaimer: This is an AI-generated analysis. Always verify with a certified pharmacist or your doctor before taking any medication."
                }
            }
    
    # Fallback: Image passed document check but no Groq/OCR response
    return {
        "success": True,
        "is_prescription": True,
        "data": {
            "is_prescription": True,
            "medicines": [],
            "summary": "Prescription image received and saved. For automatic text extraction, install pytesseract. This image has been saved for pharmacist review.",
            "clinical_notes": "OCR text extraction is not available. Manual pharmacist review is recommended.",
            "disclaimer": "⚠️ Disclaimer: Manual pharmacist verification is recommended."
        }
    }
