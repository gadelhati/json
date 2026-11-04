let geotiffLayer = null;

document.getElementById("btnUploadGeotiff").addEventListener("click", async () => {
  const input = document.getElementById("geotiffInput");
  if (!input.files.length) return alert("Selecione um arquivo GeoTIFF");

  const formData = new FormData();
  formData.append("file", input.files[0]);

  const res = await fetch("/geotiff/upload", { method: "POST", body: formData });
  if (!res.ok) return alert("Erro ao importar GeoTIFF");
  const data = await res.json();

  if (geotiffLayer) map.removeLayer(geotiffLayer);
  geotiffLayer = L.imageOverlay(data.preview_url, data.bounds, { opacity: 0.8 }).addTo(map);
  map.fitBounds(data.bounds);

  document.getElementById("metadataTabs").style.display = "flex";
  document.getElementById("meta-geo").textContent = JSON.stringify(data.metadata.geoespacial, null, 2);
  document.getElementById("meta-sensor").textContent = JSON.stringify(data.metadata.dados_sensores, null, 2);
  document.getElementById("meta-desc").textContent = JSON.stringify(data.metadata.descritivo, null, 2);
});

document.querySelectorAll(".sub-tab-btn").forEach(btn => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".sub-tab-pane").forEach(p => p.style.display = "none");
    document.querySelectorAll(".sub-tab-btn").forEach(b => b.classList.remove("active"));
    document.getElementById(btn.dataset.target).style.display = "block";
    btn.classList.add("active");
  });
});

// const res = await fetch("/geotiff/upload", { method: "POST", body: formData });
// if (!res.ok) {
//   const err = await res.json().catch(() => ({}));
//   return alert("Erro ao importar GeoTIFF: " + (err.detail || res.status));
// }