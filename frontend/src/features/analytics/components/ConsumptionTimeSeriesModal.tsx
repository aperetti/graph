import { memo, useState, useMemo } from 'react';
import { Paper, Group, Title, ActionIcon, Box, Text, RangeSlider, Stack } from '@mantine/core';
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
    const [timeRange, setTimeRange] = useState<[number, number]>([0, 23]);

    const filteredData = useMemo(() => {
        return data.filter(d => {
            const date = new Date(d.timestamp);
            const hour = date.getHours();
            return hour >= timeRange[0] && hour <= timeRange[1];
        });
    }, [data, timeRange]);

    if (!isOpen) return null;

    return (
        <Paper
            withBorder
            style={{
                position: 'fixed',
                bottom: 0,
                left: 0,
                right: 0,
                height: '45vh',
                minHeight: 400,
                zIndex: 20,
                background: 'rgba(26, 27, 30, 0.95)',
                backdropFilter: 'blur(10px)',
                display: 'flex',
                flexDirection: 'column'
            }}
        >
            <Group justify="space-between" px="md" py="xs" style={{ borderBottom: '1px solid rgba(255,255,255,0.1)' }}>
                <Group gap="xl">
                    <Title order={5}>Grid Analytics: {nodeName}</Title>
                    <Group gap="xs">
                        <Text size="xs" c="dimmed">Time Slicer (Hour of Day):</Text>
                        <Box w={200}>
                            <RangeSlider
                                min={0}
                                max={23}
                                step={1}
                                minRange={1}
                                value={timeRange}
                                onChange={setTimeRange}
                                label={(value) => `${value}h`}
                                size="xs"
                                color="blue"
                            />
                        </Box>
                    </Group>
                </Group>
                <ActionIcon variant="subtle" onClick={onClose}>
                    <X size={16} />
                </ActionIcon>
            </Group>

            <Box style={{ flex: 1, position: 'relative', width: '100%', overflow: 'hidden', padding: '10px' }}>
                {loading ? (
                    <Box style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%' }}>
                        <Text c="dimmed">Loading analytical data...</Text>
                    </Box>
                ) : data.length === 0 ? (
                    <Box style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%' }}>
                        <Text c="dimmed">No readings found for this node in the selected date range.</Text>
                    </Box>
                ) : (
                    <Stack gap="md" h="100%">
                        <Box style={{ flex: 1, minHeight: 0 }}>
                            <Text size="xs" fw={700} c="dimmed" mb={4} ta="center">Consumption & Voltage Profile</Text>
                            <ReactECharts
                                style={{ height: 'calc(100% - 20px)', width: '100%' }}
                                option={{
                                    tooltip: { trigger: 'axis', axisPointer: { type: 'cross' } },
                                    legend: { data: ['Delivered', 'Phase A', 'Phase B', 'Phase C'], textStyle: { color: '#A6A7AB' }, top: 0 },
                                    grid: { left: 50, right: 50, bottom: 25, top: 30, containLabel: true },
                                    xAxis: {
                                        type: 'category',
                                        data: data.map(d => d.timestamp.split('T')[1].substring(0, 5)),
                                        axisLabel: { color: '#A6A7AB', fontSize: 10 },
                                        splitLine: { show: true, lineStyle: { color: '#25262B' } }
                                    },
                                    yAxis: [
                                        {
                                            type: 'value',
                                            name: 'kWh',
                                            nameTextStyle: { color: '#A6A7AB' },
                                            axisLabel: { color: '#A6A7AB' },
                                            splitLine: { lineStyle: { color: '#25262B' } }
                                        },
                                        {
                                            type: 'value',
                                            name: 'V',
                                            scale: true,
                                            nameTextStyle: { color: '#A6A7AB' },
                                            axisLabel: { color: '#A6A7AB' },
                                            splitLine: { show: false }
                                        }
                                    ],
                                    series: [
                                        {
                                            name: 'Delivered',
                                            type: 'line',
                                            data: data.map(d => d.kwh_delivered),
                                            itemStyle: { color: '#868e96' },
                                            yAxisIndex: 0,
                                            showSymbol: false,
                                            smooth: true
                                        },
                                        {
                                            name: 'Phase A',
                                            type: 'line',
                                            data: data.map(d => d.median_voltage_a),
                                            itemStyle: { color: '#fa5252' },
                                            yAxisIndex: 1,
                                            showSymbol: false,
                                            smooth: true
                                        },
                                        {
                                            name: 'Phase B',
                                            type: 'line',
                                            data: data.map(d => d.median_voltage_b),
                                            itemStyle: { color: '#40c057' },
                                            yAxisIndex: 1,
                                            showSymbol: false,
                                            smooth: true
                                        },
                                        {
                                            name: 'Phase C',
                                            type: 'line',
                                            data: data.map(d => d.median_voltage_c),
                                            itemStyle: { color: '#228be6' },
                                            yAxisIndex: 1,
                                            showSymbol: false,
                                            smooth: true
                                        }
                                    ]
                                }}
                            />
                        </Box>

                        <Box style={{ flex: 1, minHeight: 0 }}>
                            <Text size="xs" fw={700} c="dimmed" mb={4} ta="center">Load vs Temperature Correlation</Text>
                            <ReactECharts
                                style={{ height: 'calc(100% - 20px)', width: '100%' }}
                                option={{
                                    tooltip: { trigger: 'axis', axisPointer: { type: 'cross' } },
                                    legend: { data: ['Load (kWh)', 'Temp (°C)'], textStyle: { color: '#A6A7AB' }, top: 0 },
                                    grid: { left: 50, right: 50, bottom: 25, top: 30, containLabel: true },
                                    xAxis: {
                                        type: 'category',
                                        data: filteredData.map(d => d.timestamp.split('T')[1].substring(0, 5)),
                                        axisLabel: { color: '#A6A7AB', fontSize: 10 },
                                        splitLine: { show: true, lineStyle: { color: '#25262B' } }
                                    },
                                    yAxis: [
                                        {
                                            type: 'value',
                                            name: 'kWh',
                                            nameTextStyle: { color: '#A6A7AB' },
                                            axisLabel: { color: '#A6A7AB' },
                                            splitLine: { lineStyle: { color: '#25262B' } }
                                        },
                                        {
                                            type: 'value',
                                            name: '°C',
                                            scale: true,
                                            nameTextStyle: { color: '#A6A7AB' },
                                            axisLabel: { color: '#A6A7AB' },
                                            splitLine: { show: false }
                                        }
                                    ],
                                    series: [
                                        {
                                            name: 'Load (kWh)',
                                            type: 'bar',
                                            data: filteredData.map(d => d.kwh_delivered),
                                            itemStyle: { color: '#ffec99', opacity: 0.6 },
                                            yAxisIndex: 0
                                        },
                                        {
                                            name: 'Temp (°C)',
                                            type: 'line',
                                            data: filteredData.map(d => d.temperature),
                                            itemStyle: { color: '#ffa94d' },
                                            yAxisIndex: 1,
                                            showSymbol: false,
                                            smooth: true
                                        }
                                    ]
                                }}
                            />
                        </Box>
                    </Stack>
                )}
            </Box>
        </Paper>
    );
});
