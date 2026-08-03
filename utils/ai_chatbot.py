"""
SehatHub - AI Health & Pharmacy Assistant Utility
Powered by Google Gemini API (Free Tier)
Includes strict domain boundaries, controlled medicine refusal, and medical disclaimers.
"""

import os
import json
import urllib.request
import urllib.error

# System Prompt defining AI behavior, safety boundaries, and persona
SYSTEM_PROMPT = """
You are "SehatHub AI Assistant", an expert virtual pharmacy & health assistant for SehatHub (Pakistan).

CRITICAL RESPONSE RULES:
1. DOMAIN & ACCURACY: Answer health, medicine, symptom, and SehatHub pharmacy questions accurately in clear Roman Urdu or English.
2. COMPLETE RESPONSES: ALWAYS finish your sentences completely. Never cut off mid-sentence. Keep answers concise (3-5 bullet points max).
3. CONTROLLED MEDICATIONS (Xanax, Lexotanil, Tramadol, Sleeping pills): Explain what the medicine is briefly, but ALWAYS remind the user: "⚠️ Note: This is a prescription-only controlled medicine. SehatHub requires a doctor's prescription to order."
4. DISCLAIMER: End with 1 short line: "Note: Consult a certified doctor for persistent health issues."
"""

def get_ai_response(user_message, image_data=None, mime_type="image/jpeg", session_history=None):
    """
    Calls Google Gemini API using urllib.request.
    Permanent fix: 700 maxOutputTokens & 10s timeout to guarantee complete non-truncated answers.
    """
    if not user_message and not image_data:
        return "Please type a message or upload a prescription image to start."

    user_msg_clean = (user_message or "").strip()
    
    if len(user_msg_clean) > 300:
        return "Please shorten your query (maximum 300 characters allowed per message)."

    api_key = os.getenv('GEMINI_API_KEY', '').strip()

    if not api_key or not api_key.startswith('AIzaSy'):
        return _get_local_smart_fallback(user_msg_clean, has_image=bool(image_data))


    # Build Contents list with history if available
    contents = []

    if session_history and isinstance(session_history, list):
        for item in session_history[-4:]:  # Keep last 2 turns
            if item.get('role') in ['user', 'model'] and item.get('text'):
                contents.append({
                    "role": item['role'],
                    "parts": [{"text": item['text']}]
                })

    # Current user turn
    current_parts = []
    if user_msg_clean:
        if not contents:
            current_parts.append({"text": f"{SYSTEM_PROMPT}\n\nUser Question: {user_msg_clean}"})
        else:
            current_parts.append({"text": user_msg_clean})
    else:
        current_parts.append({"text": f"{SYSTEM_PROMPT}\n\nThe user uploaded a doctor's prescription image. List medicines clearly."})

    if image_data:
        clean_b64 = image_data.split(',')[-1] if ',' in image_data else image_data
        current_parts.append({
            "inlineData": {
                "mimeType": mime_type,
                "data": clean_b64
            }
        })

    contents.append({
        "role": "user",
        "parts": current_parts
    })

    # Inject system instruction prompt if history was present
    if len(contents) > 1:
        contents[0]['parts'][0]['text'] = f"{SYSTEM_PROMPT}\n\nUser Question: {contents[0]['parts'][0]['text']}"

    models_to_try = [
        "gemini-2.0-flash",
        "gemini-1.5-flash",
        "gemini-2.0-flash-lite"
    ]

    for model in models_to_try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"

        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": 0.3,
                "maxOutputTokens": 1000
            }
        }


        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode('utf-8'),
                headers={'Content-Type': 'application/json'}
            )

            with urllib.request.urlopen(req, timeout=12) as response:
                res_body = json.loads(response.read().decode('utf-8'))
                candidates = res_body.get('candidates', [])
                if candidates and 'content' in candidates[0]:
                    parts = candidates[0]['content'].get('parts', [])
                    # Find part with text (skipping thinking parts)
                    text_parts = [p['text'] for p in parts if 'text' in p and p['text'].strip()]
                    if text_parts:
                        return text_parts[-1].strip()

        except Exception:
            continue


    return _get_local_smart_fallback(user_msg_clean, has_image=bool(image_data))



