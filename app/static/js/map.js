/**
 * Inicializa o mapa Leaflet da aba "Mapa", desenhando uma camada por arquivo
 * GeoJSON importado (agrupamento feito no backend, ver
 * JsonStore.feature_collections_by_layer em src/services.py).
 *
 * Recursos:
 * - Uma cor própria por camada, com checkbox para ligar/desligar.
 * - Slider de opacidade por camada.
 * - Botões para trazer uma camada para frente/enviar para trás (ordem de
 *   sobreposição), mantidos em sincronia com a ordem visual da lista.
 * - Se a página foi aberta com ?layer=<arquivo> (link vindo da aba Tabela,
 *   coluna "camada"), o mapa é enquadrado (fitBounds) apenas nessa camada
 *   em vez de todas.
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
        if (!mapEl) {
            return;
        }
        if (typeof L === "undefined") {
            mapEl.textContent = "Não foi possível carregar a biblioteca do mapa (Leaflet).";
            return;
        }

        var dataScript = document.getElementById("map-layers-data");
        var layersData = [];
        try {
            layersData = JSON.parse((dataScript && dataScript.textContent) || "[]");
        } catch (e) {
            layersData = [];
        }

        var selectedLayer = mapEl.getAttribute("data-selected-layer") || "";

        var map = L.map(mapEl);
        L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
            maxZoom: 19,
            attribution: "&copy; colaboradores do OpenStreetMap",
        }).addTo(map);

        window.map = map; // sobrescreve o global acidental (id="map") pelo mapa real

        var leafletLayersByName = {};
        var boundsByName = {};
        var overallBounds = L.latLngBounds([]);
        // Ordem atual de sobreposição, da mais ao fundo (índice 0) para a mais
        // à frente (último índice). É reaplicada ao mapa sempre que muda.
        var zOrder = layersData.map(function (layer) { return layer.name; });

        layersData.forEach(function (layer, index) {
            var color = PALETTE[index % PALETTE.length];

            var geoLayer = L.geoJSON(layer.featureCollection, {
                style: function () {
                    return { color: color, weight: 2, fillColor: color, opacity: 1, fillOpacity: 0.5 };
                },
                pointToLayer: function (feature, latlng) {
                    return L.circleMarker(latlng, {
                        radius: 6,
                        color: color,
                        fillColor: color,
                        opacity: 1,
                        fillOpacity: 0.5,
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
                boundsByName[layer.name] = geoLayer.getBounds();
                overallBounds.extend(boundsByName[layer.name]);
            }

            document.querySelectorAll("[data-layer-swatch]").forEach(function (el) {
                if (el.getAttribute("data-layer-swatch") === layer.name) {
                    el.style.backgroundColor = color;
                }
            });
        });

        // --- Enquadramento inicial: camada específica (vinda da aba Tabela)
        // ou todas as camadas combinadas. ---
        if (selectedLayer && boundsByName[selectedLayer]) {
            map.fitBounds(boundsByName[selectedLayer], { padding: [24, 24] });
            var selectedGeoLayer = leafletLayersByName[selectedLayer];
            if (selectedGeoLayer) {
                selectedGeoLayer.bringToFront();
            }
            var selectedRow = document.querySelector('[data-layer-row="' + cssEscape(selectedLayer) + '"]');
            if (selectedRow) {
                selectedRow.classList.add("layer-row-selected");
            }
        } else if (overallBounds.isValid()) {
            map.fitBounds(overallBounds, { padding: [24, 24] });
        } else {
            map.setView([0, 0], 2);
        }

        function cssEscape(value) {
            return window.CSS && CSS.escape ? CSS.escape(value) : value.replace(/["\\]/g, "\\$&");
        }

        // --- Ligar/desligar camadas ---
        document.querySelectorAll(".layer-toggle").forEach(function (checkbox) {
            checkbox.addEventListener("change", function () {
                var layerName = checkbox.getAttribute("data-layer");
                var geoLayer = leafletLayersByName[layerName];
                if (!geoLayer) {
                    return;
                }
                if (checkbox.checked) {
                    map.addLayer(geoLayer);
                    reapplyZOrder();
                } else {
                    map.removeLayer(geoLayer);
                }
            });
        });

        // --- Opacidade por camada ---
        document.querySelectorAll(".layer-opacity").forEach(function (slider) {
            slider.addEventListener("input", function () {
                var layerName = slider.getAttribute("data-layer");
                var geoLayer = leafletLayersByName[layerName];
                if (!geoLayer) {
                    return;
                }
                var fraction = Number(slider.value) / 100;
                geoLayer.setStyle({ opacity: fraction, fillOpacity: fraction * 0.5 });
            });
        });

        // --- Reordenação (z-order) ---
        function reapplyZOrder() {
            // bringToFront empilha cada camada acima das anteriores, então
            // percorrer do fundo para a frente deixa a ordem final correta.
            zOrder.forEach(function (name) {
                var geoLayer = leafletLayersByName[name];
                if (geoLayer && map.hasLayer(geoLayer)) {
                    geoLayer.bringToFront();
                }
            });
        }

        function reorderRowsInDom() {
            var container = document.querySelector(".map-layers-toggle");
            if (!container) {
                return;
            }
            // Mostra a lista na mesma ordem do z-order, do topo (frente) para
            // baixo (fundo), para casar visualmente com o que se vê no mapa.
            zOrder.slice().reverse().forEach(function (name) {
                var row = container.querySelector('[data-layer-row="' + cssEscape(name) + '"]');
                if (row) {
                    container.appendChild(row);
                }
            });
        }

        function moveLayer(name, direction) {
            var index = zOrder.indexOf(name);
            if (index === -1) {
                return;
            }
            var targetIndex = direction === "up" ? index + 1 : index - 1;
            if (targetIndex < 0 || targetIndex >= zOrder.length) {
                return;
            }
            var tmp = zOrder[targetIndex];
            zOrder[targetIndex] = zOrder[index];
            zOrder[index] = tmp;
            reapplyZOrder();
            reorderRowsInDom();
        }

        document.querySelectorAll(".layer-order-btn").forEach(function (button) {
            button.addEventListener("click", function () {
                moveLayer(button.getAttribute("data-layer"), button.getAttribute("data-action"));
            });
        });

        reorderRowsInDom();
    });
})();
