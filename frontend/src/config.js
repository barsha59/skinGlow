// frontend/src/config.js
const API_URL =
  process.env.REACT_APP_API_URL || "http://backend:5002";  // <- use 'backend' here
const STRIPE_PUBLISHABLE_KEY =
  "pk_test_51Sl1TM2YdULA0kvG2JENo4pXukqssFkAHNfEYoeqzdGrkIxBLJh8YirmBdusf6yaCJxQXWq1W7usBupkDNupbPHf00AVabIsFL";

export { API_URL, STRIPE_PUBLISHABLE_KEY };