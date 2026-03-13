import { memo, useState } from 'react';
import { Paper, Group, Title, ActionIcon, Box, Text, Select, Grid, Collapse, Button } from '@mantine/core';
import { X, Filter, ChevronDown, ChevronUp, Maximize2 } from 'lucide-react';
import ReactECharts from 'echarts-for-react';
import { Rnd } from 'react-rnd';
import { ScadaLoadingAnimation } from '../../../components/ScadaLoadingAnimation';
interface Props {
    isOpen: boolean;
    onClose: () => void;
    loading: boolean;
    data: any[];
    scatterData: any[];
    timeSeriesData: any[];
    estimatedRows?: number;
    nodeName: string | undefined;
    degrees: number | null;
    onDegreesChange: (degrees: number | null) => void;
    isMinimized?: boolean;
    onMinimize?: () => void;
}

export const VoltageDistributionModal = memo(function VoltageDistributionModal({
    isOpen,
    onClose,
    loading,
    data,
    scatterData,
    timeSeriesData,
    estimatedRows,
    nodeName,
    degrees,
    onDegreesChange,
    isMinimized,
    onMinimize,
}: Props) {
    const [showFilters, setShowFilters] = useState<boolean>(false);
    const [rndState, setRndState] = useState(() => {
        const saved = localStorage.getItem('voltageWindowPos');
        if (saved) {
            try {
                return JSON.parse(saved);
            } catch (e) {
                console.error('Failed to parse saved voltageWindowPos', e);
            }
        }
        return {
            x: window.innerWidth - 650,
            y: 50,
            width: 600,
            height: 800
        };
    });

    const handleRndChange = (d: any) => {
        const newState = { ...rndState, ...d };
        setRndState(newState);
        localStorage.setItem('voltageWindowPos', JSON.stringify(newState));
    };

    if (!isOpen) return null;

    if (isMinimized) return null;

    return (
        <Rnd
            size={{ width: rndState.width, height: rndState.height }}
            position={{ x: rndState.x, y: rndState.y }}
            onDragStop={(_e, d) => handleRndChange({ x: d.x, y: d.y })}
            onResizeStop={(_e, _direction, ref, _delta, position) => {
                handleRndChange({
                    width: ref.style.width,
                    height: ref.style.height,
                    ...position
                });
            }}
            minWidth={400}
            minHeight={400}
            bounds="window"
            dragHandleClassName="handle"
            style={{ zIndex: 20 }}
        >
            <Paper
                withBorder
                style={{
                    width: '100%',
                    height: '100%',
                    background: 'rgba(26, 27, 30, 0.95)',
                    backdropFilter: 'blur(10px)',
                    display: 'flex',
                    flexDirection: 'column',
                    overflow: 'hidden'
                }}
            >
                <Box px="md" py="xs" className="handle" style={{ borderBottom: '1px solid rgba(255,255,255,0.1)', cursor: 'grab' }}>
                    <Group justify="space-between" align="center" wrap="nowrap">
                        <Group gap="xs">
                            <Maximize2 size={14} style={{ opacity: 0.5 }} />
                            <Title order={5} style={{ whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>Voltage Analysis: {nodeName}</Title>
                        </Group>
                        <Group wrap="nowrap" gap="xs">
                            <Button
                                variant="subtle"
                                size="xs"
                                color="gray"
                                leftSection={<Filter size={14} />}
                                rightSection={showFilters ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                                onClick={() => setShowFilters(!showFilters)}
                            >
                                Filters
                            </Button>
                            {onMinimize && (
                                <ActionIcon variant="subtle" onClick={onMinimize} title="Minimize">
                                    <ChevronDown size={16} />
                                </ActionIcon>
                            )}
                            <ActionIcon variant="subtle" onClick={onClose} title="Close">
                                <X size={16} />
                            </ActionIcon>
                        </Group>
                    </Group>

                    <Collapse in={showFilters}>
                        <Box mt="md" mb="xs">
                            <Group gap="xs" wrap="wrap">
                                <Text size="xs" c="dimmed">Search Depth:</Text>
                                <Select
                                    size="xs"
                                    w={120}
                                    value={degrees === null ? 'downstream' : degrees.toString()}
                                    onChange={(val: string | null) => {
                                        if (val === null) return;
                                        onDegreesChange(val === 'downstream' ? null : parseInt(val));
                                    }}
                                    allowDeselect={false}
                                    data={[
                                        { label: 'Strictly Downstream', value: 'downstream' },
                                        { label: '1 Degree (Proximal)', value: '1' },
                                        { label: '2 Degrees', value: '2' },
                                        { label: '3 Degrees', value: '3' },
                                        { label: '4 Degrees', value: '4' },
                                        { label: '5 Degrees', value: '5' },
                                        { label: '10 Degrees', value: '10' },
                                    ]}
                                />
                            </Group>
                        </Box>
                    </Collapse>
                </Box>

                <Box style={{ flex: 1, position: 'relative', width: '100%', overflow: 'hidden', padding: '10px' }}>
                    {loading ? (
                        <ScadaLoadingAnimation estimatedRows={estimatedRows} />
                    ) : data.length === 0 && scatterData.length === 0 ? (
                        <Box style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%' }}>
                            <Text c="dimmed">No distribution data found for this node in the selected date range.</Text>
                        </Box>
                    ) : (
                        <Grid style={{ width: '100%', height: '100%' }} gutter="md" align="stretch">
                            {/* 1. KDE Distribution */}
                            <Grid.Col span={{ base: 12, md: 4, lg: 3 }} style={{ height: 350 }}>
                                <Text size="xs" c="dimmed" mb={4} ta="center">Distribution (KDE)</Text>
                                <Box h="calc(100% - 24px)" w="100%">
                                    <ReactECharts
                                        style={{ height: '100%', width: '100%' }}
                                        option={{
                                            tooltip: { trigger: 'axis', axisPointer: { type: 'cross' } },
                                            legend: { data: ['Phase A', 'Phase B', 'Phase C'], textStyle: { color: '#A6A7AB', fontSize: 10 }, top: 0, itemWidth: 10 },
                                            grid: { left: 10, right: 10, bottom: 20, top: 30, containLabel: true },
                                            xAxis: {
                                                type: 'category',
                                                data: data.map((d: any) => d.voltage),
                                                axisLabel: { color: '#A6A7AB', fontSize: 10 },
                                                splitLine: { show: true, lineStyle: { color: '#25262B' } }
                                            },
                                            yAxis: {
                                                type: 'value',
                                                show: false,
                                                splitLine: { lineStyle: { color: '#25262B' } }
                                            },
                                            series: [
                                                {
                                                    name: 'Phase A',
                                                    type: 'line',
                                                    data: data.map((d: any) => d.a),
                                                    itemStyle: { color: '#fa5252' },
                                                    areaStyle: { opacity: 0.2 },
                                                    showSymbol: false,
                                                    smooth: true
                                                },
                                                {
                                                    name: 'Phase B',
                                                    type: 'line',
                                                    data: data.map((d: any) => d.b),
                                                    itemStyle: { color: '#40c057' },
                                                    areaStyle: { opacity: 0.2 },
                                                    showSymbol: false,
                                                    smooth: true
                                                },
                                                {
                                                    name: 'Phase C',
                                                    type: 'line',
                                                    data: data.map((d: any) => d.c),
                                                    itemStyle: { color: '#228be6' },
                                                    areaStyle: { opacity: 0.2 },
                                                    showSymbol: false,
                                                    smooth: true
                                                }
                                            ]
                                        }}
                                    />
                                </Box>
                            </Grid.Col>

                            {/* 2. Daily Timeseries (Median + 10/90 Bands) */}
                            <Grid.Col span={{ base: 12, md: 8, lg: 5 }} style={{ height: 350 }}>
                                <Text size="xs" c="dimmed" mb={4} ta="center">Daily Voltage stability (Median & 10/90 Bands)</Text>
                                <Box h="calc(100% - 24px)" w="100%">
                                    <ReactECharts
                                        style={{ height: '100%', width: '100%' }}
                                        option={{
                                            tooltip: { trigger: 'axis' },
                                            grid: { left: 40, right: 20, bottom: 20, top: 30, containLabel: true },
                                            xAxis: {
                                                type: 'category',
                                                data: timeSeriesData.map(d => d.date),
                                                axisLabel: { color: '#A6A7AB', fontSize: 10 },
                                                splitLine: { show: true, lineStyle: { color: '#25262B' } }
                                            },
                                            yAxis: {
                                                type: 'value',
                                                scale: true,
                                                axisLabel: { color: '#A6A7AB', fontSize: 10 },
                                                splitLine: { lineStyle: { color: '#25262B' } }
                                            },
                                            series: [
                                                {
                                                    name: 'P90',
                                                    type: 'line',
                                                    data: timeSeriesData.map(d => parseFloat(d.p90.toFixed(2))),
                                                    itemStyle: { color: '#fa5252' },
                                                    showSymbol: false,
                                                    smooth: true
                                                },
                                                {
                                                    name: 'Median',
                                                    type: 'line',
                                                    data: timeSeriesData.map(d => parseFloat(d.p50.toFixed(2))),
                                                    itemStyle: { color: '#fab005' },
                                                    showSymbol: false,
                                                    smooth: true
                                                },
                                                {
                                                    name: 'P10',
                                                    type: 'line',
                                                    data: timeSeriesData.map(d => parseFloat(d.p10.toFixed(2))),
                                                    itemStyle: { color: '#228be6' },
                                                    showSymbol: false,
                                                    smooth: true
                                                }
                                            ]
                                        }}
                                    />
                                </Box>
                            </Grid.Col>

                            {/* 3. Heatmap */}
                            <Grid.Col span={{ base: 12, md: 12, lg: 4 }} style={{ height: 350 }}>
                                <Text size="xs" c="dimmed" mb={4} ta="center">Voltage vs Loading (Heatmap)</Text>
                                <Box h="calc(100% - 24px)" w="100%">
                                    <ReactECharts
                                        style={{ height: '100%', width: '100%' }}
                                        option={{
                                            tooltip: {
                                                trigger: 'item',
                                                formatter: (params: any) => {
                                                    const [x, y, count] = params.data;
                                                    return `Loading: ${x} kWh<br/>Voltage: ${y} V<br/>Count: ${count}`;
                                                }
                                            },
                                            grid: { left: 40, right: 20, bottom: 40, top: 30, containLabel: true },
                                            xAxis: {
                                                type: 'value',
                                                name: 'Loading (kWh)',
                                                nameLocation: 'middle',
                                                nameGap: 25,
                                                scale: true,
                                                nameTextStyle: { color: '#A6A7AB', fontSize: 10 },
                                                axisLabel: { color: '#A6A7AB', fontSize: 10 },
                                                splitLine: { lineStyle: { color: '#25262B' } }
                                            },
                                            yAxis: {
                                                type: 'value',
                                                name: 'Voltage (V)',
                                                nameLocation: 'middle',
                                                nameGap: 30,
                                                scale: true,
                                                nameTextStyle: { color: '#A6A7AB', fontSize: 10 },
                                                axisLabel: { color: '#A6A7AB', fontSize: 10 },
                                                splitLine: { lineStyle: { color: '#25262B' } }
                                            },
                                            visualMap: {
                                                show: false,
                                                dimension: 1,
                                                min: 110,
                                                max: 130,
                                                inRange: {
                                                    color: ['#fa5252', '#fab005', '#40c057', '#fab005', '#fa5252']
                                                }
                                            },
                                            series: [
                                                {
                                                    name: 'Density',
                                                    type: 'scatter',
                                                    symbolSize: 4,
                                                    symbol: 'roundRect',
                                                    itemStyle: {
                                                        borderRadius: 1,
                                                        opacity: 0.5
                                                    },
                                                    data: scatterData[0]?.data?.map((d: any) => [d.x, d.y, d.count]) || []
                                                }
                                            ]
                                        }}
                                    />
                                </Box>
                            </Grid.Col>
                        </Grid>
                    )}
                </Box>
            </Paper>
        </Rnd>
    );
});
