import '@mantine/core/styles.css';
import '@mantine/dates/styles.css';
import { useState, useEffect, useCallback } from 'react';
import { MantineProvider, AppShell, Box, Stack, ActionIcon, Menu, Group, Tooltip } from '@mantine/core';
import { Menu as MenuIcon, X, Search, Activity, Settings } from 'lucide-react';

import { GridMap } from './features/grid/components/GridMap';
import { AnalysisToolbar } from './features/grid/components/AnalysisToolbar';
import { GridContextMenu } from './features/grid/components/GridContextMenu';
import { AnalyticsPanel } from './features/analytics/components/AnalyticsPanel';
import { ConsumptionTimeSeriesModal } from './features/analytics/components/ConsumptionTimeSeriesModal';
import { VoltageDistributionModal } from './features/analytics/components/VoltageDistributionModal';
import { VoltageScalePanel } from './features/analytics/components/VoltageScalePanel';
import { GlobalSettingsModal, type GlobalConfig } from './features/analytics/components/GlobalSettingsModal';
import {
  fetchTopology,
  fetchConsumption,
  fetchVoltageDistribution,
  fetchMapVoltage,
  fetchVoltageEstimate,
  fetchConsumptionEstimate,
  fetchMapVoltageEstimate
} from './shared/api';
import type { Node, Edge } from './shared/types';

const DEFAULT_CONFIG: GlobalConfig = {
  defaultDuration: '1M',
  customDays: 30,
  endDateType: 'now',
  fixedEndDate: new Date().toISOString()
};

const calculateRange = (config: GlobalConfig) => {
  const end = config.endDateType === 'now' ? new Date() : new Date(config.fixedEndDate);
  const start = new Date(end.getTime());

  const duration = config.defaultDuration || '1M';

  if (duration === '1D') {
    start.setDate(end.getDate() - 1);
  } else if (duration === '1W') {
    start.setDate(end.getDate() - 7);
  } else if (duration === '1M') {
    start.setMonth(end.getMonth() - 1);
  } else if (duration === '1Y') {
    start.setFullYear(end.getFullYear() - 1);
  } else if (duration === 'custom') {
    start.setDate(end.getDate() - (config.customDays || 30));
  } else {
    start.setMonth(end.getMonth() - 1);
  }

  // Final check for zero duration (edge case where math fails)
  if (start.getTime() === end.getTime()) {
    console.warn('[App] Range calculation resulted in zero duration! Falling back to 1M.');
    start.setMonth(end.getMonth() - 1);
  }

  return {
    start: start.toISOString().split('.')[0],
    end: end.toISOString().split('.')[0]
  };
};

