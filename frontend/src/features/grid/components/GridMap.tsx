import React, { useMemo, useState, useEffect, useRef } from 'react';
import DeckGL from '@deck.gl/react';
import { ScatterplotLayer, PathLayer, IconLayer } from '@deck.gl/layers';
import { PathStyleExtension } from '@deck.gl/extensions';
import { WebMercatorViewport } from '@deck.gl/core';
import type { Node, Edge } from '../../../shared/types';

interface GridMapProps {
    nodes: Node[];
    edges: Edge[];
    onNodeClick: (node: Node, multiSelect: boolean) => void;
    onEdgeClick?: (edge: Edge, multiSelect: boolean) => void;
    highlightedNodes?: Set<string>;
    highlightedEdges?: Set<string>;
    selectedNodeIds?: string[];
    nodeAverages?: Record<string, number> | null;
    onMapClick?: () => void;
    voltageScale?: {
        criticalHigh: number;
        highWarning: number;
        lowWarning: number;
        criticalLow: number;
        baseVoltage: number;
    };
    fitHighlightedNodesTrigger?: number;
}
const stringToColor = (str: string): [number, number, number] => {
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
        hash = str.charCodeAt(i) + ((hash << 5) - hash);
    }
    // Generate subtle colors (hue, saturation ~50%, lightness ~60%)
    // Converted to simple RGB hash
    const c = (hash & 0x00FFFFFF).toString(16).toUpperCase();
    const hex = "00000".substring(0, 6 - c.length) + c;

    // Mix with gray to make it subtle
    const r = Math.floor((parseInt(hex.substring(0, 2), 16) + 150) / 2);
    const g = Math.floor((parseInt(hex.substring(2, 4), 16) + 150) / 2);
    const b = Math.floor((parseInt(hex.substring(4, 6), 16) + 150) / 2);

    return [r, g, b];
};

const getNodeColor = (type: string, isHighlighted: boolean, isSelected: boolean, circuitId?: string): [number, number, number] => {
    if (isSelected) return [255, 200, 50]; // Distinct gold/amber for the specifically selected node
    if (isHighlighted) return [60, 160, 240]; // Softer blue for downstream highlighted nodes

    if (circuitId && circuitId !== 'unknown') {
        return stringToColor(circuitId);
    }

    switch (type) {
        case 'SubstationBreaker':
        case 'Substation':
            return [255, 50, 50]; // Bright Red for Feeder Breaker
        case 'Transformer':
            return [100, 200, 255];
        case 'Meter':
            return [100, 255, 100];
        default:
            return [200, 200, 200];
    }
};

