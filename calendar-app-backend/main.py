from google import genai
import icalendar
import datetime
import os
import uuid
import re  # Import the re module

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel


# Define a Pydantic model for the request body
class UserInput(BaseModel):
    user_input: str
    time_zone: str = "America/New_York"  # Add time_zone field with a default value


app = FastAPI()

# Configure CORS
origins = [
    "http://localhost",
    "http://localhost:8081",  # Default Expo web port
    "exp://192.168.1.152:8081",  # Example Expo Go URL - replace with your actual Expo Go URL
    "http://127.0.0.1:8081",  # Another common local development address
    os.getenv(
        "FRONTEND_URL", "*"
    ),  # Allow requests from the frontend URL in production
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Vercel serves static files from the 'public' directory
# We don't need to mount static files in the FastAPI app for Vercel deployment

# Configure Gemini API
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY environment variable not set")
client = genai.Client(api_key=api_key)


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.post("/create-event")
async def create_calendar_event(user_input: UserInput):
    try:
        # Use Gemini to generate the schedule and .ics content
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        time_zone = user_input.time_zone  # Use the time zone from user input

        prompt = f"""
You are acting as a **flexible daily planner** for someone with an **irregular sleep schedule**. Your job is to create a complete and structured schedule for the day based on:

1. **Wake-up time** (user provides; often from the previous night)
2. **Current time** (assumed to be real-time in America/New_York unless otherwise stated)
3. **A list of tasks with estimated durations** (provided by the user, in hours or minutes)

---

### Your responsibilities:

- **Start the schedule at the wake-up time**
- **Fit all tasks into the current day**, without pushing any to the next day
- **Reorder tasks** for efficiency, if logical
- **Insert buffer breaks** (5–15 mins) after long or consecutive tasks
- **End with a suggested bedtime**, based on ~16–18 hours of total wakefulness
- Output two things:
  1. **Readable written schedule** with:
     - Start/end times
     - Task names or short labels
     - Breaks labeled clearly
  2. **Raw `.ics` file content** with correct formatting:
     - Use `BEGIN:VEVENT`, `DTSTART;TZID=America/New_York:YYYYMMDDTHHMMSS`, `DTEND;TZID=America/New_York:YYYYMMDDTHHMMSS`, and `SUMMARY:Task name`
     - Wrap all events in `BEGIN:VCALENDAR` and `END:VCALENDAR`
     - Use 24-hour time and assume all times are in America/New_York

---

### Example Input:
- Wake-up time: 2025-05-05 20:00
- Current time: 2025-05-06 06:00
- Tasks:
  - Research (1 hour)
  - Watch recording (5 hours)

---

### Example Written Output:
\`\`\`
08:00 PM – 09:00 PM: Research  
09:00 PM – 09:15 PM: Short Break  
09:15 PM – 02:15 AM: Watch recording  
02:15 AM – 02:30 AM: Short Break  
02:30 AM – 04:30 AM: Leisure or unwind  
Suggested bedtime: 12:00 PM  
\`\`\`

---

### Example `.ics` Output:
\`\`\`
BEGIN:VCALENDAR
VERSION:2.0
BEGIN:VEVENT
DTSTART;TZID=America/New_York:20250505T200000
DTEND;TZID=America/New_York:20250505T210000
SUMMARY:Research
END:VEVENT
BEGIN:VEVENT
DTSTART;TZID=America/New_York:20250505T211500
DTEND;TZID=America/New_York:20250506T021500
SUMMARY:Watch recording
END:VEVENT
END:VCALENDAR
\`\`\`

---

User Input: "{user_input.user_input}"  
Current Time: "{current_time}"  
Time Zone: "{time_zone}"
YOU MUST BE AWARE OF THE CURRENT TIME!!!! you should only schduel event that happens after the current time
"""

        print(f"Prompt sent to Gemini: {prompt}")
        response = client.models.generate_content(
            model="gemini-2.5-flash-preview-04-17", contents=prompt
        )
        print(f"Raw response from Gemini: {response.text}")
        response_text = response.text.strip()

        # Use regex to extract the .ics content from the Gemini response
        ics_match = re.search(
            r"BEGIN:VCALENDAR.*?END:VCALENDAR", response_text, re.DOTALL
        )

        if ics_match:
            ics_content = ics_match.group(0)
            print("Extracted .ics content.")
        else:
            # If no .ics content found, raise an error
            raise HTTPException(
                status_code=500,
                detail="Could not extract .ics content from Gemini response.",
            )

        # Generate unique filename
        filename = f"{uuid.uuid4()}.ics"
        # Save to the 'public' directory for Vercel static serving
        filepath = os.path.join("public", filename)

        # Create public directory if it doesn't exist
        if not os.path.exists("public"):
            os.makedirs("public")

        # Save to the public file directory
        with open(filepath, "wb") as f:
            f.write(ics_content.encode("utf-8"))  # Encode to bytes for writing

        # Construct the URL for Vercel static files
        # Vercel serves files from 'public' at the root path
        base_url = os.getenv("VERCEL_URL")
        if base_url:
            # Use HTTPS for production
            file_url = f"https://{base_url}/{filename}"
        else:
            # Fallback for local development (if needed)
            file_url = f"http://127.0.0.1:8000/public/{filename}"

        return JSONResponse(content={"ics_url": file_url})

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
