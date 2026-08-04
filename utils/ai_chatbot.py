"""
SehatHub - AI Health & Pharmacy Assistant Utility
Powered by Groq Cloud AI Engine (Llama 3.1 / 3.3)
Includes strict domain boundaries, controlled medicine refusal, and medical disclaimers.
"""


import os
import json
import urllib.request
import urllib.error

# System Prompt defining AI behavior, safety boundaries, and persona
SYSTEM_PROMPT = """
You are "SehatHub AI Support Assistant", a pharmacy & health information assistant for SehatHub (Pakistan's online pharmacy).

RESPONSE FORMAT (MANDATORY — follow this EXACT structure for medicine queries):
When user asks about ANY medicine, respond in this format:

💊 [Medicine Name] ([Generic Name]) Details:

• Uses: [2-3 specific medical conditions this medicine treats]
• Dosage: [Standard adult dosage with timing]
• Side Effects: [2-3 common side effects]
• Precautions: [1-2 key warnings]

Note: Consult a certified doctor for persistent health issues.

STRICT RULES:
1. ONLY answer health, medicine, symptom, disease, and SehatHub platform questions.
2. For non-health topics (sports, movies, politics, coding, games): Reply ONLY with "I am SehatHub's AI Health Assistant. I can only assist you with health, medicines, and SehatHub pharmacy services."
3. You do NOT place orders. For ordering guide: "SehatHub par medicine search karein aur cart mein add karein."
4. For controlled drugs (Xanax, Lexotanil, Tramadol): Add "⚠️ Prescription-only controlled medicine."
5. Keep answers SHORT (max 8-10 lines). DO NOT repeat sentences. DO NOT use filler text.
6. Use simple English or Roman Urdu matching user's language.
"""


