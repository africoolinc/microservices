// Firebase Configuration for Lyrikali
// Replace with your Firebase project config

const firebaseConfig = {
  apiKey: "AIzaSyAmS0qOzT2QIfw_4pvGjdK9zRDUNYrX41s",
  authDomain: "lyrikali-app.firebaseapp.com",
  projectId: "lyrikali-app",
  storageBucket: "lyrikali-app.appspot.com",
  messagingSenderId: "YOUR_SENDER_ID",
  appId: "YOUR_APP_ID",
  measurementId: "YOUR_MEASUREMENT_ID"
};

// Initialize Firebase
firebase.initializeApp(firebaseConfig);

// Initialize Analytics (optional)
const analytics = firebase.analytics();

// Export auth for use in app.js
export const firebaseAuth = firebase.auth();
export const firebaseDb = firebase.firestore();
