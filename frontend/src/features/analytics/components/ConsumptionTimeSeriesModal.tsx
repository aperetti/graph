import { memo } from 'react';
import { Paper, Group, Title, ActionIcon, Box, Text } from '@mantine/core';
import { X } from 'lucide-react';
import ReactECharts from 'echarts-for-react';

interface Props {
    isOpen: boolean;
    onClose: () => void;
    loading: boolean;
    data: any[];
    nodeName: string | undefined;
}

export const ConsumptionTimeSeriesModal = memo(function ConsumptionTimeSeriesModal({
    isOpen,
    onClose,
    loading,
    data,
    nodeName,
}: Props) {
    if (!isOpen) return null;

    return (
        <Paper
            withBorder
            style={{
                position: 'fixed',
                bottom: 0,
                left: 0,
                right: 0,
                height: '20vh',
                minHeight: 200,
                zIndex: 20,
                background: 'rgba(26, 27, 30, 0.95)',
                backdropFilter: 'blur(10px)',
                display: 'flex',
                flexDirection: 'column'
            }}
        >
            <Group justify="space-between" px="md" py="xs" style={{ borderBottom: '1px solid rgba(255,255,255,0.1)' }}>
                <Title order={5}>Aggregated Consumption: {nodeName}</Title>
                <ActionIcon variant="subtle" onClick={onClose}>
                    <X size={16} />
                </ActionIcon>
            </Group>

            <Box style={{ flex: 1, position: 'relative', width: '100%', overflow: 'hidden', padding: '10px' }}>
                {loading ? (
                    <Box style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%' }}>
                        <Text c="dimmed">Loading time-series data...</Text>
                    </Box>
                ) : data.length === 0 ? (
                    <Box style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%' }}>
                        <Text c="dimmed">No readings found for this node in the selected date range.</Text>
                    </Box>
                ) : (
                    <Group style={{ width: '100%', height: '100%' }} wrap="nowrap" gap="md" align="stretch">
                        <Box style={{ flex: 1, height: '100%' }}>
                            <Text size="xs" c="dimmed" mb={4} ta="center">Energy Delivered (kWh)</Text>
                            <Box h="calc(100% - 24px)" w="100%">
                                <ReactECharts
                                    style={{ height: '100%', width: '100%' }}
                                    option={{
                                        tooltip: { trigger: 'axis', axisPointer: { type: 'cross' } },
                                        grid: { left: 50, right: 40, bottom: 20, top: 40, containLabel: true },
                                        xAxis: {
                                            type: 'category',
                                            data: data.map(d => d.date),
                                            axisLabel: { color: '#A6A7AB' },
                                            splitLine: { show: true, lineStyle: { color: '#25262B' } }
                                        },
                                        yAxis: {
                                            type: 'value',
                                            scale: true,
                                            name: 'kWh',
                                            nameTextStyle: { color: '#A6A7AB' },
                                            axisLabel: { color: '#A6A7AB' },
                                            splitLine: { lineStyle: { color: '#25262B' } }
                                        },
                                        series: [
                                            {
                                                name: 'Delivered',
                                                type: 'line',
                                                data: data.map(d => d.delivered),
                                                itemStyle: { color: '#868e96' },
                                                showSymbol: false,
                                                smooth: true
                                            }
                                        ]
                                    }}
                                />
                            </Box>
                        </Box>

                        <Box style={{ flex: 1, height: '100%' }}>
                            <Text size="xs" c="dimmed" mb={4} ta="center">Voltage Profiles</Text>
                            <Box h="calc(100% - 24px)" w="100%">
                                <ReactECharts
                                    style={{ height: '100%', width: '100%' }}
                                    option={{
                                        tooltip: { trigger: 'axis', axisPointer: { type: 'cross' } },
                                        legend: { data: ['Phase A', 'Phase B', 'Phase C'], textStyle: { color: '#A6A7AB' }, top: 5 },
                                        grid: { left: 50, right: 40, bottom: 20, top: 50, containLabel: true },
                                        xAxis: {
                                            type: 'category',
                                            data: data.map(d => d.date),
                                            axisLabel: { color: '#A6A7AB' },
                                            splitLine: { show: true, lineStyle: { color: '#25262B' } }
                                        },
                                        yAxis: {
                                            type: 'value',
                                            scale: true,
                                            name: 'Voltage (V)',
                                            nameTextStyle: { color: '#A6A7AB', padding: [0, 0, 0, 20] },
                                            axisLabel: { color: '#A6A7AB' },
                                            splitLine: { lineStyle: { color: '#25262B' } }
                                        },
                                        series: [
                                            {
                                                name: 'Phase A',
                                                type: 'line',
                                                data: data.map(d => d.voltageA),
                                                itemStyle: { color: '#fa5252' },
                                                showSymbol: false,
                                                smooth: true
                                            },
                                            {
                                                name: 'Phase B',
                                                type: 'line',
                                                data: data.map(d => d.voltageB),
                                                itemStyle: { color: '#40c057' },
                                                showSymbol: false,
                                                smooth: true
                                            },
                                            {
                                                name: 'Phase C',
                                                type: 'line',
                                                data: data.map(d => d.voltageC),
                                                itemStyle: { color: '#228be6' },
                                                showSymbol: false,
                                                smooth: true
                                            }
                                        ]
                                    }}
                                />
                            </Box>
                        </Box>
                    </Group>
                )}
            </Box>
        </Paper>
    );
});
