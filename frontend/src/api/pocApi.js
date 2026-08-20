const BASE_URL = "/api/poc";

export async function createPoc(pocData) {
  const res = await fetch(BASE_URL, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(pocData),
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(JSON.stringify(err));
  }
  return res.json();
}

export async function getPocsByOpportunity(opportunityId) {
  const res = await fetch(`${BASE_URL}/opportunity/${opportunityId}`);
  if (!res.ok) throw new Error("Failed to fetch POCs");
  return res.json();
}

export async function updatePoc(pocId, pocData) {
  const res = await fetch(`${BASE_URL}/${pocId}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(pocData),
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(JSON.stringify(err));
  }
  return res.json();
}
