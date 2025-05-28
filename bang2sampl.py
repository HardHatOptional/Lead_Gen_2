import math
import random
import time
import csv
import json
import os
from dotenv import load_dotenv

load_dotenv()
import requests
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, simpledialog
from pymongo import MongoClient, errors
from transformers import pipeline
from bson import json_util  # For ObjectId serialization

# ---------------------------
# Configuration & MongoDB Setup
# ---------------------------
GOOGLE_MONTHLY_LIMIT = 1000  
SAFETY_FACTOR = 2.0
QUALITY_THRESHOLD = 70  # Evaluated quality threshold

# Google Custom Search API Credentials
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_CX = os.getenv("GOOGLE_CX")
GOOGLE_SEARCH_URL = os.getenv("GOOGLE_SEARCH_URL", "https://www.googleapis.com/customsearch/v1")
BANG3_API_URL = os.getenv("BANG3_API_URL", "http://localhost:5001/scrape")

# MongoDB connection URI (optional)
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
client = MongoClient(MONGO_URI)
db = client["leadgen_db"]
usage_col = db["api_usage"]
fallback_col = db["fallback_events"]
if usage_col is not None and usage_col.count_documents({}) == 0:
    usage_col.insert_one({"service": "usage", "google": 0})

CSV_FILE = "bang2_output.csv"
if not os.path.exists(CSV_FILE):
    with open(CSV_FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["url", "timestamp"])

# ---------------------------
# Function to Send URLs to Bang3 API
# ---------------------------
def send_to_bang3(urls):
    try:
        response = requests.post(BANG3_API_URL, json={"urls": urls}, timeout=10)
        print("[Bang3 API] Response:", response.json())
    except Exception as e:
        print("[Bang3 API] Error sending URLs:", e)

# ---------------------------
# Backup URLs to CSV
# ---------------------------
def backup_urls_to_csv(urls):
    with open(CSV_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        for url in urls:
            writer.writerow([url, time.time()])
    print("[Backup] URLs saved to CSV.")

# ---------------------------
# Process Query and Link to Bang3
# ---------------------------
def process_query(query, total_num_results):
    api_calls_needed = math.ceil(total_num_results / 10)
    all_results = []
    for i in range(api_calls_needed):
        start = i * 10 + 1
        num_for_call = min(10, total_num_results - i * 10)
        partial_results = safe_api_call(call_google_api_paginated, query, "google", start, num_for_call)
        all_results.extend(partial_results)
    
    urls = [res["url"] for res in all_results]
    
    if urls:
        backup_urls_to_csv(urls)  # Save URLs for redundancy
        send_to_bang3(urls)  # Send URLs to Bang3 for scraping
    
    return all_results, evaluate_result_relevance(" ".join([res["snippet"] for res in all_results]), query)

# ---------------------------
# GUI Implementation (Tkinter)
# ---------------------------
class LeadGenGUI:
    def __init__(self, master):
        self.master = master
        master.title("AI-Driven Lead Generator (Google CSE Edition)")

        self.label = tk.Label(master, text="Enter your lead generation query:")
        self.label.pack(pady=5)

        self.query_entry = tk.Entry(master, width=80)
        self.query_entry.pack(padx=5, pady=5)

        self.results_label = tk.Label(master, text="Number of Results (max 10 per API call):")
        self.results_label.pack(pady=5)

        self.num_results_entry = tk.Entry(master, width=10)
        self.num_results_entry.insert(0, "10")
        self.num_results_entry.pack(pady=5)

        self.search_button = tk.Button(master, text="Search", command=self.run_query)
        self.search_button.pack(pady=5)

        self.results_text = scrolledtext.ScrolledText(master, width=100, height=20)
        self.results_text.pack(padx=5, pady=5)

    def run_query(self):
        query = self.query_entry.get().strip()
        if not query:
            messagebox.showwarning("Input Error", "Please enter a query.")
            return

        try:
            num_results = int(self.num_results_entry.get().strip())
        except ValueError:
            messagebox.showwarning("Input Error", "Please enter a valid number for results.")
            return

        self.results_text.delete("1.0", tk.END)
        self.results_text.insert(tk.END, f"Processing query: {query}\n")

        final_results, quality = process_query(query, num_results)
        self.results_text.insert(tk.END, f"\nEvaluated Quality: {quality}\n")
        self.results_text.insert(tk.END, "\n--- Final Results ---\n")
        for res in final_results:
            self.results_text.insert(tk.END, f"Title: {res['title']}\n")
            self.results_text.insert(tk.END, f"URL: {res['url']}\n")
            self.results_text.insert(tk.END, f"Snippet: {res['snippet']}\n\n")
        self.results_text.insert(tk.END, "Processing complete.\n")

# ---------------------------
# Main Function
# ---------------------------
def main():
    root = tk.Tk()
    gui = LeadGenGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
