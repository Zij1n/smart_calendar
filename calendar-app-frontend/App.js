import React from "react";
import {
  StyleSheet,
  Text,
  View,
  TextInput,
  Button,
  Linking,
} from "react-native";
import axios from "axios";

// Backend URL
const backendUrl = "http://192.168.1.152:8000"; // Or your deployed backend URL

export default function App() {
  const [userInput, setUserInput] = React.useState("");
  const [icsUrl, setIcsUrl] = React.useState(null);
  const [status, setStatus] = React.useState("");

  const handleCreateEvent = async () => {
    setStatus("Generating iCalendar file...");
    setStatus("Generating iCalendar file...");
    setIcsUrl(null);
    try {
      // Get the user's time zone
      const userTimeZone = Intl.DateTimeFormat().resolvedOptions().timeZone;
      console.log("User Time Zone:", userTimeZone);

      // Send user input and time zone to the backend to create .ics
      const backendResponse = await axios.post(`${backendUrl}/create-event`, {
        user_input: userInput,
        time_zone: userTimeZone, // Include the time zone
      });

      if (backendResponse.data && backendResponse.data.ics_url) {
        setIcsUrl(backendResponse.data.ics_url);
        setStatus("iCalendar file generated successfully!");
      } else {
        setStatus("Error: Could not get iCalendar file URL from backend.");
      }
    } catch (error) {
      console.error("Error creating event:", error);
      setStatus(`Error creating event: ${error.message}`);
    }
  };

  const openIcsUrl = () => {
    if (icsUrl) {
      Linking.openURL(icsUrl);
    }
  };

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Calendar Event Creator</Text>

      <TextInput
        style={styles.input}
        placeholder="Enter event details (e.g., 'Meeting tomorrow at 10 AM about project X')"
        value={userInput}
        onChangeText={setUserInput}
      />

      <Button title="Create iCalendar File" onPress={handleCreateEvent} />

      {status ? <Text style={styles.status}>{status}</Text> : null}

      {icsUrl && (
        <View style={styles.icsLinkContainer}>
          <Text>iCalendar File URL:</Text>
          <Text style={styles.link} onPress={openIcsUrl}>
            {icsUrl}
          </Text>
          <Button title="Open/Download .ics File" onPress={openIcsUrl} />
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#fff",
    alignItems: "center",
    justifyContent: "center",
    padding: 20,
  },
  title: {
    fontSize: 24,
    fontWeight: "bold",
    marginBottom: 20,
  },
  input: {
    height: 40,
    borderColor: "gray",
    borderWidth: 1,
    marginBottom: 20,
    paddingHorizontal: 10,
    width: "100%",
  },
  status: {
    marginTop: 15,
    fontStyle: "italic",
    color: "grey",
  },
  icsLinkContainer: {
    marginTop: 20,
    padding: 15,
    borderWidth: 1,
    borderColor: "#ccc",
    width: "100%",
    alignItems: "center",
  },
  link: {
    color: "blue",
    textDecorationLine: "underline",
    marginBottom: 10,
    marginTop: 5,
  },
});