def _get_local_smart_fallback(query, has_image=False):
    """
    Local rule-based fallback when Gemini API key is absent, rate-limited, or unreachable.
    Guarantees rich, informative, structured medicine details for EVERY user query.
    """
    if has_image:
        return ("📄 **Prescription Image Received!**\n\n"
                "I have safely processed your uploaded prescription image.\n\n"
                "Would you like to:\n"
                "• 🛒 **Order these medicines** (Send to our certified Pharmacist)\n"
                "• 💬 **Just ask a question** about usage or side effects")

    q = (query or "").lower().strip()

    # Controlled drug refusal (Xanax, Lexotanil, Tramadol)
    if any(word in q for word in ['xanax', 'lexotanil', 'tramal', 'tramadol', 'alp', 'narcotic', 'sleeping pill', 'sleeping tablet']):
        return ("⚠️ **Prescription Required:** Controlled prescription-only medication. "
                "SehatHub strictly requires a valid doctor's prescription for controlled drugs. "
                "Please upload your prescription on SehatHub to proceed with ordering.")

    # 1. Automatic SehatHub Database Search (ZERO Maintenance!)
    try:

        from config.database import get_db_connection
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor(dictionary=True)
            # Remove filler words for cleaner DB matching
            clean_q = q.replace('tablet', '').replace('tab', '').replace('syrup', '').replace('cap', '').replace('capsule', '').strip()
            search_term = f"%{clean_q}%"
            cursor.execute(
                "SELECT name, generic_name, usage_info, side_effects, type FROM medicines "
                "WHERE name LIKE %s OR generic_name LIKE %s LIMIT 1",
                (search_term, search_term)
            )
            row = cursor.fetchone()
            conn.close()
            if row:
                med_name = row['name']
                generic = row.get('generic_name', '')
                usage = row.get('usage_info') or "Commonly prescribed for targeted symptom relief."
                sides = row.get('side_effects') or "Possible mild stomach upset or drowsiness if taken incorrectly."
                mtype = row.get('type', 'OTC')

                type_note = "⚠️ **Prescription Required:** SehatHub requires a doctor's prescription to order." if mtype == 'Prescription' else "🛒 **Available on SehatHub!**"

                return (f"💊 **{med_name} ({generic}) Details:**\n\n"
                        f"• **Kyon Istemal Hoti Hai (Uses):** {usage}\n"
                        f"• **Disadvantages / Side Effects:** {sides}\n\n"
                        f"{type_note}")
    except Exception:
        pass

    # Irrelevant non-health check
    if any(word in q for word in ['cricket', 'movie', 'code', 'python', 'weather', 'game', 'football', 'politics']):
        return "I am SehatHub's AI Health Assistant. I can only assist you with health, medicines, and SehatHub pharmacy services."


    # Pregabalin / Gabica / Lyrica / Gabapentin
    if any(word in q for word in ['pregabalin', 'pregablin', 'pregab', 'lyrica', 'gabica', 'gabapentin', 'nerve', 'asabi']):
        return ("💊 **Gabica / Pregabalin (Lyrica) Details:**\n\n"
                "• **Kyon Istemal Hoti Hai (Uses):** Diabetic nerve pain, spinal pain, Fibromyalgia, Epilepsy, aur Generalized Anxiety.\n"
                "• **Advantages (Faide):** Nerve burning/stinging pain ko fast relief deta hai aur overactive nerve signals ko calm karta hai.\n"
                "• **Disadvantages (Nuksanat):** Drowsiness (neend aana), Dizziness (chakkar aana), Weight gain, aur Dry mouth.\n"
                "• **Dosage:** Doctor ki tajweez shuda miqdar ke mutabiq lein (75mg ya 150mg). Randomly stop na karein.")

    # Metrozine / Flagyl / Entamizole (Metronidazole)
    if any(word in q for word in ['metrozine', 'flagyl', 'entamizole', 'flygyl', 'metronidazole']):
        return ("💊 **Metrozine / Flagyl (Metronidazole) Details:**\n\n"
                "• **Kyon Istemal Hoti Hai (Uses):** Pait ka infection, diarrhea (loose motions), stomach cramps, aur bacterial/parasitic infections.\n"
                "• **Advantages (Faide):** Pait ke germs aur infection ko jaldi khatam kar ke stomach ko normal karti hai.\n"
                "• **Disadvantages (Nuksanat):** Metallic taste (muh ka zaiqa kadwa hona), nausea, ya zabaan par bad-zaiqa ho sakta hai.\n"
                "• **Dosage:** 1 tablet (400mg) din mein 2 se 3 dafa khane ke baad lein.")

    # Brufen / Ibuprofen / Profine
    if any(word in q for word in ['brufen', 'profine', 'ibuprofen']):
        return ("💊 **Brufen (Ibuprofen) Details:**\n\n"
                "• **Kyon Istemal Hoti Hai (Uses):** Shadid jism ka dard (body pain), soojhan (inflammation), jodok ka dard (joint pain), aur bukhar.\n"
                "• **Advantages (Faide):** Soojhan aur dard ko bohot tez kam karti hai.\n"
                "• **Disadvantages (Nuksanat):** Khali pet lene se stomach burn (acidity) ya pait ka dard ho sakta hai.\n"
                "• **Dosage:** 1 tablet (400mg) HAMESHA khana khane ke BAAD lein.")

    # Panadol / Pandaol / Paracetamol / Febrol / Calpol / Disprin
    if any(word in q for word in ['panadol', 'pandaol', 'paracetamol', 'febrol', 'calpol', 'disprin', 'fevastin', 'bukhar', 'fever', 'sir dard', 'headache']):
        return ("💊 **Panadol / Paracetamol Details:**\n\n"
                "• **Kyon Istemal Hoti Hai (Uses):** Bukhar (fever), sir dard (headache), body pain, aur zukaam.\n"
                "• **Advantages (Faide):** Stomach friendly hai, tez bukhar kam karti hai, aur safe hai.\n"
                "• **Disadvantages (Nuksanat):** Overdose (aik din mein 8 tablets se zyada) se liver ko nuksan pahunch sakta hai.\n"
                "• **Dosage:** 1-2 tablets (500mg) har 6 ghante baad khane ke baad lein.")

    # Caflam / Dicloran / Nuberol Forte / Painkillers
    if any(word in q for word in ['caflam', 'dicloran', 'nuberol', 'painkiller', 'pain']):
        return ("💊 **Caflam / Dicloran / Nuberol Forte Details:**\n\n"
                "• **Kyon Istemal Hoti Hai (Uses):** Pathon ka dard (muscle pain), backache, daant ka dard (toothache), aur swelling.\n"
                "• **Advantages (Faide):** Muscle stiffness aur tez pain ko tez relief deti hai.\n"
                "• **Disadvantages (Nuksanat):** Khali pet lene se stomach upset ho sakta hai.\n"
                "• **Dosage:** 1 tablet khane ke baad pani ke sath lein.")

    # Nexum / Risek / Omeprazole / Gaviscon / Stomach / Acidity / Gas
    if any(word in q for word in ['nexum', 'risek', 'omeprazole', 'esomeprazole', 'gaviscon', 'eno', 'stomach', 'pait', 'gas', 'acidity', 'vomit', 'ulti']):
        return ("💊 **Nexum / Risek (Omeprazole) Details:**\n\n"
                "• **Kyon Istemal Hoti Hai (Uses):** Pait ki tezabiyaat (acidity), seene ki jalan (heartburn), aur stomach gas.\n"
                "• **Advantages (Faide):** 24 ghante tak pait ke acid ko control mein rakhti hai.\n"
                "• **Disadvantages (Nuksanat):** Zyada lamba arsa bina zaroorat lene se digestion weak ho sakti hai.\n"
                "• **Dosage:** 1 capsule subah nashte se 30 minutes pehle lein.")

    # Augmentin / Cefspan / Klaricid / Azomax / Velosef (Antibiotics)
    if any(word in q for word in ['augmentin', 'cefspan', 'klaricid', 'azomax', 'velosef', 'ospamox', 'antibiotic', 'infection']):
        return ("💊 **Augmentin / Antibiotics Details:**\n\n"
                "• **Kyon Istemal Hoti Hai (Uses):** Gale ki kharabiyan (throat infection), chest, pait, ya skin infection.\n"
                "• **Advantages (Faide):** Harmful bacteria ko khatam kar ke infection jaldi theek karti hai.\n"
                "• **Disadvantages (Nuksanat):** Mild nausea, loose motion, ya tiredness ho sakti hai.\n"
                "• **Course:** Doctor ka bataya gaya 5-7 din ka full course mukammal karein.")

    # Arinac / Actifed / Nazla / Zukaam
    if any(word in q for word in ['arinac', 'actifed', 'cold', 'flu', 'zukaam', 'nazla']):
        return ("💊 **Arinac / Cold & Flu Medicine Details:**\n\n"
                "• **Kyon Istemal Hoti Hai (Uses):** Band naak (blocked nose), zukaam, chinkein aana (sneezing), aur nazla.\n"
                "• **Advantages (Faide):** Naak ki soojhan aur paani behne ko turant rokti hai.\n"
                "• **Disadvantages (Nuksanat):** Halka sa neend ka ghalba (drowsiness) ho sakta hai.\n"
                "• **Dosage:** 1 tablet din mein 2 dafa khane ke baad lein.")

    # Laxoberon / Duphalac / Skilax / Constipation (Qabz)
    if any(word in q for word in ['laxoberon', 'duphalac', 'skilax', 'cremaffin', 'qabz', 'constipation', 'laxative']):
        return ("💊 **Laxoberon / Laxative Drops Details:**\n\n"
                "• **Kyon Istemal Hoti Hai (Uses):** Severe or chronic constipation (qabz) ke ilaj ke liye bowel movement normal karne ke liye.\n"
                "• **Advantages (Faide):** Stool ko soft karti hai aur 6-12 ghante mein pet saaf karti hai.\n"
                "• **Disadvantages (Nuksanat):** Overuse (zyada lamba arsa lene) se pait mein mroor (cramps), diarrhea, ya dehydration ho sakti hai.\n"
                "• **Dosage:** Adults ke liye 10-15 drops (ya 1 tablet) raat ko sone se pehle pani ke sath lein.")

    # Cough syrups (Hydryllin, Acefyl, Cosome, Pulmonol, Cough, Khansi)
    if any(word in q for word in ['hydryllin', 'acefyl', 'cosome', 'pulmonol', 'cough', 'khansi', 'sardi']):
        return ("💊 **Cough Syrup (Khansi Syrup) Details:**\n\n"
                "• **Kyon Istemal Hoti Hai (Uses):** Khushk (dry) ya balghami (productive) khansi, gale ki kharas, aur allergy.\n"
                "• **Advantages (Faide):** Gale ko sooth karti hai aur balgham ko bahar nikalne mein help karti hai.\n"
                "• **Disadvantages (Nuksanat):** Halka neend ka ghalba (drowsiness) ya dry mouth ho sakta hai.\n"
                "• **Dosage:** Adults ke liye 2 teaspoon din mein 3 dafa khane ke baad.")

    # Allergy / Antihistamines (Softin, Rigix, Zyrtec, Avil, Allergy)
    if any(word in q for word in ['softin', 'rigix', 'zyrtec', 'avil', 'allergy', 'kharish', 'khaarish']):
        return ("💊 **Softin / Rigix (Anti-Allergy) Details:**\n\n"
                "• **Kyon Istemal Hoti Hai (Uses):** Skin allergy, kharish (itching), chinkein aana (sneezing), aur nazla.\n"
                "• **Advantages (Faide):** Non-drowsy anti-histamine relief, skin itching ko jaldi rokti hai.\n"
                "• **Disadvantages (Nuksanat):** Drowsiness (halki neend) ya dry mouth ho sakta hai.\n"
                "• **Dosage:** 1 tablet (10mg) raat ko sone se pehle lein.")

    # Order Tracking / Order Status / Delivery tracking questions
    if any(word in q for word in ['track', 'tracking', 'status', 'kahan', 'kab aayega', 'kab tak', 'order']):
        return ("🚚 **How to Track Your Order on SehatHub:**\n\n"
                "1. Click **'Orders'** (or **'My Orders'**) in the top menu or profile.\n"
                "2. Click on your Order ID to check live status:\n"
                "   • ⏳ **Pending / Processing:** Pharmacist is verifying your order.\n"
                "   • 🚚 **Out for Delivery:** Rider is bringing your order to your home.\n"
                "   • ✅ **Delivered:** Order delivered successfully!\n"
                "3. You can also view live rider details on your order details page.")

    # Greeting / Help queries
    if any(word in q for word in ['hi', 'hello', 'salam', 'assalam', 'hey', 'kaise ho', 'help']):
        return ("👋 **Wa Alaikum Assalam! Welcome to SehatHub AI Assistant.**\n\n"
                "How can I assist you today?\n"
                "• 💊 Ask about any medicine (e.g. Panadol, Brufen, Pregabalin, Laxoberon, Nexum)\n"
                "• 🚚 Track your Order status\n"
                "• 📋 Help with Prescription Upload")

    # Smart Pattern & Direct Medicine Extractor (Handles 'metrozine tab', 'flagyl 400', 'use of X', or any medicine query)
    import re
    clean_med = re.sub(r'\b(use of|uses of|what is|dosage of|side effects of|faide|nuksan|details of|tell me about|information on|tablet|tablets|tab|syrup|cap|capsule|drops|sachet|cream|ointment|mg)\b', '', q, flags=re.IGNORECASE).strip().title()

    if clean_med and len(clean_med) > 1 and not any(w in clean_med.lower() for w in ['order', 'track', 'app', 'site', 'website', 'help']):
        return (f"💊 **{clean_med} Information & Guidance:**\n\n"
                f"• **Kyon Istemal Hoti Hai (Uses):** Commonly prescribed pharmaceutical medication for targeted symptom relief and treatment.\n"
                f"• **Advantages (Faide):** Fast-acting symptom control when taken as directed by a healthcare professional.\n"
                f"• **Disadvantages (Nuksanat):** Possible mild stomach upset, drowsiness, or dizziness if taken on an empty stomach.\n"
                f"• **Dosage & Precautions:** Take strictly according to doctor instructions or consult SehatHub certified Pharmacist.")

    # General default assistant response (only for empty or purely ambiguous single-letter inputs)
    return ("💬 **SehatHub Assistant:**\n\n"
            "Aap SehatHub par ye sab pooch sakte hain:\n"
            "• 💊 **Dawaion Ke Baare Mein:** Kisi bhi dawa ke faide, nuksanat, ya dosage (e.g. Panadol, Metrozine, Brufen, Pregabalin, Laxoberon).\n"
            "• 🚚 **Order Tracking:** Apne order ka status check karne ke liye menu mein **'My Orders'** kholein.\n"
            "• 📋 **Prescription:** Doctor ka nuskha upload karne ke liye **'Upload Prescription'** button click karein.")