export const GridMap = React.memo<GridMapProps>(({
    nodes,
    edges,
    onNodeClick,
    onEdgeClick,
    highlightedNodes = new Set(),
    highlightedEdges = new Set(),
    selectedNodeIds = [],
    nodeAverages = null,
    onMapClick,
    voltageScale,
    fitHighlightedNodesTrigger = 0
}) => {
    const selectedNodeIdsSet = useMemo(() => new Set(selectedNodeIds), [selectedNodeIds]);
    const [mounted, setMounted] = useState(false);
    const [dimensions, setDimensions] = useState({ width: 0, height: 0 });

    const [viewState, setViewState] = useState<any>({
        longitude: -118.2437,
        latitude: 34.0522,
        zoom: 14,
        pitch: 0,
        bearing: 0
    });
    const [hoveredNodeId, setHoveredNodeId] = useState<string | null>(null);
    const [hoveredEdgeId, setHoveredEdgeId] = useState<string | null>(null);
    const [centered, setCentered] = useState(false);
    const lastHandledTrigger = useRef(0);

    useEffect(() => {
        if (!centered && nodes.length > 0) {
            const avgLon = nodes.reduce((sum, n) => sum + n.position[0], 0) / nodes.length;
            const avgLat = nodes.reduce((sum, n) => sum + n.position[1], 0) / nodes.length;
            setViewState((prev: any) => ({ ...prev, longitude: avgLon, latitude: avgLat }));
            setCentered(true);
        }
    }, [nodes, centered]);

    useEffect(() => {
        if (fitHighlightedNodesTrigger > 0 && 
            fitHighlightedNodesTrigger > lastHandledTrigger.current && 
            highlightedNodes.size > 0 && 
            dimensions.width > 0) {
            
            lastHandledTrigger.current = fitHighlightedNodesTrigger;
            
            const nodesToFit = nodes.filter(n => highlightedNodes.has(n.id));
            if (nodesToFit.length === 0) return;

            // Check if all highlighted nodes are already visible
            const viewport = new WebMercatorViewport({
                width: dimensions.width,
                height: dimensions.height,
                ...viewState
            });

            const allVisible = nodesToFit.every(n => {
                const [x, y] = viewport.project(n.position);
                // 10% padding check
                const paddingX = dimensions.width * 0.1;
                const paddingY = dimensions.height * 0.1;
                return (
                    x >= paddingX &&
                    x <= dimensions.width - paddingX &&
                    y >= paddingY &&
                    y <= dimensions.height - paddingY
                );
            });

            // If only one node is highlighted (e.g. from search), we ALWAYS want to zoom to it 
            // even if it's already visible, to provide clear feedback.
            if (allVisible && highlightedNodes.size > 1) {
                console.log('[GridMap] All nodes already visible, skipping zoom transition');
                return;
            }

            let minLon = Infinity, maxLon = -Infinity, minLat = Infinity, maxLat = -Infinity;
            nodesToFit.forEach(n => {
                const [lon, lat] = n.position;
                minLon = Math.min(minLon, lon);
                maxLon = Math.max(maxLon, lon);
                minLat = Math.min(minLat, lat);
                maxLat = Math.max(maxLat, lat);
            });

            // For a single point, fitBounds might not work as expected or zoom in too far/not enough.
            // We'll calculate target state directly or add a small offset.
            let targetLon, targetLat, targetZoom;

            if (nodesToFit.length === 1) {
                targetLon = nodesToFit[0].position[0];
                targetLat = nodesToFit[0].position[1];
                targetZoom = 17; // Good focus level
            } else {
                const bounds = viewport.fitBounds(
                    [[minLon, minLat], [maxLon, maxLat]],
                    {
                        padding: Math.min(dimensions.width, dimensions.height) * 0.1,
                        maxZoom: 18
                    }
                );
                targetLon = bounds.longitude;
                targetLat = bounds.latitude;
                targetZoom = bounds.zoom;
            }

            setViewState((prev: any) => ({
                ...prev,
                longitude: targetLon,
                latitude: targetLat,
                zoom: targetZoom,
                transitionDuration: 1000
            }));
        }
    }, [fitHighlightedNodesTrigger, highlightedNodes, nodes, dimensions]);

    useEffect(() => {
        setMounted(true);
        const updateSize = () => {
            setDimensions({
                width: window.innerWidth,
                height: window.innerHeight >= 500 ? window.innerHeight : 500
            });
        };
        updateSize();
        window.addEventListener('resize', updateSize);
        return () => window.removeEventListener('resize', updateSize);
    }, []);

    // Extract exactly where switches/breakers are so we can hide base nodes underneath them
    const switchPositions = useMemo(() => {
        const positions = new Set<string>();
        for (const n of nodes) {
            if (n.type === 'Switch' || n.type === 'Breaker') {
                positions.add(`${n.position[0].toFixed(6)},${n.position[1].toFixed(6)}`);
            }
        }
        return positions;
    }, [nodes]);

    const layers = useMemo(() => [
        new ScatterplotLayer({
            id: 'selection-halo',
            data: nodes.filter(n => selectedNodeIdsSet.has(n.id)),
            getPosition: (d: Node) => d.position,
            getFillColor: [255, 255, 255, 80], // Subtle soft white/gray halo
            getRadius: (d: Node) => {
                const baseRadius = d.type === 'Transformer' ? 6 : (d.type === 'Meter' || d.type === 'Bus' ? 5 : 10);
                return baseRadius * 1.1; // Slightly bigger (1.1x)
            },
            radiusUnits: 'pixels',
            radiusScale: Math.pow(1.5, (viewState.zoom || 14) - 14),
            radiusMinPixels: 2,
            pickable: false,
            updateTriggers: {
                getRadius: [selectedNodeIdsSet, viewState.zoom],
                getFillColor: [selectedNodeIdsSet]
            }
        }),
        new PathLayer({
            id: 'grid-lines',
            data: edges,
            getPath: (d: Edge) => [d.sourcePosition, d.targetPosition],
            getColor: (d: Edge) => {
                if (nodeAverages && nodeAverages[d.target] !== undefined && voltageScale) {
                    const voltage = nodeAverages[d.target];
                    const pu = voltage / (voltageScale.baseVoltage || 120);
                    // Soft coral for critical high
                    if (pu > voltageScale.criticalHigh) return [255, 107, 107, 200];
                    // Muted orange for high warning
                    if (pu >= voltageScale.highWarning) return [250, 150, 80, 200];
                    // Emerald green for low warning (since it's inverted from normal logic, this is 'in band' here)
                    if (pu >= voltageScale.lowWarning) return [46, 204, 113, 200];
                    // Soft gold for critical low (since it's warning)
                    if (pu >= voltageScale.criticalLow) return [241, 196, 15, 200];
                    // Periwinkle/Indigo for extreme low
                    return [142, 68, 173, 200];
                }
                if (highlightedEdges.has(d.id || '') || highlightedEdges.has(`${d.source}-${d.target}`)) return [60, 160, 240, 200];
                return d.circuit_id && d.circuit_id !== 'unknown' ? [...stringToColor(d.circuit_id), 120] as [number, number, number, number] : [150, 150, 150, 150];
            },
            getWidth: (d: Edge) => {
                const isHovered = (d.id && hoveredEdgeId === d.id) || hoveredEdgeId === `${d.source}-${d.target}`;
                if (isHovered) return 3;
                if (nodeAverages && nodeAverages[d.target] !== undefined) return 2;
                if (highlightedEdges.has(d.id || '') || highlightedEdges.has(`${d.source}-${d.target}`)) return 2;
                return 1;
            },
            widthUnits: 'pixels',
            getDashArray: (d: Edge) => {
                const count = d.phases ? d.phases.length : 3;
                if (count === 1) return [4, 4];
                if (count === 2) return [12, 6];
                return [0, 0];
            },
            dashJustified: true,
            extensions: [new PathStyleExtension({ dash: true })],
            pickable: true,
            autoHighlight: true,
            highlightColor: [255, 255, 255, 100],
            onHover: (info) => {
                setHoveredEdgeId(info.object ? (info.object.id || `${info.object.source}-${info.object.target}`) : null);
            },
            onClick: (info, event) => {
                const srcEvent = (event as any).srcEvent as MouseEvent;
                if (info.object && srcEvent && onEdgeClick) {
                    onEdgeClick(info.object as Edge, srcEvent.shiftKey || srcEvent.ctrlKey);
                }
            },
            updateTriggers: {
                getColor: [highlightedEdges, nodeAverages, voltageScale],
                getWidth: [highlightedEdges, hoveredEdgeId, nodeAverages]
            }
        }),
        new ScatterplotLayer({
            id: 'grid-nodes',
            data: nodes.filter(n => {
                if (n.type === 'Switch' || n.type === 'Breaker' || n.type === 'Transformer') return false;
                // Hide buses that overlap completely with switches/breakers
                const posKey = `${n.position[0].toFixed(6)},${n.position[1].toFixed(6)}`;
                if (switchPositions.has(posKey)) return false;
                return true;
            }),
            getPosition: (d: Node) => d.position,
            getFillColor: (d: Node) => {
                if (selectedNodeIdsSet.has(d.id)) return [255, 200, 50, 255];

                if (nodeAverages && nodeAverages[d.id] !== undefined && voltageScale) {
                    const voltage = nodeAverages[d.id];
                    const pu = voltage / (voltageScale.baseVoltage || 120);
                    // Soft coral for critical high
                    if (pu > voltageScale.criticalHigh) return [255, 107, 107, 200];
                    // Muted orange for high warning
                    if (pu >= voltageScale.highWarning) return [250, 150, 80, 200];
                    // Emerald green for low warning (since it's inverted from normal logic, this is 'in band' here)
                    if (pu >= voltageScale.lowWarning) return [46, 204, 113, 200];
                    // Soft gold for critical low (since it's warning)
                    if (pu >= voltageScale.criticalLow) return [241, 196, 15, 200];
                    // Periwinkle/Indigo for extreme low
                    return [142, 68, 173, 200];
                }

                const color = getNodeColor(d.type, highlightedNodes.has(d.id), false, d.circuit_id);
                return [color[0], color[1], color[2], 255];
            },
            getRadius: (d: Node) => {
                const isHovered = hoveredNodeId === d.id;
                const isHighlighted = highlightedNodes.has(d.id);
                const isSelected = selectedNodeIdsSet.has(d.id);
                // Transformer takes old Bus size (4). Bus takes Meter size (3).
                const baseRadius = d.type === 'Transformer' ? 4 : (d.type === 'Meter' || d.type === 'Bus' ? 3 : 8);
                let radius = isHovered ? baseRadius * 2.5 : baseRadius;
                if (isHighlighted) radius = radius * 1.5;
                if (isSelected) radius = radius * 1.1; // Make the specifically selected node slightly larger
                return radius;
            },
            updateTriggers: {
                getRadius: [hoveredNodeId, highlightedNodes, selectedNodeIdsSet],
                getFillColor: [highlightedNodes, selectedNodeIdsSet, nodeAverages, voltageScale]
            },
            radiusUnits: 'pixels',
            radiusScale: Math.pow(1.5, (viewState.zoom || 14) - 14),
            radiusMinPixels: 1,
            pickable: true,
            autoHighlight: true,
            highlightColor: [255, 255, 255, 50],
            onHover: (info) => {
                setHoveredNodeId(info.object ? info.object.id : null);
            },
            onClick: (info, event) => {
                const srcEvent = (event as any).srcEvent as MouseEvent;
                console.log('[GridMap] Interaction:', info.object?.id, 'Shift:', srcEvent?.shiftKey);
                if (info.object && srcEvent) {
                    onNodeClick(info.object, srcEvent.shiftKey || srcEvent.ctrlKey);
                }
            }
        }),
        new IconLayer({
            id: 'grid-switches-open',
            data: nodes.filter(n => (n.type === 'Switch' || n.type === 'Breaker') && n.is_open),
            getPosition: (d: Node) => d.position,
            iconAtlas: '/open-switch.svg',
            iconMapping: {
                marker: { x: 0, y: 0, width: 100, height: 100, anchorY: 50, mask: false }
            },
            getIcon: () => 'marker',
            getSize: (d: Node) => {
                const isSelected = selectedNodeIdsSet.has(d.id);
                return isSelected ? 36 : 24;
            },
            sizeScale: Math.pow(1.5, (viewState.zoom || 14) - 14),
            sizeMinPixels: 1,
            updateTriggers: {
                getSize: [selectedNodeIdsSet]
            },
            pickable: true,
            autoHighlight: false,
            onHover: (info) => {
                setHoveredNodeId(info.object ? info.object.id : null);
            },
            onClick: (info, event) => {
                const srcEvent = (event as any).srcEvent as MouseEvent;
                console.log('[GridMap] Interaction:', info.object?.id, 'Shift:', srcEvent?.shiftKey);
                if (info.object && srcEvent) {
                    onNodeClick(info.object, srcEvent.shiftKey || srcEvent.ctrlKey);
                }
            }
        }),
        new IconLayer({
            id: 'grid-switches-closed',
            data: nodes.filter(n => (n.type === 'Switch' || n.type === 'Breaker') && !n.is_open),
            getPosition: (d: Node) => d.position,
            iconAtlas: '/close-switch.svg',
            iconMapping: {
                marker: { x: 0, y: 0, width: 100, height: 100, anchorY: 50, mask: false }
            },
            getIcon: () => 'marker',
            getSize: (d: Node) => {
                const isSelected = selectedNodeIdsSet.has(d.id);
                return isSelected ? 36 : 24;
            },
            sizeScale: Math.pow(1.5, (viewState.zoom || 14) - 14),
            sizeMinPixels: 1,
            updateTriggers: {
                getSize: [selectedNodeIdsSet]
            },
            pickable: true,
            autoHighlight: false,
            onHover: (info) => {
                setHoveredNodeId(info.object ? info.object.id : null);
            },
            onClick: (info, event) => {
                const srcEvent = (event as any).srcEvent as MouseEvent;
                console.log('[GridMap] Interaction:', info.object?.id, 'Shift:', srcEvent?.shiftKey);
                if (info.object && srcEvent) {
                    onNodeClick(info.object, srcEvent.shiftKey || srcEvent.ctrlKey);
                }
            }
        }),
        new IconLayer({
            id: 'grid-transformers',
            data: nodes.filter(n => n.type === 'Transformer'),
            getPosition: (d: Node) => d.position,
            iconAtlas: '/transformer.svg',
            iconMapping: {
                marker: { x: 0, y: 0, width: 100, height: 100, anchorY: 50, mask: false }
            },
            getIcon: () => 'marker',
            getSize: (d: Node) => {
                const isSelected = selectedNodeIdsSet.has(d.id);
                return isSelected ? 9 : 8;
            },
            sizeScale: Math.pow(1.5, (viewState.zoom || 14) - 14),
            sizeMinPixels: 1,
            updateTriggers: {
                getSize: [selectedNodeIdsSet]
            },
            pickable: true,
            autoHighlight: false,
            onHover: (info) => {
                setHoveredNodeId(info.object ? info.object.id : null);
            },
            onClick: (info, event) => {
                const srcEvent = (event as any).srcEvent as MouseEvent;
                console.log('[GridMap] Interaction:', info.object?.id, 'Shift:', srcEvent?.shiftKey);
                if (info.object && srcEvent) {
                    onNodeClick(info.object, srcEvent.shiftKey || srcEvent.ctrlKey);
                }
            }
        })
    ], [nodes, edges, hoveredNodeId, hoveredEdgeId, highlightedNodes, highlightedEdges, selectedNodeIdsSet, switchPositions, nodeAverages, voltageScale, onNodeClick, onEdgeClick, viewState.zoom]);

    return (
        <div
            style={{ position: 'relative', width: '100vw', height: '100vh', minHeight: '500px', background: '#141517' }}
        >
            {mounted && dimensions.width > 0 && dimensions.height > 0 && (
                <DeckGL
                    width={dimensions.width}
                    height={dimensions.height}
                    useDevicePixels={false}
                    onWebGLInitialized={(gl) => {
                        if (!gl) console.error("WebGL context failed to initialize.");
                    }}
                    initialViewState={viewState}
                    viewState={viewState}
                    onViewStateChange={({ viewState }) => setViewState(viewState)}
                    onDragStart={() => {
                        // We track drag starts but don't block them with 'return false'
                        // as that can interfere with click propagation in some environments
                    }}
                    getCursor={({ isHovering }) => isHovering ? 'pointer' : 'grabbing'}
                    onClick={(info) => {
                        if (!info.object && onMapClick) {
                            console.log('[GridMap] Background click - clearing selection');
                            onMapClick();
                        }
                    }}
                    controller={{
                        dragRotate: false,
                        doubleClickZoom: true,
                        touchRotate: false
                    }}
                    layers={layers}
                    getTooltip={({ object }) => {
                        if (!object) return null;
                        if ('type' in object) {
                            return {
                                html: `
                                <div style="padding: 10px; background: #25262b; border: 1px solid #373A40; border-radius: 8px; color: #fff;">
                                <strong>ID:</strong> ${object.id}<br/>
                                <strong>Type:</strong> ${object.type}<br/>
                                <strong>Name:</strong> ${object.name}
                                </div>
                            `,
                                style: { backgroundColor: 'transparent', fontSize: '13px' }
                            };
                        } else {
                            return {
                                html: `
                                <div style="padding: 10px; background: #25262b; border: 1px solid #373A40; border-radius: 8px; color: #fff;">
                                <strong>ID:</strong> ${object.id || `${object.source}-${object.target}`}<br/>
                                <strong>Type:</strong> Edge<br/>
                                <strong>Phases:</strong> ${object.phases ? object.phases.join('') : 'ABC'}
                                </div>
                            `,
                                style: { backgroundColor: 'transparent', fontSize: '13px' }
                            };
                        }
                    }}
                />
            )}
        </div>
    );
});
