from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import random

app = FastAPI(title="Smart Waste Management System")

# Define the WasteBin model
class WasteBin(BaseModel):
    id: int
    location: str
    fillLevel: int = 0
    needsCollection: bool = False

# List to store the bins
bins: List[WasteBin] = []

# Endpoint to add bins
@app.post("/bins/", response_model=dict)
def add_bins(new_bins: List[WasteBin]):
    existing_ids = {bin.id for bin in bins}
    for bin in new_bins:
        if bin.id in existing_ids:
            raise HTTPException(status_code=400, detail=f"Bin ID {bin.id} already exists.")
        bin.fillLevel = 0
        bin.needsCollection = False
        bins.append(bin)
    return {"message": f"{len(new_bins)} bins added successfully."}

# Endpoint to collect sensor data and update the fill level and collection status
@app.post("/bins/collect-sensor-data/", response_model=dict)
def collect_sensor_data():
    if not bins:
        raise HTTPException(status_code=404, detail="No bins available.")
    for bin in bins:
        bin.fillLevel = random.randint(0, 100)  # Simulate sensor data
        bin.needsCollection = bin.fillLevel >= 75  # Mark for collection if 75% or more
    return {"message": "Sensor data collected and updated."}

# Endpoint to display all bin data (like in your C++ displayBins function)
@app.get("/bins/", response_model=List[WasteBin])
def display_bins():
    if not bins:
        raise HTTPException(status_code=404, detail="No bins available.")
    return bins

# Endpoint to delete a bin (similar to deleteBinData in C++)
@app.delete("/bins/{bin_id}", response_model=dict)
def delete_bin(bin_id: int):
    global bins
    for bin in bins:
        if bin.id == bin_id:
            bins = [b for b in bins if b.id != bin_id]
            return {"message": f"Bin ID {bin_id} deleted successfully."}
    raise HTTPException(status_code=404, detail=f"Bin ID {bin_id} not found.")

# Endpoint to optimize the collection route (like optimizeCollectionRoute in C++)
@app.get("/optimize-route/", response_model=dict)
def optimize_collection_route():
    to_collect = [bin for bin in bins if bin.needsCollection]
    if not to_collect:
        raise HTTPException(status_code=404, detail="No bins need collection right now.")
    sorted_bins = sorted(to_collect, key=lambda x: x.fillLevel, reverse=True)  # Sort by fill level
    return {"optimizedRoute": [{"id": bin.id, "location": bin.location, "fillLevel": bin.fillLevel} for bin in sorted_bins]}

# Endpoint to save bin data to a file (mimicking saveData in C++)
@app.post("/bins/save-data/", response_model=dict)
def save_data():
    with open("bin_data.txt", "w") as file:
        for bin in bins:
            file.write(f"{bin.id} {bin.location} {bin.fillLevel} {bin.needsCollection}\n")
    return {"message": "Bin data saved successfully."}

# Endpoint to load bin data from a file (mimicking loadData in C++)
@app.post("/bins/load-data/", response_model=dict)
def load_data():
    try:
        with open("bin_data.txt", "r") as file:
            bins.clear()
            for line in file:
                id, location, fillLevel, needsCollection = line.split()
                bins.append(WasteBin(
                    id=int(id),
                    location=location,
                    fillLevel=int(fillLevel),
                    needsCollection=needsCollection.lower() == "true"
                ))
        return {"message": "Bin data loaded successfully."}
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="No saved data found.")
