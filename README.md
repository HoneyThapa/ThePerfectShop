# ThePerfectShop — MVP Data Pipeline (Step 1–3)

**ThePerfectShop** is an **expiry risk intelligence system** for retail inventory.  
This repository contains the **core MVP data pipeline** that:

1. Ingests messy Excel/CSV exports (sales, inventory-by-batch, purchases)
2. Builds store–SKU sales behavior features
3. Computes a **daily batch-level expiry risk list**

This implementation intentionally stops at **Step 3 (Baseline Risk Scoring)**.  
Actions, UI, scheduling, and ML are **Phase 2**.

---

## 📌 What this MVP does

✔ Handles messy retail Excel / CSV files  
✔ Normalizes column names and validates data  
✔ Stores clean data in PostgreSQL  
✔ Computes rolling sales velocities (v7, v14, v30)  
✔ Calculates batch-level expiry risk (deterministic, explainable)  
✔ Exposes a `/risk` API endpoint  

---

## 🧱 Architecture (MVP Scope)
Excel / CSV
↓
Ingestion + Validation
↓
Clean Tables (Postgres)
↓
Feature Builder (Store–SKU velocity)
↓
Baseline Risk Scoring
↓
Risk Inbox API
