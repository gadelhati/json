/**
 * Inicializa o mapa Leaflet da aba "Mapa", desenhando uma camada por arquivo
 * GeoJSON importado (agrupamento feito no backend, ver
 * JsonStore.feature_collections_by_layer em src/services.py), cada uma com
 * uma cor própria e um checkbox para ligar/desligar.
 */
(function () {
    "use strict";

    var PALETTE = [
        "#e6194b", "#3cb44b", "#4363d8", "#f58231", "#911eb4",
        "#42d4f4", "#f032e6", "#9a6324", "#808000", "#000075",
    ];

    function escapeHtml(value) {
        return String(value).replace(/[&<>"']/g, function (ch) {
            return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[ch];
        });
    }

    function popupHtml(properties) {
        var keys = Object.keys(properties || {});
        if (keys.length === 0) {
            return "<em>Sem propriedades</em>";
        }
        var rows = keys.map(function (key) {
            return "<tr><th>" + escapeHtml(key) + "</th><td>" + escapeHtml(properties[key]) + "</td></tr>";
        }).join("");
        return '<table class="map-popup">' + rows + "</table>";
    }

    document.addEventListener("DOMContentLoaded", function () {
        var mapEl = document.getElementById("map");
        if (!mapEl || typeof L === "undefined") {
            return;
        }

        var dataScript = document.getElementById("map-layers-data");
        var layersData = [];
        try {
            layersData = JSON.parse((dataScript && dataScript.textContent) || "[]");
        } catch (e) {
            layersData = [];
        }

        var map = L.map(mapEl);
        L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
            maxZoom: 19,
            attribution: "&copy; colaboradores do OpenStreetMap",
        }).addTo(map);

        var leafletLayersByName = {};
        var bounds = L.latLngBounds([]);

        layersData.forEach(function (layer, index) {
            var color = PALETTE[index % PALETTE.length];

            var geoLayer = L.geoJSON(layer.featureCollection, {
                style: function () {
                    return { color: color, weight: 2, fillColor: color, fillOpacity: 0.3 };
                },
                pointToLayer: function (feature, latlng) {
                    return L.circleMarker(latlng, {
                        radius: 6,
                        color: color,
                        fillColor: color,
                        fillOpacity: 0.85,
                        weight: 2,
                    });
                },
                onEachFeature: function (feature, lyr) {
                    lyr.bindPopup(popupHtml(feature.properties));
                },
            });

            leafletLayersByName[layer.name] = geoLayer;
            geoLayer.addTo(map);

            if (geoLayer.getBounds && geoLayer.getBounds().isValid()) {
                bounds.extend(geoLayer.getBounds());
            }

            document.querySelectorAll("[data-layer-swatch]").forEach(function (el) {
                if (el.getAttribute("data-layer-swatch") === layer.name) {
                    el.style.backgroundColor = color;
                }
            });
        });

        if (bounds.isValid()) {
            map.fitBounds(bounds, { padding: [24, 24] });
        } else {
            map.setView([0, 0], 2);
        }

        document.querySelectorAll(".layer-toggle").forEach(function (checkbox) {
            checkbox.addEventListener("change", function () {
                var layerName = checkbox.getAttribute("data-layer");
                var geoLayer = leafletLayersByName[layerName];
                if (!geoLayer) {
                    return;
                }
                if (checkbox.checked) {
                    map.addLayer(geoLayer);
                } else {
                    map.removeLayer(geoLayer);
                }
            });
        });
    });
})();
