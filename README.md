# DaVinci Resolve Project Organizer

A Python command-line tool that scans your DaVinci Resolve project folders and tells you **where your disk space is going** — proxy media, optimized media, render cache, stills, and backups.  
It creates clear **JSON** and **CSV** reports so you can safely clean up space later.

---

##  Why I Built This
While editing in DaVinci Resolve, my drives kept filling up quickly. Resolve generates **proxy**, **optimized**, and **cache** files that can reach hundreds of gigabytes, but it’s not easy to see where they all are.  
This tool solves that problem by:
- Scanning any folder you choose  
- Grouping files into familiar Resolve categories  
- Showing how much space each type uses  
- Listing your largest files  
- Exporting a readable report (JSON + CSV)

---

##  Features
- **Safe audit only** – it never deletes files unless you explicitly add a delete flag (Phase 2).  
- **Human-readable output** – totals, categories, and top-N largest files.  
- **JSON + CSV reports** – easy to analyze in Excel, Sheets, or scripts.  
- **Configurable** – you can choose how many largest files to display (`--top N`).  
- **Cross-platform** – works on Windows, macOS, and Linux.

---

##  How to Run

### 1. Install Python 3.10 +
Make sure Python is installed and available in your terminal:
```bash
python --version