def _call_groq_api(user_msg_clean, session_history=None):
    """
    Calls Groq Cloud API (Llama 3.3 70B primary, 8B fallback).
    Ultra-fast free AI response.
    """
    q_lower = user_msg_clean.lower()

    # Pre-filter for non-health/out-of-context topics
    non_health_words = ['cricket', 'psl', 'ipl', 'match', 'score', 'football', 'soccer', 'movie', 'cinema', 'film', 'song', 'music', 'python', 'java', 'programming', 'coding', 'weather', 'politics', 'election', 'game', 'pubg']
    if any(w in q_lower for w in non_health_words):
        return "I am SehatHub's AI Health Assistant. I can only assist you with health, medicines, and SehatHub pharmacy services."

    groq_key = os.getenv('GROQ_API_KEY', '').strip()
    if not groq_key or not groq_key.startswith('gsk_'):
        return None

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    if session_history and isinstance(session_history, list):
        for item in session_history[-4:]:
            if item.get('role') in ['user', 'assistant', 'model'] and item.get('text'):
                role = "assistant" if item['role'] in ['model', 'assistant'] else "user"
                messages.append({"role": role, "content": item['text']})

    messages.append({"role": "user", "content": user_msg_clean})

    # 70B first (smarter, accurate), 8B fallback (faster but lower quality)
    models = ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"]

    for model in models:
        try:
            url = "https://api.groq.com/openai/v1/chat/completions"
            payload = {
                "model": model,
                "messages": messages,
                "temperature": 0.2,
                "max_tokens": 600
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
            with urllib.request.urlopen(req, timeout=10) as response:
                body = json.loads(response.read().decode('utf-8'))
                choices = body.get('choices', [])
                if choices and 'message' in choices[0]:
                    text = choices[0]['message']['content'].strip()
                    # Quality filter: reject repetitive/garbage responses
                    if text and len(text) > 20:
                        words = text.split()
                        # Check for excessive word repetition (sign of bad output)
                        if len(words) > 10:
                            unique_ratio = len(set(words)) / len(words)
                            if unique_ratio < 0.25:
                                continue  # Skip this garbage response, try next model
                        return text
        except Exception:
            continue

    return None



def get_ai_response(user_message, image_data=None, mime_type="image/jpeg", session_history=None):
    """
    Primary AI Engine: Groq Cloud API (Llama 3.1 8B / Llama 3.3 70B).
    Fallback Engine: SehatHub Database + Local Health Assistant.
    """
    if not user_message and not image_data:
        return "Please type a message or upload a prescription image to start."

    user_msg_clean = (user_message or "").strip()

    if len(user_msg_clean) > 300:
        return "Please shorten your query (maximum 300 characters allowed per message)."

    # 1. Image Upload Handling
    if image_data:
        base_reply = _get_local_smart_fallback(user_msg_clean, has_image=True)
        if user_msg_clean:
            groq_reply = _call_groq_api(user_msg_clean, session_history)
            if groq_reply:
                return f"{groq_reply}\n\n---\n{base_reply}"
        return base_reply

    # 2. Try Groq Cloud API (Ultra-fast free Llama 3 AI)
    if user_msg_clean:
        groq_reply = _call_groq_api(user_msg_clean, session_history)
        if groq_reply:
            return groq_reply

    # 3. Local Database & Smart Health Assistant Fallback
    return _get_local_smart_fallback(user_msg_clean, has_image=False)





def _get_local_smart_fallback(query, has_image=False):
    """
    Local rule-based fallback when Gemini API key is absent, rate-limited, or unreachable.
    Guarantees rich, informative, structured medicine details for EVERY user query.
    """
    if has_image:
        base_reply = ("📷 **Medicine Photo / Document Received!**\n\n"
                      "Main aap ki uploaded image dekh chuka hoon.\n\n"
                      "💬 **Aap mujh se pooch sakte hain:**\n"
                      "• Medicine ka naam type karein aur main bataunga — Uses, Side Effects, Dosage & Availability on SehatHub!\n"
                      "• Ya koi bhi health related sawal poochein.\n\n"
                      "🛒 **Order Place Karne Ke Liye:** SehatHub homepage par jaayein aur medicine search karein ya 'Upload Prescription' option use karein.")
        return base_reply



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

    # Prescription upload instructions
    if any(word in q for word in ['nuskha', 'parchi']) or (any(word in q for word in ['prescription']) and any(word in q for word in ['upload', 'karo', 'kaise', 'how'])):
        return ("📋 **How to Upload Prescription on SehatHub:**\n\n"
                "1. Click **'Upload Prescription'** in the top navigation bar or on homepage.\n"
                "2. Select a clear picture or PDF of your doctor's prescription.\n"
                "3. Click **'Submit Prescription'**!\n"
                "4. Our certified pharmacist will verify your prescription and confirm your order within minutes.")

    # How to place order instructions
    if (any(word in q for word in ['order', 'buy', 'purchase']) and any(word in q for word in ['place', 'kaise', 'how', 'karein', 'khareedein', 'khareedna'])) or 'how to order' in q:
        return ("🛒 **How to Order Medicines on SehatHub:**\n\n"
                "1. **Search Medicine:** Type medicine name in the top search bar.\n"
                "2. **Add to Cart:** Click **'Add to Cart'**.\n"
                "3. **Upload Prescription:** For prescription medicines, attach doctor's note during checkout or via 'Upload Prescription' menu.\n"
                "4. **Checkout:** Enter delivery address & select Payment method (Cash on Delivery / Card).\n"
                "5. **Fast Delivery:** Order delivered to your doorstep within 30 to 60 minutes!")

    # Order Tracking / Order Status / Delivery tracking questions
    if any(word in q for word in ['track', 'tracking', 'status', 'kahan', 'kab aayega', 'kab tak']) or 'track order' in q:
        return ("🚚 **How to Track Your Order on SehatHub:**\n\n"
                "1. Click **'Orders'** (or **'My Orders'**) in the top menu or profile.\n"
                "2. Click on your Order ID to check live status:\n"
                "   • ⏳ **Pending / Processing:** Pharmacist is verifying your order.\n"
                "   • 🚚 **Out for Delivery:** Rider is bringing your order to your home.\n"
                "   • ✅ **Delivered:** Order delivered successfully!\n"
                "3. You can also view live rider details on your order details page.")

    # Greeting / Help queries
    if any(word in q for word in ['hi', 'hello', 'salam', 'assalam', 'hey', 'kaise ho', 'help']):
        return ("👋 **Wa Alaikum Assalam! Welcome to SehatHub AI Support Assistant.**\n\n"
                "How can I assist you today?\n"
                "• 💊 Ask about any medicine (e.g. Panadol, Brufen, Pregabalin, Laxoberon, Nexum)\n"
                "• 🚚 How to Track your Order status\n"
                "• 🛒 How to place an Order on SehatHub\n"
                "• 📋 How to Upload Prescription on SehatHub")


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


