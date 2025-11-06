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
```
bash
python --version
```

### 2. Clone this repository
```
git clone https://github.com/enockola/Resolve-Video-Tracker.git
cd Resolve-Video-Tracker
```

### 3. Run the auditor

Example (Windows paths shown, forward slashes also work):

```
python resolve_space_audit.py "D:/Videos" --report out/report --top 30
```

### 4. View results

Console summary (category sizes, top files, top extensions)
JSON report: `out/report.json`
CSV report: `out/report.csv` → open in Excel or Google Sheets

### Example Output
```
Scanned: D:/Videos
Total: 512.3 GB

== Size by category ==
       proxy: 180.5 GB
    optimized: 75.2 GB
 render_cache: 90.8 GB
       stills: 12.6 GB
      backups: 4.3 GB
        other: 149.0 GB

== Top largest files ==
  8.6 GB   D:/Videos/ProxyMedia/clip001.mov
  7.2 GB   D:/Videos/OptimizedMedia/clip002.mov
```

---

## Project Structure
```csharp
resolve-project-organizer/
│
├── resolve_space_audit.py     # main script
├── out/                       # JSON + CSV reports
├── tests/                     # future test files
├── README.md
└── requirements.txt
```

## Roadmap

- Phase 1 – Audit Mode (scan + report)
- Phase 2 – Safe Deletion with --min-age-days
- Phase 3 – Simple GUI (Tkinter or Flask)
- Phase 4 – Archive Projects to ZIP / external drive

## Key Learnings

- Efficiently scanned thousands of files using os.walk and pathlib without reading file contents.
- Grouped raw folder data into meaningful Resolve categories.
- Designed a linear-time algorithm (O(N)) that works even on large drives.
- Learned safe program design: read-only first, deletion only with confirmations.
- Practiced structuring a real-world CLI project for GitHub.

---

## Author

Enoch Olayemi
Computer Science major | Web Development minor | Cybersecurity certificate
Connect with me on [LinkedIn](https://www.linkedin.com/in/enoch-olayemi/)
 or check out more projects on GitHub
.


## License

MIT License © 2025 Enoch Olayemi
