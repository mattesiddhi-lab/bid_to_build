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
    assert stats["total"] == 20
    assert stats["priority_counts"]["Critical"] == 5
    assert stats["priority_counts"]["High"] == 5
    assert stats["priority_counts"]["Medium"] == 5
    assert stats["priority_counts"]["Low"] == 5

print("\n--- 4. Testing GET /api/complaints ---")
with urllib.request.urlopen(base + "/api/complaints") as r:
    complaints = json.loads(r.read().decode("utf-8"))
    assert len(complaints) == 20
    print(f"[PASS] 20 complaints seeded. Sample ticket: {complaints[0]['ticket_no']} ({complaints[0]['category']})")

print("\n--- 5. Testing POST /api/complaints (Create new ticket) ---")
# Submit a new complaint
form_data = urllib.parse.urlencode({
    "category": "Plumbing",
    "location": "Chemistry Lab 102 - Fume Hood Sink",
    "description": "Severe sulfuric acid trap blockage overflowing onto floor.",
    "priority": "Critical"
}).encode("utf-8")

req = urllib.request.Request(base + "/api/complaints", data=form_data, headers={
    "Content-Type": "application/x-www-form-urlencoded"
})
with urllib.request.urlopen(req) as r:
    new_res = json.loads(r.read().decode("utf-8"))
    assert new_res["success"] is True
    created = new_res["complaint"]
    print(f"[PASS] Created ticket: {created['ticket_no']}, Priority: {created['priority']}, Status: {created['status']}")
    new_id = created["id"]

print("\n--- 6. Testing POST /api/complaints/<id>/assign (Admin assigns worker) ---")
# Admin assigns Marcus Chen (worker #2) to the new ticket
assign_data = json.dumps({"worker_id": 2}).encode("utf-8")
req = urllib.request.Request(f"{base}/api/complaints/{new_id}/assign", data=assign_data, headers={
    "Content-Type": "application/json"
})
with urllib.request.urlopen(req) as r:
    assign_res = json.loads(r.read().decode("utf-8"))
    assert assign_res["success"] is True
    c = assign_res["complaint"]
    print(f"[PASS] Assigned to: {c['assigned_worker_name']} ({c['assigned_worker_role']})")
    print(f"       Status moved to: {c['status']}")
    assert c["status"] == "Assigned"

print("\n--- 7. Testing POST /api/complaints/<id>/advance (Admin workflow progression) ---")
# Step 1: Move from Assigned -> In Progress
req = urllib.request.Request(f"{base}/api/complaints/{new_id}/advance", data=b"", headers={
    "Content-Type": "application/json"
})
with urllib.request.urlopen(req) as r:
    adv_res = json.loads(r.read().decode("utf-8"))
    assert adv_res["complaint"]["status"] == "In Progress"
    print(f"[PASS] Workflow advanced to: {adv_res['complaint']['status']}")

# Step 2: Move from In Progress -> Resolved
req = urllib.request.Request(f"{base}/api/complaints/{new_id}/advance", data=b"", headers={
    "Content-Type": "application/json"
})
with urllib.request.urlopen(req) as r:
    adv_res = json.loads(r.read().decode("utf-8"))
    assert adv_res["complaint"]["status"] == "Resolved"
    print(f"[PASS] Workflow advanced to: {adv_res['complaint']['status']}")

print("\n--- 8. Testing Filters ---")
# Test filter by priority
with urllib.request.urlopen(base + "/api/complaints?priority=Critical") as r:
    crit_complaints = json.loads(r.read().decode("utf-8"))
    print(f"[PASS] Filter by Priority=Critical returned {len(crit_complaints)} items.")
    for c in crit_complaints:
        assert c["priority"] == "Critical"

# Test filter by status
with urllib.request.urlopen(base + "/api/complaints?status=Resolved") as r:
    res_complaints = json.loads(r.read().decode("utf-8"))
    print(f"[PASS] Filter by Status=Resolved returned {len(res_complaints)} items.")
    for c in res_complaints:
        assert c["status"] == "Resolved"

# Test filter by category
with urllib.request.urlopen(base + "/api/complaints?category=Electrical") as r:
    elec_complaints = json.loads(r.read().decode("utf-8"))
    print(f"[PASS] Filter by Category=Electrical returned {len(elec_complaints)} items.")
    for c in elec_complaints:
        assert c["category"] == "Electrical"

print("\n--- 9. Testing Static Asset Serving (CSS, JS, SVGs) ---")
for asset in ["/static/css/style.css", "/static/js/app.js", "/static/uploads/sample_switchboard.svg"]:
    with urllib.request.urlopen(base + asset) as r:
        assert r.status == 200
        print(f"[PASS] Successfully fetched {asset} (Content-Length: {len(r.read())})")

print("\n==========================================")
print("ALL END-TO-END VERIFICATION CHECKS PASSED!")
print("==========================================")
