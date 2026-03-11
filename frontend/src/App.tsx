import '@mantine/core/styles.css';
import '@mantine/dates/styles.css';
import { useState, useEffect, useCallback } from 'react';
import { MantineProvider, AppShell, Box, Stack } from '@mantine/core';

import { GridMap } from './features/grid/components/GridMap';
import { GridExplorerPanel } from './features/grid/components/GridExplorerPanel';
import { GridContextMenu } from './features/grid/components/GridContextMenu';
import { AnalyticsPanel } from './features/analytics/components/AnalyticsPanel';
import { ConsumptionTimeSeriesModal } from './features/analytics/components/ConsumptionTimeSeriesModal';
import { VoltageDistributionModal } from './features/analytics/components/VoltageDistributionModal';
import { NaturalLanguagePanel } from './features/agent/components/NaturalLanguagePanel';
import { VoltageScalePanel } from './features/analytics/components/VoltageScalePanel';

import { fetchTopology, fetchConsumption, nlQuery, fetchVoltageDistribution, fetchMapVoltage } from './shared/api';
import type { Node, Edge } from './shared/types';

export default function App() {
  const [nodes, setNodes] = useState<Node[]>([]);
  const [edges, setEdges] = useState<Edge[]>([]);
  const [selectedNode, setSelectedNode] = useState<Node | null>(null);

  const [dateRange, setDateRange] = useState({
    start: '2025-01-01T00:00:00',
    end: '2025-02-01T00:00:00'
  });


  const [loading, setLoading] = useState(false);
  const [nlResult, setNlResult] = useState<string>('');
  const [query, setQuery] = useState('');

  const [consumptionModalOpen, setConsumptionModalOpen] = useState(false);
  const [consumptionData, setConsumptionData] = useState<any[]>([]);
  const [consumptionLoading, setConsumptionLoading] = useState(false);

  const [voltageModalOpen, setVoltageModalOpen] = useState(false);
  const [voltageData, setVoltageData] = useState<any[]>([]);
  const [voltageScatterData, setVoltageScatterData] = useState<any[]>([]);
  const [voltageLoading, setVoltageLoading] = useState(false);
  const [voltageDegrees, setVoltageDegrees] = useState<number | null>(5);
  const [voltageTimeSeries, setVoltageTimeSeries] = useState<any[]>([]);

  const [highlightedNodes, setHighlightedNodes] = useState<Set<string>>(new Set());
  const [highlightedEdges, setHighlightedEdges] = useState<Set<string>>(new Set());
  const [nodeAverages, setNodeAverages] = useState<Record<string, number> | null>(null);

  const [voltageScale, setVoltageScale] = useState(() => {
    const saved = localStorage.getItem('voltageScale');
    if (saved) {
      try {
        return JSON.parse(saved);
      } catch (e) {
        console.error('Failed to parse saved voltageScale', e);
      }
    }
    return {
      criticalHigh: 1.06,
      highWarning: 1.05,
      lowWarning: 0.95,
      criticalLow: 0.90,
      baseVoltage: 120
    };
  });

  useEffect(() => {
    localStorage.setItem('voltageScale', JSON.stringify(voltageScale));
  }, [voltageScale]);

  const [contextMenu, setContextMenu] = useState<{ x: number, y: number, item: any, type: 'node' | 'edge' } | null>(null);

  const handleCloseConsumptionModal = useCallback(() => setConsumptionModalOpen(false), []);
  const handleCloseVoltageModal = useCallback(() => setVoltageModalOpen(false), []);
  const handleClearSelection = useCallback(() => setSelectedNode(null), []);
  const handleCloseContextMenu = useCallback(() => setContextMenu(null), []);


  useEffect(() => {
    fetchTopology()
      .then(data => {
        setNodes(data.nodes);
        setEdges(data.edges);
        if (data.nodes.length === 0) {
          console.warn('[App] Topology returned 0 nodes');
        }
      })
      .catch(err => console.error('[App] Failed to fetch topology:', err));
  }, []);



  const handleRunVoltageMap = async (agg: string) => {
    setLoading(true);
    try {
      const res = await fetchMapVoltage(dateRange.start, dateRange.end, agg, selectedNode?.id || null);
      if (res.node_voltages) {
        setNodeAverages(res.node_voltages);
        // We highlight the area if a specific node was queried
        if (selectedNode) {
          const keys = Object.keys(res.node_voltages);
          setHighlightedNodes(new Set(keys));
          // For map voltage we don't have explicit edges yet in the same way, 
          // but we can clear them or try to infer. Let's clear for now.
          setHighlightedEdges(new Set());
        } else {
          setHighlightedNodes(new Set());
          setHighlightedEdges(new Set());
        }
      }
    } catch (err) {
      console.error('[App] Failed to fetch map voltage overlay:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleShowConsumption = async (rangeOption?: '1W' | '1M' | '1Y', overrideNode?: Node) => {
    const node = overrideNode || selectedNode;
    if (!node) return;
    setSelectedNode(node);

    let start = dateRange.start;
    let end = dateRange.end;

    if (rangeOption) {
      const endDate = new Date();
      const startDate = new Date();
      if (rangeOption === '1W') startDate.setDate(startDate.getDate() - 7);
      if (rangeOption === '1M') startDate.setMonth(startDate.getMonth() - 1);
      if (rangeOption === '1Y') startDate.setFullYear(startDate.getFullYear() - 1);

      start = startDate.toISOString().split('.')[0];
      end = endDate.toISOString().split('.')[0];
      setDateRange({ start, end });
    }

    setVoltageModalOpen(false);
    setConsumptionData([]);
    setNodeAverages(null);
    setConsumptionLoading(true);
    setConsumptionModalOpen(true);
    try {
      const res = await fetchConsumption(node.id, start, end);
      if (res.downstream_node_ids) {
        setHighlightedNodes(new Set(res.downstream_node_ids));
      } else {
        setHighlightedNodes(new Set());
      }
      if (res.downstream_edge_ids) {
        setHighlightedEdges(new Set(res.downstream_edge_ids));
      } else {
        setHighlightedEdges(new Set());
      }
      if (res.time_series && res.time_series.length > 0) {
        setConsumptionData(res.time_series);
      }
    } catch (err) {
      console.error('[App] Failed to fetch consumption:', err);
    } finally {
      setConsumptionLoading(false);
    }
  };

  const handleShowVoltageDistribution = async (rangeOption?: '1W' | '1M' | '1Y', overrideNode?: Node, degrees?: number | null) => {
    const node = overrideNode || selectedNode;
    if (!node) return;
    setSelectedNode(node);

    let start = dateRange.start;
    let end = dateRange.end;

    if (rangeOption) {
      const endDate = new Date();
      const startDate = new Date();
      if (rangeOption === '1W') startDate.setDate(startDate.getDate() - 7);
      if (rangeOption === '1M') startDate.setMonth(startDate.getMonth() - 1);
      if (rangeOption === '1Y') startDate.setFullYear(startDate.getFullYear() - 1);

      start = startDate.toISOString().split('.')[0];
      end = endDate.toISOString().split('.')[0];
      setDateRange({ start, end });
    }

    setConsumptionModalOpen(false);
    setVoltageData([]);
    setVoltageScatterData([]);
    setNodeAverages(null);
    setVoltageLoading(true);
    setVoltageModalOpen(true);
    const degreesToUse = degrees !== undefined ? degrees : voltageDegrees;
    setVoltageDegrees(degreesToUse);
    try {
      const res = await fetchVoltageDistribution(node.id, start, end, degreesToUse === null ? undefined : degreesToUse);
      if (res.downstream_node_ids) {
        setHighlightedNodes(new Set(res.downstream_node_ids));
      } else {
        setHighlightedNodes(new Set());
      }
      if (res.downstream_edge_ids) {
        setHighlightedEdges(new Set(res.downstream_edge_ids));
      } else {
        setHighlightedEdges(new Set());
      }
      if (res.distribution) {
        setVoltageData(res.distribution.map((d: any) => ({
          voltage: d.voltage.toString() + 'V',
          a: d.phase_a,
          b: d.phase_b,
          c: d.phase_c,
        })));
      }
      if (res.scatter) {
        const maxCount = Math.max(...res.scatter.map((d: any) => d.count || 1), 1);
        setVoltageScatterData([
          {
            color: 'cyan.6',
            name: 'Voltage vs Loading Density',
            data: res.scatter.map((d: any) => ({
              x: d.loading,
              y: d.voltage,
              count: d.count || 1,
              maxCount: maxCount
            }))
          }
        ]);
      }
      if (res.node_averages) {
        setNodeAverages(res.node_averages);
      }
      if (res.timeseries) {
        setVoltageTimeSeries(res.timeseries);
      }
    } catch (err) {
      console.error('[App] Failed to fetch voltage distribution:', err);
    } finally {
      setVoltageLoading(false);
    }
  };

  const handleNlQuery = async () => {
    try {
      const res = await nlQuery(query);
      setNlResult(res.generated_prompt);
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <MantineProvider defaultColorScheme="dark">
      <AppShell padding="0" header={{ height: 0 }}>
        <AppShell.Main>

          {/* Deck.GL Interactive Grid Map */}
          <Box style={{ position: 'absolute', inset: 0, zIndex: 0 }}>
            <GridMap
              nodes={nodes}
              edges={edges}
              onNodeClick={setSelectedNode}
              onNodeRightClick={(node, x, y) => setContextMenu({ x, y, item: node, type: 'node' })}
              onEdgeRightClick={(edge, x, y) => setContextMenu({ x, y, item: edge, type: 'edge' })}
              highlightedNodes={highlightedNodes}
              highlightedEdges={highlightedEdges}
              selectedNodeId={selectedNode?.id}
              nodeAverages={nodeAverages}
              voltageScale={voltageScale}
            />
          </Box>

          {/* Right-Click Context Menu */}
          <GridContextMenu
            contextMenu={contextMenu}
            nodes={nodes}
            onClose={handleCloseContextMenu}
            onShowConsumption={handleShowConsumption}
            onShowVoltage={handleShowVoltageDistribution}
          />

          {/* Persistent Overlay Panels */}
          <VoltageScalePanel
            voltageScale={voltageScale}
            setVoltageScale={setVoltageScale}
            visible={!!nodeAverages}
          />

          <Box
            style={{ position: 'absolute', top: 20, right: 20, zIndex: 10, pointerEvents: 'none' }}
            w={{ base: 'calc(100vw - 40px)', sm: 400 }}
          >
            <Stack gap="16px">
              <div style={{ pointerEvents: 'auto' }}>
                <GridExplorerPanel
                  nodeCount={nodes.filter(n => n.type === 'Meter').length}
                  selectedNode={selectedNode}
                  onClearSelection={handleClearSelection}
                  onViewConsumption={handleShowConsumption}
                />
              </div>

              <div style={{ pointerEvents: 'auto' }}>
                <AnalyticsPanel
                  dateRange={dateRange}
                  setDateRange={setDateRange}
                  loading={loading}
                  onRunVoltageMap={handleRunVoltageMap}
                />
              </div>

              <div style={{ pointerEvents: 'auto' }}>
                <NaturalLanguagePanel
                  query={query}
                  setQuery={setQuery}
                  onNlQuery={handleNlQuery}
                  nlResult={nlResult}
                />
              </div>
            </Stack>
          </Box>

          {/* Full Width Bottom Modals */}
          <ConsumptionTimeSeriesModal
            isOpen={consumptionModalOpen}
            onClose={handleCloseConsumptionModal}
            loading={consumptionLoading}
            data={consumptionData}
            nodeName={selectedNode?.name || selectedNode?.id}
          />

          <VoltageDistributionModal
            isOpen={voltageModalOpen}
            onClose={handleCloseVoltageModal}
            loading={voltageLoading}
            data={voltageData}
            scatterData={voltageScatterData}
            timeSeriesData={voltageTimeSeries}
            nodeName={selectedNode?.name}
            degrees={voltageDegrees}
            onDegreesChange={(d: number | null) => handleShowVoltageDistribution(undefined, undefined, d)}
          />

        </AppShell.Main>
      </AppShell>
    </MantineProvider >
  );
}
