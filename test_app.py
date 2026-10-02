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
    assert stats["total"] >= 20
    assert "Critical" in stats["priority_counts"]

print("\n--- 4. Testing Critical complaints sorting at the top ---")
with urllib.request.urlopen(base + "/api/complaints") as r:
    complaints = json.loads(r.read().decode("utf-8"))
    priorities = [c["priority"] for c in complaints]
    last_crit = max(i for i, p in enumerate(priorities) if p == "Critical")
    first_non_crit = min(i for i, p in enumerate(priorities) if p != "Critical")
    assert first_non_crit > last_crit, "Critical complaints not sorted at top"
    print(f"[PASS] All Critical complaints are at the top of the list! (Count: {last_crit + 1})")

print("\n--- 5. Testing Auto Priority Detection ---")
# 5a. Critical keyword ('sparking') with user priority=Low -> should become Critical and auto_flagged=1
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

# 5b. High keyword ('leaking') with user priority=Low -> should become High and auto_flagged=1
form_data = urllib.parse.urlencode({
    "category": "Plumbing",
    "location": "Hostel Washroom",
    "description": "The ceiling pipe is leaking slowly.",
    "priority": "Low"
}).encode("utf-8")
req = urllib.request.Request(base + "/api/complaints", data=form_data)
with urllib.request.urlopen(req) as r:
    res = json.loads(r.read().decode("utf-8"))
    assert res["success"] is True
    assert res["complaint"]["priority"] == "High"
    assert res["auto_flagged"] is True
    assert res["trigger_keyword"] == "leaking"
    print(f"[PASS] Auto-detected as High: {res['trigger_keyword']} (auto_flagged=1)")

# 5c. Never lower user priority: user chooses Critical, description has 'leak'
form_data = urllib.parse.urlencode({
    "category": "Plumbing",
    "location": "Server Room B",
    "description": "Small leak near server rack.",
    "priority": "Critical"
}).encode("utf-8")
req = urllib.request.Request(base + "/api/complaints", data=form_data)
with urllib.request.urlopen(req) as r:
    res = json.loads(r.read().decode("utf-8"))
    assert res["success"] is True
    assert res["complaint"]["priority"] == "Critical"
    assert res["auto_flagged"] is False
    print("[PASS] User Critical priority was preserved (never lowered)")

print("\n--- 6. Testing Worker Assignment & Status Advance ---")
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
