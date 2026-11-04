/**
 * Editor dinâmico de geometria GeoJSON.
 *
 * Substitui a edição de coordenadas como texto JSON cru por campos numéricos
 * (lon/lat) organizados conforme o tipo escolhido no <select>. O resultado é
 * sempre serializado para o campo hidden `_geometry`, mantendo o contrato já
 * esperado pelo backend (services.py -> prepare_incoming).
 *
 * Tipos com coordinates aninhadas (profundidade em relação a um par [lon, lat]):
 *   Point            -> 0 (o próprio par)
 *   LineString       -> 1 (lista de pares)
 *   MultiPoint       -> 1 (lista de pares)
 *   Polygon          -> 2 (lista de anéis, cada anel é uma lista de pares)
 *   MultiLineString  -> 2 (lista de linhas, cada linha é uma lista de pares)
 *   MultiPolygon     -> 3 (lista de polígonos, cada um lista de anéis)
 *
 * GeometryCollection não segue esse padrão (usa "geometries" em vez de
 * "coordinates"), então cai automaticamente no modo de edição via JSON bruto.
 */
(function () {
    "use strict";

    var DEPTH_BY_TYPE = {
        Point: 0,
        LineString: 1,
        MultiPoint: 1,
        Polygon: 2,
        MultiLineString: 2,
        MultiPolygon: 3,
    };

    function defaultLeafPair() {
        return [0, 0];
    }

    function defaultForDepth(depth) {
        if (depth === 0) return defaultLeafPair();
        if (depth === 1) return [defaultLeafPair()];
        return [defaultForDepth(depth - 1)];
    }

    function subLabel(depth) {
        if (depth === 3) return "Polígono";
        if (depth === 2) return "Anel";
        return "Linha";
    }

    function initGeometryEditor(root) {
        var typeSelect = root.querySelector("[data-geom-type]");
        var editorContainer = root.querySelector("[data-geom-editor]");
        var rawContainer = root.querySelector("[data-geom-raw]");
        var rawTextarea = root.querySelector("[data-geom-raw-textarea]");
        var hiddenInput = root.querySelector("[data-geom-hidden]");
        var toggleRawBtn = root.querySelector("[data-geom-toggle-raw]");
        var initialScript = document.getElementById("geom-initial-data");

        var initial = {};
        if (initialScript) {
            try {
                initial = JSON.parse(initialScript.textContent || "{}") || {};
            } catch (e) {
                initial = {};
            }
        }

        var state = {
            type: initial.type || "Point",
            coordinates: initial.coordinates,
            rawMode: false,
        };

        if (Object.prototype.hasOwnProperty.call(DEPTH_BY_TYPE, state.type)) {
            if (state.coordinates === undefined || state.coordinates === null) {
                state.coordinates = defaultForDepth(DEPTH_BY_TYPE[state.type]);
            }
        } else {
            // GeometryCollection ou tipo desconhecido: edição via JSON bruto.
            state.rawMode = true;
            rawTextarea.value = JSON.stringify(initial, null, 2);
        }

        function serialize() {
            if (state.rawMode) {
                try {
                    var parsed = JSON.parse(rawTextarea.value || "null");
                    hiddenInput.value = parsed === null ? "" : JSON.stringify(parsed);
                } catch (e) {
                    // Mantém o texto como está; o backend reporta o erro de JSON inválido.
                    hiddenInput.value = rawTextarea.value;
                }
                return;
            }
            hiddenInput.value = JSON.stringify({ type: state.type, coordinates: state.coordinates });
        }

        function numberInput(value, onChange) {
            var input = document.createElement("input");
            input.type = "number";
            input.step = "any";
            input.value = value;
            input.addEventListener("input", function () {
                onChange(input.value === "" ? 0 : parseFloat(input.value));
                serialize();
            });
            return input;
        }

        function pairRow(pair, onRemove) {
            var row = document.createElement("div");
            row.className = "geom-pair";

            var lonLabel = document.createElement("label");
            lonLabel.textContent = "lon";
            lonLabel.appendChild(numberInput(pair[0], function (v) { pair[0] = v; }));

            var latLabel = document.createElement("label");
            latLabel.textContent = "lat";
            latLabel.appendChild(numberInput(pair[1], function (v) { pair[1] = v; }));

            row.appendChild(lonLabel);
            row.appendChild(latLabel);

            if (onRemove) {
                var removeBtn = document.createElement("button");
                removeBtn.type = "button";
                removeBtn.className = "geom-remove";
                removeBtn.textContent = "Remover ponto";
                removeBtn.addEventListener("click", onRemove);
                row.appendChild(removeBtn);
            }
            return row;
        }

        function listGroup(list, depth, onRemoveSelf) {
            var group = document.createElement("fieldset");
            group.className = "geom-group";

            list.forEach(function (item, index) {
                if (depth === 1) {
                    group.appendChild(pairRow(item, function () {
                        list.splice(index, 1);
                        rerenderEditor();
                    }));
                } else {
                    group.appendChild(listGroup(item, depth - 1, function () {
                        list.splice(index, 1);
                        rerenderEditor();
                    }));
                }
            });

            var addBtn = document.createElement("button");
            addBtn.type = "button";
            addBtn.className = "geom-add";
            addBtn.textContent = depth === 1 ? "+ ponto" : "+ " + subLabel(depth).toLowerCase();
            addBtn.addEventListener("click", function () {
                list.push(depth === 1 ? defaultLeafPair() : defaultForDepth(depth - 1));
                rerenderEditor();
            });
            group.appendChild(addBtn);

            if (onRemoveSelf) {
                var legend = document.createElement("legend");
                legend.textContent = subLabel(depth + 1);
                group.insertBefore(legend, group.firstChild);

                var removeBtn = document.createElement("button");
                removeBtn.type = "button";
                removeBtn.className = "geom-remove geom-remove-group";
                removeBtn.textContent = "Remover " + subLabel(depth + 1).toLowerCase();
                removeBtn.addEventListener("click", onRemoveSelf);
                group.appendChild(removeBtn);
            }

            return group;
        }

        function rerenderEditor() {
            editorContainer.innerHTML = "";

            if (state.rawMode) {
                editorContainer.hidden = true;
                rawContainer.hidden = false;
                serialize();
                return;
            }

            editorContainer.hidden = false;
            rawContainer.hidden = true;

            var depth = DEPTH_BY_TYPE[state.type];
            if (depth === 0) {
                editorContainer.appendChild(pairRow(state.coordinates, null));
            } else {
                editorContainer.appendChild(listGroup(state.coordinates, depth, null));
            }
            serialize();
        }

        typeSelect.addEventListener("change", function () {
            state.type = typeSelect.value;
            if (Object.prototype.hasOwnProperty.call(DEPTH_BY_TYPE, state.type)) {
                state.rawMode = false;
                state.coordinates = defaultForDepth(DEPTH_BY_TYPE[state.type]);
            } else {
                state.rawMode = true;
                rawTextarea.value = JSON.stringify({ type: state.type, geometries: [] }, null, 2);
            }
            rerenderEditor();
        });

        if (toggleRawBtn) {
            toggleRawBtn.addEventListener("click", function () {
                if (!state.rawMode) {
                    rawTextarea.value = JSON.stringify(
                        { type: state.type, coordinates: state.coordinates },
                        null,
                        2
                    );
                    state.rawMode = true;
                    toggleRawBtn.textContent = "Editar com campos de coordenadas";
                } else {
                    try {
                        var parsed = JSON.parse(rawTextarea.value);
                        if (parsed && typeof parsed.type === "string") {
                            state.type = parsed.type;
                        }
                        if (parsed && parsed.coordinates !== undefined) {
                            state.coordinates = parsed.coordinates;
                        }
                    } catch (e) {
                        // JSON inválido: mantém o estado anterior e permanece em modo bruto.
                        return;
                    }
                    if (Object.prototype.hasOwnProperty.call(DEPTH_BY_TYPE, state.type)) {
                        state.rawMode = false;
                        typeSelect.value = state.type;
                        toggleRawBtn.textContent = "Editar como JSON bruto";
                    }
                }
                rerenderEditor();
            });
        }

        rawTextarea.addEventListener("input", serialize);

        if (Object.prototype.hasOwnProperty.call(DEPTH_BY_TYPE, state.type)) {
            typeSelect.value = state.type;
        }
        rerenderEditor();
    }

    document.addEventListener("DOMContentLoaded", function () {
        var root = document.querySelector("[data-geom-root]");
        if (root) {
            initGeometryEditor(root);
        }
    });
})();
