import urllib.request
import urllib.parse
import json

base = "http://127.0.0.1:5000"

print("--- 1. Testing GET / ---")
with urllib.request.urlopen(base + "/") as r:
    html = r.read().decode("utf-8")
    assert "CampusFix" in html, "CampusFix brand not found in HTML"
    assert "role-toggle-group" in html, "Role toggle not found"
    assert "Maintenance Dashboard" in html, "Dashboard not found"
    assert "Recurring Issues" in html, "Recurring Issues card not found"
    assert "Report a Complaint" in html, "Complaint form not found"
    print("[PASS] Root page loaded successfully (HTML verified)")

print("\n--- 2. Testing GET /api/workers ---")
with urllib.request.urlopen(base + "/api/workers") as r:
    workers = json.loads(r.read().decode("utf-8"))
    assert len(workers) == 4, f"Expected 4 workers, got {len(workers)}"
    print("[PASS] 4 workers seeded properly:")
    for w in workers:
        print(f"   Worker #{w['id']}: {w['name']} - {w['role']} ({w['phone']})")

print("\n--- 3. Testing GET /api/stats ---")
with urllib.request.urlopen(base + "/api/stats") as r:
    stats = json.loads(r.read().decode("utf-8"))
    print("[PASS] Stats retrieved:")
    print("   Total complaints:", stats["total"])
    print("   Status breakdown:", stats["status_counts"])
    print("   Priority breakdown:", stats["priority_counts"])
    print("   Recurring count:", stats.get("recurring_count"))
    assert stats["total"] >= 20
    assert "recurring_count" in stats
    assert stats["recurring_count"] >= 3

print("\n--- 4. Testing Critical complaints sorting at the top ---")
with urllib.request.urlopen(base + "/api/complaints") as r:
    complaints = json.loads(r.read().decode("utf-8"))
    priorities = [c["priority"] for c in complaints]
    last_crit = max(i for i, p in enumerate(priorities) if p == "Critical")
    first_non_crit = min(i for i, p in enumerate(priorities) if p != "Critical")
    assert first_non_crit > last_crit, "Critical complaints not sorted at top"
    print(f"[PASS] All Critical complaints are at the top of the list! (Count: {last_crit + 1})")

print("\n--- 5. Testing Recurring Issue Detection & History ---")
with urllib.request.urlopen(base + "/api/complaints") as r:
    complaints = json.loads(r.read().decode("utf-8"))
    rec_complaints = [c for c in complaints if c["is_recurring"]]
    assert len(rec_complaints) >= 3, "Expected at least 3 recurring complaints in seed data"
    print(f"[PASS] Found {len(rec_complaints)} recurring complaints in database:")
    for rc in rec_complaints:
        print(f"   {rc['ticket_no']} ({rc['category']} @ {rc['location']}): total={rc['total_occurrences']}, earlier={rc['recurrence_count']}")
    
    # Test history endpoint
    sample_id = rec_complaints[0]["id"]
    with urllib.request.urlopen(f"{base}/api/complaints/{sample_id}/history") as hr:
        hist = json.loads(hr.read().decode("utf-8"))
        assert hist["total"] >= 2
        print(f"[PASS] History for ticket #{sample_id} ({hist['category']} @ {hist['location']}): {hist['total']} complaints found (newest first)")

# Test filtering by recurring=true
with urllib.request.urlopen(base + "/api/complaints?recurring=true") as r:
    filtered_rec = json.loads(r.read().decode("utf-8"))
    assert len(filtered_rec) == len(rec_complaints)
    assert all(c["is_recurring"] for c in filtered_rec)
    print(f"[PASS] Filter by recurring=true returned {len(filtered_rec)} items accurately.")

print("\n--- 6. Testing Auto Priority Detection ---")
# Critical keyword ('sparking') with user priority=Low -> should become Critical and auto_flagged=1
form_data = urllib.parse.urlencode({
    "category": "Electrical",
    "location": "Physics Lab 3",
    "description": "Switchboard is sparking near the chemical table.",
    "priority": "Low"
}).encode("utf-8")
req = urllib.request.Request(base + "/api/complaints", data=form_data)
with urllib.request.urlopen(req) as r:
    res = json.loads(r.read().decode("utf-8"))
    assert res["success"] is True
    assert res["complaint"]["priority"] == "Critical"
    assert res["auto_flagged"] is True
    assert res["trigger_keyword"] == "sparking"
    assert res["complaint"]["auto_flagged"] == 1
    new_crit_id = res["complaint"]["id"]
    print(f"[PASS] Auto-detected as Critical: {res['trigger_keyword']} (auto_flagged=1)")

print("\n--- 7. Testing Worker Assignment & Status Advance ---")
assign_data = json.dumps({"worker_id": 1}).encode("utf-8")
req = urllib.request.Request(f"{base}/api/complaints/{new_crit_id}/assign", data=assign_data, headers={
    "Content-Type": "application/json"
})
with urllib.request.urlopen(req) as r:
    assign_res = json.loads(r.read().decode("utf-8"))
    assert assign_res["success"] is True
    assert assign_res["complaint"]["assigned_worker_id"] == 1
    assert assign_res["complaint"]["status"] == "Assigned"
    print(f"[PASS] Assigned to {assign_res['complaint']['assigned_worker_name']} and moved to Assigned")

req = urllib.request.Request(f"{base}/api/complaints/{new_crit_id}/advance", data=b"", headers={
    "Content-Type": "application/json"
})
with urllib.request.urlopen(req) as r:
    adv_res = json.loads(r.read().decode("utf-8"))
    assert adv_res["complaint"]["status"] == "In Progress"
    print(f"[PASS] Advanced to: {adv_res['complaint']['status']}")

print("\n==========================================")
print("ALL AUTOMATED TESTS PASSED!")
print("==========================================")
