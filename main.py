from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import random
import json
import threading
from datetime import datetime

app = FastAPI(title="Smart Waste Management System")

# Lock for thread-safe file operations
lock = threading.Lock()

# WasteBin model with timestamp
class WasteBin(BaseModel):
    id: int
    location: str
    fillLevel: int = 0
    needsCollection: bool = False
    lastUpdated: str = datetime.utcnow().isoformat()

# In-memory list of bins
bins: List[WasteBin] = []
next_bin_id = 1  # Internal ID tracker


# Helper: Load data from file
def load_bins_from_file():
    global bins, next_bin_id
    try:
        with lock:
            with open("bin_data.json", "r") as f:
                data = json.load(f)
                bins.clear()
                for item in data:
                    bins.append(WasteBin(**item))
                # Update next_bin_id to avoid ID collisions
                if bins:
                    next_bin_id = max(b.id for b in bins) + 1
    except FileNotFoundError:
        bins.clear()
        next_bin_id = 1
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading data: {str(e)}")


# Helper: Save data to file
def save_bins_to_file():
    try:
        with lock:
            with open("bin_data.json", "w") as f:
                json.dump([bin.dict() for bin in bins], f, indent=4)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving data: {str(e)}")


# Model for bin creation (no ID required from client)
class BinCreateRequest(BaseModel):
    location: str


# Add bins with server-assigned IDs
@app.post("/bins/", response_model=dict)
def add_bins(new_bins: List[BinCreateRequest]):
    global next_bin_id
    created = []
    for bin_data in new_bins:
        new_bin = WasteBin(
            id=next_bin_id,
            location=bin_data.location,
            fillLevel=0,
            needsCollection=False,
            lastUpdated=datetime.utcnow().isoformat()
        )
        bins.append(new_bin)
        created.append(new_bin)
        next_bin_id += 1
    save_bins_to_file()
    return {"message": f"{len(created)} bins added successfully.", "bins": created}


# Collect and update sensor data
@app.post("/bins/collect-sensor-data/", response_model=dict)
def collect_sensor_data():
    if not bins:
        raise HTTPException(status_code=404, detail="No bins available.")
    for bin in bins:
        bin.fillLevel = random.randint(0, 100)
        bin.needsCollection = bin.fillLevel >= 75
        bin.lastUpdated = datetime.utcnow().isoformat()
    save_bins_to_file()
    return {"message": "Sensor data collected and updated."}


# Display all bins
@app.get("/bins/", response_model=List[WasteBin])
def display_bins():
    if not bins:
        raise HTTPException(status_code=404, detail="No bins available.")
    return bins


# Delete bin by ID
@app.delete("/bins/{bin_id}", response_model=dict)
def delete_bin(bin_id: int):
    global bins
    for bin in bins:
        if bin.id == bin_id:
            bins = [b for b in bins if b.id != bin_id]
            save_bins_to_file()
            return {"message": f"Bin ID {bin_id} deleted successfully."}
    raise HTTPException(status_code=404, detail=f"Bin ID {bin_id} not found.")


# Optimize collection route
@app.get("/optimize-route/", response_model=dict)
def optimize_collection_route():
    to_collect = [bin for bin in bins if bin.needsCollection]
    if not to_collect:
        raise HTTPException(status_code=404, detail="No bins need collection right now.")
    sorted_bins = sorted(to_collect, key=lambda x: x.fillLevel, reverse=True)
    return {"optimizedRoute": [{"id": bin.id, "location": bin.location, "fillLevel": bin.fillLevel} for bin in sorted_bins]}


# Load bins from file manually
@app.post("/bins/load-data/", response_model=dict)
def load_data():
    load_bins_from_file()
    return {"message": "Bin data loaded successfully."}


# Save bins to file manually
@app.post("/bins/save-data/", response_model=dict)
def save_data():
    save_bins_to_file()
    return {"message": "Bin data saved successfully."}
