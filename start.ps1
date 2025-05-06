# Start the backend
cd calendar-app-backend
uvicorn main:app --reload

# Start the frontend
cd ../calendar-app-frontend
npx expo start