export default function App() {
  const [nodes, setNodes] = useState<Node[]>([]);
  const [edges, setEdges] = useState<Edge[]>([]);
  const [selectedNodes, setSelectedNodes] = useState<Node[]>([]);

  const [globalConfig, setGlobalConfig] = useState<GlobalConfig>(() => {
    const saved = localStorage.getItem('globalConfig');
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        // Merge with DEFAULT_CONFIG to ensure new fields (like endDateType) are present
        return { ...DEFAULT_CONFIG, ...parsed };
      } catch (e) {
        console.error('Failed to parse saved globalConfig', e);
      }
    }
    return DEFAULT_CONFIG;
  });

  const [dateRange, setDateRange] = useState(() => calculateRange(globalConfig));
  const [settingsOpen, setSettingsOpen] = useState(false);

  useEffect(() => {
    localStorage.setItem('globalConfig', JSON.stringify(globalConfig));
    // When config changes, we might want to refresh the dateRange if it's "now" based
    if (globalConfig.endDateType === 'now') {
      setDateRange(calculateRange(globalConfig));
    }
  }, [globalConfig]);

  const [activeSidePanel, setActiveSidePanel] = useState<'none' | 'analytics'>('none');
  const [loading, setLoading] = useState(false);
  const [mapVoltageEstimatedRows, setMapVoltageEstimatedRows] = useState<number | undefined>();

  const [consumptionModalOpen, setConsumptionModalOpen] = useState(false);
  const [consumptionData, setConsumptionData] = useState<any[]>([]);
  const [consumptionEstimatedRows, setConsumptionEstimatedRows] = useState<number | undefined>();
  const [consumptionLoading, setConsumptionLoading] = useState(false);

  const [voltageModalOpen, setVoltageModalOpen] = useState(false);
  const [voltageData, setVoltageData] = useState<any[]>([]);
  const [voltageScatterData, setVoltageScatterData] = useState<any[]>([]);
  const [voltageLoading, setVoltageLoading] = useState(false);
  const [voltageEstimatedRows, setVoltageEstimatedRows] = useState<number | undefined>();
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
  const handleClearSelection = useCallback(() => setSelectedNodes([]), []);
  const handleCloseContextMenu = useCallback(() => setContextMenu(null), []);

  const onNodeClick = useCallback((node: Node, multiSelect: boolean) => {
    console.log('[App] onNodeClick:', node.id, 'multiSelect:', multiSelect);
    setSelectedNodes(prev => {
      if (!multiSelect) return [node];
      const exists = prev.find(n => n.id === node.id);
      if (exists) return prev.filter(n => n.id !== node.id);
      return [...prev, node];
    });
  }, []);

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
    setMapVoltageEstimatedRows(undefined);

    const firstNodeId = selectedNodes.length > 0 ? selectedNodes[0].id : null;

    // Fetch estimate separately to unblock the loading UI
    fetchMapVoltageEstimate(dateRange.start, dateRange.end, agg, firstNodeId)
      .then(res => setMapVoltageEstimatedRows(res.estimated_rows))
      .catch(err => console.error('[App] Map estimate failed:', err));

    try {
      const res = await fetchMapVoltage(dateRange.start, dateRange.end, agg, firstNodeId);

      if (res.estimated_rows !== undefined) {
        setMapVoltageEstimatedRows(res.estimated_rows);
      }

      if (res.node_voltages) {
        setNodeAverages(res.node_voltages);
        // We highlight the area if a specific node was queried
        if (firstNodeId) {
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

  const handleShowConsumption = async (rangeOption?: string, overrideNode?: Node) => {
    const nodesToQuery = overrideNode ? [overrideNode] : selectedNodes;
    if (nodesToQuery.length === 0) return;
    if (overrideNode) setSelectedNodes([overrideNode]);

    const range = calculateRange(globalConfig);
    let start = range.start;
    let end = range.end;
    if (globalConfig.endDateType === 'now') {
      setDateRange(range);
    }

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
    setConsumptionEstimatedRows(undefined);
    setNodeAverages(null);
    setConsumptionLoading(true);
    setConsumptionModalOpen(true);

    const nodeIds = nodesToQuery.map(n => n.id);

    // Fetch estimate separately to update the progress UI
    fetchConsumptionEstimate(nodeIds, start, end)
      .then(res => setConsumptionEstimatedRows(res.estimated_rows))
      .catch(err => console.error('[App] Consumption estimate failed:', err));

    try {
      const res = await fetchConsumption(nodeIds, start, end);
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
      if (res.estimated_rows !== undefined) {
        setConsumptionEstimatedRows(res.estimated_rows);
      }
    } catch (err) {
      console.error('[App] Failed to fetch consumption:', err);
    } finally {
      setConsumptionLoading(false);
    }
  };

  const handleShowVoltageDistribution = async (rangeOption?: string, overrideNode?: Node, degrees?: number | null) => {
    const nodesToQuery = overrideNode ? [overrideNode] : selectedNodes;
    if (nodesToQuery.length === 0) return;
    if (overrideNode) setSelectedNodes([overrideNode]);

    const nodeIds = nodesToQuery.map(n => n.id);

    const range = calculateRange(globalConfig);
    let start = range.start;
    let end = range.end;
    if (globalConfig.endDateType === 'now') {
      setDateRange(range);
    }

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
    setVoltageEstimatedRows(undefined);
    setNodeAverages(null);
    setVoltageLoading(true);
    setVoltageModalOpen(true);
    const degreesToUse = degrees !== undefined ? degrees : voltageDegrees;
    setVoltageDegrees(degreesToUse);

    // Fetch estimate separately to update the progress UI
    fetchVoltageEstimate(nodeIds, start, end, degreesToUse === null ? undefined : degreesToUse)
      .then(res => setVoltageEstimatedRows(res.estimated_rows))
      .catch(err => console.error('[App] Voltage estimate failed:', err));

    try {
      const res = await fetchVoltageDistribution(nodeIds, start, end, degreesToUse === null ? undefined : degreesToUse);
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
      if (res.estimated_rows !== undefined) {
        setVoltageEstimatedRows(res.estimated_rows);
      }
    } catch (err) {
      console.error('[App] Failed to fetch voltage distribution:', err);
    } finally {
      setVoltageLoading(false);
    }
  };

  return (
    <MantineProvider defaultColorScheme="dark">
      <GlobalSettingsModal
        opened={settingsOpen}
        onClose={() => setSettingsOpen(false)}
        config={globalConfig}
        onSave={(newConfig) => {
          setGlobalConfig(newConfig);
          const newRange = calculateRange(newConfig);
          setDateRange(newRange);
        }}
      />

      <AppShell padding="0" header={{ height: 0 }}>
        <AppShell.Main>


          {/* Deck.GL Interactive Grid Map */}
          <Box style={{ position: 'absolute', inset: 0, zIndex: 0 }}>
            <GridMap
              nodes={nodes}
              edges={edges}
              onNodeClick={onNodeClick}
              onNodeRightClick={(node, x, y) => setContextMenu({ x, y, item: node, type: 'node' })}
              onEdgeRightClick={(edge, x, y) => setContextMenu({ x, y, item: edge, type: 'edge' })}
              highlightedNodes={highlightedNodes}
              highlightedEdges={highlightedEdges}
              selectedNodeIds={selectedNodes.map(n => n.id)}
              nodeAverages={nodeAverages}
              onMapClick={handleClearSelection}
              voltageScale={voltageScale}
            />
          </Box>

          {/* Right-Click Context Menu */}
          <GridContextMenu
            contextMenu={contextMenu}
            nodes={nodes}
            onClose={handleCloseContextMenu}
            onShowConsumption={(range, node) => handleShowConsumption(range, node)}
            onShowVoltage={(range, node) => handleShowVoltageDistribution(range, node)}
          />

          {/* Persistent Overlay Panels */}
          <VoltageScalePanel
            voltageScale={voltageScale}
            setVoltageScale={setVoltageScale}
            visible={!!nodeAverages}
          />

          {/* Floating Action Button and Analysis Toolbar */}
          <Box style={{ position: 'absolute', top: 20, right: 20, zIndex: 100 }}>
            <Group gap="sm">
              <AnalysisToolbar
                selectedNodes={selectedNodes}
                onClearSelection={handleClearSelection}
                onViewConsumption={() => handleShowConsumption()}
                onViewVoltage={() => handleShowVoltageDistribution()}
                visible={selectedNodes.length > 0}
              />

              <Tooltip label="Global Settings" position="bottom" withArrow>
                <ActionIcon
                  variant="filled"
                  color="blue"
                  size="xl"
                  radius="md"
                  onClick={(e) => {
                    e.stopPropagation();
                    setSettingsOpen(true);
                  }}
                  style={{
                    boxShadow: '0 4px 12px rgba(0,0,0,0.3)',
                    border: '1px solid rgba(255,255,255,0.1)',
                    pointerEvents: 'auto'
                  }}
                >
                  <Settings size={20} />
                </ActionIcon>
              </Tooltip>

              <Menu shadow="md" width={200} position="bottom-end" withArrow offset={10}>
                <Menu.Target>
                  <ActionIcon
                    variant="filled"
                    color="dark"
                    size="xl"
                    radius="md"
                    style={{
                      boxShadow: '0 4px 12px rgba(0,0,0,0.3)',
                      border: '1px solid rgba(255,255,255,0.1)'
                    }}
                  >
                    <MenuIcon />
                  </ActionIcon>
                </Menu.Target>

                <Menu.Dropdown bg="rgba(26, 27, 30, 0.95)" style={{ backdropFilter: 'blur(10px)', border: '1px solid rgba(255,255,255,0.1)' }}>
                  <Menu.Label>System Analytics</Menu.Label>
                  <Menu.Item
                    leftSection={<Settings size={16} />}
                    onClick={() => {
                      setSettingsOpen(true);
                    }}
                  >
                    Global Analysis Settings
                  </Menu.Item>
                  <Menu.Item
                    leftSection={<Activity size={16} />}
                    onClick={() => setActiveSidePanel(p => p === 'analytics' ? 'none' : 'analytics')}
                    bg={activeSidePanel === 'analytics' ? 'rgba(51, 154, 240, 0.2)' : undefined}
                  >
                    Voltage Map Settings
                  </Menu.Item>

                  <Menu.Label>Resources</Menu.Label>
                  <Menu.Item
                    leftSection={<Search size={16} />}
                    onClick={() => window.open('/docs/', '_blank')}
                  >
                    Documentation
                  </Menu.Item>

                  <Menu.Divider />
                  <Menu.Item
                    leftSection={<X size={16} />}
                    color="red"
                    onClick={() => setActiveSidePanel('none')}
                  >
                    Close All Panels
                  </Menu.Item>
                </Menu.Dropdown>
              </Menu>
            </Group>
          </Box>

          {activeSidePanel !== 'none' && (
            <Box
              style={{ position: 'absolute', top: 80, right: 20, zIndex: 10, pointerEvents: 'none' }}
              w={{ base: 'calc(100vw - 40px)', sm: 400 }}
            >
              <Stack gap="16px">

                {activeSidePanel === 'analytics' && (
                  <div style={{ pointerEvents: 'auto' }}>
                    <AnalyticsPanel
                      dateRange={dateRange}
                      setDateRange={setDateRange}
                      loading={loading}
                      estimatedRows={mapVoltageEstimatedRows}
                      onRunVoltageMap={handleRunVoltageMap}
                    />
                  </div>
                )}
              </Stack>
            </Box>
          )}

          {/* Full Width Bottom Modals */}
          <ConsumptionTimeSeriesModal
            isOpen={consumptionModalOpen}
            onClose={handleCloseConsumptionModal}
            loading={consumptionLoading}
            data={consumptionData}
            estimatedRows={consumptionEstimatedRows}
            nodeName={selectedNodes.length > 1 ? `${selectedNodes.length} Assets Aggregate` : (selectedNodes[0]?.name || selectedNodes[0]?.id)}
          />

          <VoltageDistributionModal
            isOpen={voltageModalOpen}
            onClose={handleCloseVoltageModal}
            loading={voltageLoading}
            data={voltageData}
            scatterData={voltageScatterData}
            timeSeriesData={voltageTimeSeries}
            estimatedRows={voltageEstimatedRows}
            nodeName={selectedNodes[0]?.name}
            degrees={voltageDegrees}
            onDegreesChange={(d: number | null) => handleShowVoltageDistribution(undefined, undefined, d)}
          />

        </AppShell.Main>
      </AppShell>
    </MantineProvider >
  );
}
