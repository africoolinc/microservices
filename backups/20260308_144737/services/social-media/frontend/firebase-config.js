// Firebase Configuration for Lyrikali
// Updated: March 3, 2026

const firebaseConfig = {
  apiKey: "AIzaSyD3JYyK4aN7G3B8PlU7tXIqn1GkuXm9Z-Q",
  authDomain: "africool-fd821.firebaseapp.com",
  projectId: "africool-fd821",
  storageBucket: "africool-fd821.firebasestorage.app",
  messagingSenderId: "149058299293",
  appId: "1:149058299293:web:ee9d1775d70b277a67bb74",
  measurementId: "G-GJQDHVVRSH"
};

// Initialize Firebase
firebase.initializeApp(firebaseConfig);

// Initialize Analytics (optional)
const analytics = firebase.analytics();

// Export auth for use in app.js
export const firebaseAuth = firebase.auth();
export const firebaseDb = firebase.firestore();
