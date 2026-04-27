import { initializeApp } from "firebase/app";
import { getAuth } from "firebase/auth";

// Replace with your actual Firebase project configuration
const firebaseConfig = {
  apiKey: "AIzaSyCKOJntcUFE0eg65bp0A3c6vSd-Rqzug2w",
  authDomain: "sentinel-sports-ip.firebaseapp.com",
  projectId: "sentinel-sports-ip",
  storageBucket: "sentinel-sports-ip.firebasestorage.app",
  messagingSenderId: "1051966477615",
  appId: "1:1051966477615:web:ca80a4ba292377a73abdda",
  measurementId: "G-EZ55H2N8VH"
};

const app = initializeApp(firebaseConfig);
export const auth = getAuth(app);
