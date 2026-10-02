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
    assert "Worker Workload" in html, "Worker Workload section not found"
    assert "Recurring Issues" in html, "Recurring Issues card not found"
    assert "Report a Complaint" in html, "Complaint form not found"
    print("[PASS] Root page loaded successfully (HTML verified)")

print("\n--- 2. Testing GET /api/workers & GET /api/workload ---")
with urllib.request.urlopen(base + "/api/workload") as r:
    workload = json.loads(r.read().decode("utf-8"))
    assert len(workload) == 4, f"Expected 4 workers, got {len(workload)}"
    print("[PASS] 4 workers workload retrieved:")
    for w in workload:
        print(f"   Worker #{w['id']}: {w['name']} ({w['role']}) -> Active: {w['active_count']}, Resolved: {w['resolved_count']}")
    
    # Verify at least one worker has 5+ active complaints
    max_active = max(w["active_count"] for w in workload)
    assert max_active >= 5, f"Expected at least one worker with 5+ active, got {max_active}"
    print(f"[PASS] Overloaded worker check passed (Max active: {max_active})")

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
    print(f"[PASS] Found {len(rec_complaints)} recurring complaints in database.")
    
    sample_id = rec_complaints[0]["id"]
    with urllib.request.urlopen(f"{base}/api/complaints/{sample_id}/history") as hr:
        hist = json.loads(hr.read().decode("utf-8"))
        assert hist["total"] >= 2
        print(f"[PASS] History for ticket #{sample_id} ({hist['category']} @ {hist['location']}): {hist['total']} complaints found")

print("\n--- 6. Testing Auto Priority Detection ---")
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
    new_crit_id = res["complaint"]["id"]
    print(f"[PASS] Auto-detected as Critical: {res['trigger_keyword']} (auto_flagged=1)")

print("\n--- 7. Testing Worker Assignment & Workload Update ---")
# Assign to least-loaded worker (Sarah Jenkins, id=4)
with urllib.request.urlopen(base + "/api/workload") as r:
    w_before = {w["id"]: w for w in json.loads(r.read().decode("utf-8"))}
    sarah_before = w_before[4]["active_count"]

assign_data = json.dumps({"worker_id": 4}).encode("utf-8")
req = urllib.request.Request(f"{base}/api/complaints/{new_crit_id}/assign", data=assign_data, headers={
    "Content-Type": "application/json"
})
with urllib.request.urlopen(req) as r:
    assign_res = json.loads(r.read().decode("utf-8"))
    assert assign_res["success"] is True

with urllib.request.urlopen(base + "/api/workload") as r:
    w_after = {w["id"]: w for w in json.loads(r.read().decode("utf-8"))}
    assert w_after[4]["active_count"] == sarah_before + 1
    print(f"[PASS] Worker workload updated on assignment (Sarah active: {sarah_before} -> {w_after[4]['active_count']})")

print("\n==========================================")
print("ALL AUTOMATED TESTS PASSED!")
print("==========================================")
