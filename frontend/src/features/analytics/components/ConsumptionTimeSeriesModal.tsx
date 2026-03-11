import { useState, useMemo } from 'react';
import { Paper, Group, Title, ActionIcon, Box, Text, Stack, Select, NumberInput } from '@mantine/core';
import { X } from 'lucide-react';
import ReactECharts from 'echarts-for-react';

interface ReadingData {
    timestamp: string;
    kwh_delivered: number | null;
    temperature: number | null;
}

interface Props {
    isOpen: boolean;
    onClose: () => void;
    loading: boolean;
    data: ReadingData[];
    nodeName: string | undefined;
}

const MONTH_OPTIONS = [
    { value: '0', label: 'Jan' },
    { value: '1', label: 'Feb' },
    { value: '2', label: 'Mar' },
    { value: '3', label: 'Apr' },
    { value: '4', label: 'May' },
    { value: '5', label: 'Jun' },
    { value: '6', label: 'Jul' },
    { value: '7', label: 'Aug' },
    { value: '8', label: 'Sep' },
    { value: '9', label: 'Oct' },
    { value: '10', label: 'Nov' },
    { value: '11', label: 'Dec' },
];

const HOUR_OPTIONS = Array.from({ length: 24 }, (_, i) => ({
    value: i.toString(),
    label: `${i.toString().padStart(2, '0')}:00`
}));

export function ConsumptionTimeSeriesModal({
    isOpen,
    onClose,
    loading,
    data,
    nodeName,
}: Props) {
    const [startHour, setStartHour] = useState<string>('0');
    const [endHour, setEndHour] = useState<string>('23');
    const [startMonth, setStartMonth] = useState<string>('0');
    const [endMonth, setEndMonth] = useState<string>('11');
    const [targetTemp, setTargetTemp] = useState<number | string>(20);

    const filteredByMonth = useMemo(() => {
        const sM = parseInt(startMonth);
        const eM = parseInt(endMonth);

        return data.filter(d => {
            const date = new Date(d.timestamp);
            const month = date.getMonth();

            return sM <= eM
                ? (month >= sM && month <= eM)
                : (month >= sM || month <= eM);
        });
    }, [data, startMonth, endMonth]);

    const filteredData = useMemo(() => {
        const sH = parseInt(startHour);
        const eH = parseInt(endHour);

        return filteredByMonth.filter(d => {
            const date = new Date(d.timestamp);
            const hour = date.getHours();

            return sH <= eH
                ? (hour >= sH && hour <= eH)
                : (hour >= sH || hour <= eH);
        });
    }, [filteredByMonth, startHour, endHour]);

    const regression = useMemo(() => {
        const points = filteredData
            .filter((d): d is ReadingData & { temperature: number; kwh_delivered: number } =>
                d.temperature != null && d.kwh_delivered != null
            )
            .map(d => ({ x: d.temperature, y: d.kwh_delivered }));

        if (points.length < 2) return null;

        const n = points.length;
        let sumX = 0, sumY = 0, sumXY = 0, sumX2 = 0;
        let minX = points[0].x, maxX = points[0].x;

        for (const p of points) {
            sumX += p.x;
            sumY += p.y;
            sumXY += p.x * p.y;
            sumX2 += p.x * p.x;
            if (p.x < minX) minX = p.x;
            if (p.x > maxX) maxX = p.x;
        }

        const denominator = (n * sumX2 - sumX * sumX);
        if (denominator === 0) return null;

        const slope = (n * sumXY - sumX * sumY) / denominator;
        const intercept = (sumY - slope * sumX) / n;

        return {
            start: [minX, slope * minX + intercept],
            end: [maxX, slope * maxX + intercept],
            slope,
            intercept
        };
    }, [filteredData]);

    const smoothedTemperatures = useMemo(() => {
        if (data.length === 0) return [];
        const windowSize = 96; // 24h at 15m resolution
        const result: (number | null)[] = [];
        let sum = 0;
        let count = 0;

        for (let i = 0; i < data.length; i++) {
            if (data[i].temperature != null) {
                sum += data[i].temperature!;
                count++;
            }
            if (i >= windowSize) {
                const old = data[i - windowSize].temperature;
                if (old != null) {
                    sum -= old;
                    count--;
                }
            }
            result.push(count > 0 ? sum / count : null);
        }
        return result;
    }, [data]);

    const timeSeriesData = useMemo(() => {
        if (data.length === 0) return [];

        const first = new Date(data[0].timestamp).getTime();
        const last = new Date(data[data.length - 1].timestamp).getTime();
        const spanDays = (last - first) / (1000 * 60 * 60 * 24);

        if (spanDays <= 90) {
            return data.map((d, i) => [new Date(d.timestamp).getTime(), d.kwh_delivered, smoothedTemperatures[i]]);
        }

        const bucketHours = spanDays > 365 ? 3 : 1;
        const bucketMs = bucketHours * 60 * 60 * 1000;
        const aggregated: [number, number | null, number | null][] = [];
        let curKwh: number[] = [];
        let curTemp: number[] = [];
        let bucketStartTime = Math.floor(first / bucketMs) * bucketMs;

        data.forEach((d, i) => {
            const time = new Date(d.timestamp).getTime();
            const sTemp = smoothedTemperatures[i];
            if (time < bucketStartTime + bucketMs) {
                if (d.kwh_delivered != null) curKwh.push(d.kwh_delivered);
                if (sTemp != null) curTemp.push(sTemp);
            } else {
                if (curKwh.length > 0 || curTemp.length > 0) {
                    const avgKwh = curKwh.length > 0 ? curKwh.reduce((a, b) => a + b, 0) / curKwh.length : null;
                    const avgTemp = curTemp.length > 0 ? curTemp.reduce((a, b) => a + b, 0) / curTemp.length : null;
                    aggregated.push([bucketStartTime, avgKwh, avgTemp]);
                }
                bucketStartTime = Math.floor(time / bucketMs) * bucketMs;
                curKwh = d.kwh_delivered != null ? [d.kwh_delivered] : [];
                curTemp = sTemp != null ? [sTemp] : [];
            }
        });

        if (curKwh.length > 0 || curTemp.length > 0) {
            const avgKwh = curKwh.length > 0 ? curKwh.reduce((a, b) => a + b, 0) / curKwh.length : null;
            const avgTemp = curTemp.length > 0 ? curTemp.reduce((a, b) => a + b, 0) / curTemp.length : null;
            aggregated.push([bucketStartTime, avgKwh, avgTemp]);
        }

        return aggregated;
    }, [data]);

    const hourlyAggregation = useMemo(() => {
        const buckets = Array.from({ length: 24 }, () => ({ total: 0, count: 0 }));

        filteredByMonth.forEach(d => {
            if (d.kwh_delivered != null) {
                const hour = new Date(d.timestamp).getHours();
                buckets[hour].total += d.kwh_delivered;
                buckets[hour].count += 1;
            }
        });

        return buckets.map((b, i) => ({
            hour: `${i.toString().padStart(2, '0')}:00`,
            avg: b.count > 0 ? b.total / b.count : 0
        }));
    }, [filteredByMonth]);

    const markLines = useMemo(() => {
        if (data.length === 0) return [];
        const marks: any[] = [];
        let lastMonth = -1;

        data.forEach((d) => {
            const date = new Date(d.timestamp);
            const month = date.getMonth();
            const timestamp = date.getTime();

            // Month boundary marker
            if (lastMonth !== -1 && month !== lastMonth) {
                marks.push({
                    xAxis: timestamp,
                    label: {
                        show: true,
                        position: 'end',
                        formatter: MONTH_OPTIONS[month].label,
                        color: '#A6A7AB',
                        fontSize: 10,
                        backgroundColor: 'rgba(26, 27, 30, 0.7)',
                        padding: [2, 4],
                        borderRadius: 2
                    },
                    lineStyle: { type: 'solid', color: 'rgba(255, 255, 255, 0.2)', width: 1 }
                });
            }
            lastMonth = month;
        });
        return marks;
    }, [data]);

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
                zIndex: 1000,
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
                        <Text size="xs" c="dimmed">Month Range:</Text>
                        <Select
                            id="select-month-start"
                            data={MONTH_OPTIONS}
                            value={startMonth}
                            onChange={(v) => v && setStartMonth(v)}
                            size="xs"
                            w={80}
                            comboboxProps={{ withinPortal: true, zIndex: 2000 }}
                        />
                        <Text size="xs" c="dimmed">to</Text>
                        <Select
                            id="select-month-end"
                            data={MONTH_OPTIONS}
                            value={endMonth}
                            onChange={(v) => v && setEndMonth(v)}
                            size="xs"
                            w={80}
                            comboboxProps={{ withinPortal: true, zIndex: 2000 }}
                        />
                    </Group>

                    <Group gap="xs">
                        <Text size="xs" c="dimmed">Time Range (Slicer):</Text>
                        <Select
                            id="select-hour-start"
                            data={HOUR_OPTIONS}
                            value={startHour}
                            onChange={(v) => v && setStartHour(v)}
                            size="xs"
                            w={90}
                            comboboxProps={{ withinPortal: true, zIndex: 2000 }}
                        />
                        <Text size="xs" c="dimmed">to</Text>
                        <Select
                            id="select-hour-end"
                            data={HOUR_OPTIONS}
                            value={endHour}
                            onChange={(v) => v && setEndHour(v)}
                            size="xs"
                            w={90}
                            comboboxProps={{ withinPortal: true, zIndex: 2000 }}
                        />
                    </Group>
                    <Text size="xs" c="dimmed" style={{ fontStyle: 'italic' }}>*Month slicer affects Daily Profile; Hour slicer affects Correlation</Text>
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
                    <Box style={{ height: '100%', overflowY: 'auto', paddingRight: '10px' }}>
                        <Stack gap="xl">
                            <Box style={{ height: 280 }}>
                                <Text size="xs" fw={700} c="dimmed" mb={4} ta="center">Consumption Time-Series (Full Period)</Text>
                                <ReactECharts
                                    style={{ height: 240, width: '100%' }}
                                    option={{
                                        tooltip: {
                                            trigger: 'axis',
                                            backgroundColor: 'rgba(26, 27, 30, 0.9)',
                                            borderColor: '#373A40',
                                            textStyle: { color: '#C1C2C5', fontSize: 11 }
                                        },
                                        legend: {
                                            data: ['kWh Delivered', 'Temp (24h Avg)'],
                                            textStyle: { color: '#A6A7AB', fontSize: 10 },
                                            top: 0
                                        },
                                        grid: { left: 40, right: 40, bottom: 25, top: 30, containLabel: true },
                                        xAxis: {
                                            type: 'time',
                                            axisLabel: {
                                                color: '#A6A7AB',
                                                fontSize: 10,
                                                formatter: (value: number) => {
                                                    const date = new Date(value);
                                                    return date.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
                                                }
                                            },
                                            axisLine: { lineStyle: { color: '#373A40' } },
                                            splitLine: { show: false }
                                        },
                                        yAxis: [
                                            {
                                                type: 'value',
                                                name: 'kWh',
                                                scale: true,
                                                axisLabel: { color: '#A6A7AB', fontSize: 10 },
                                                splitLine: { lineStyle: { color: '#25262B' } }
                                            },
                                            {
                                                type: 'value',
                                                name: '°C',
                                                scale: true,
                                                axisLabel: { color: '#FA5252', fontSize: 10 },
                                                splitLine: { show: false }
                                            }
                                        ],
                                        series: [
                                            {
                                                name: 'kWh Delivered',
                                                type: 'line',
                                                data: timeSeriesData.map(d => [d[0], d[1]]),
                                                smooth: true,
                                                showSymbol: false,
                                                itemStyle: { color: '#339af0' },
                                                areaStyle: {
                                                    opacity: 0.1,
                                                    color: {
                                                        type: 'linear',
                                                        x: 0, y: 0, x2: 0, y2: 1,
                                                        colorStops: [{ offset: 0, color: '#339af0' }, { offset: 1, color: 'rgba(51, 154, 240, 0)' }]
                                                    }
                                                },
                                                markLine: {
                                                    symbol: ['none', 'none'],
                                                    silent: true,
                                                    data: markLines
                                                }
                                            },
                                            {
                                                name: 'Temp (24h Avg)',
                                                type: 'line',
                                                yAxisIndex: 1,
                                                data: timeSeriesData.map(d => [d[0], d[2]]),
                                                smooth: true,
                                                showSymbol: false,
                                                itemStyle: { color: '#fa5252' },
                                                lineStyle: { width: 1, opacity: 0.5 }
                                            }
                                        ]
                                    }}
                                />
                            </Box>

                            <Group grow align="stretch" gap="lg" mb="xl">
                                <Box style={{ height: 380 }}>
                                    <Text size="xs" fw={700} c="dimmed" mb={4} ta="center">Typical Daily Load Profile (Hourly Avg)</Text>
                                    <ReactECharts
                                        style={{ height: 340, width: '100%' }}
                                        option={{
                                            tooltip: {
                                                trigger: 'axis',
                                                backgroundColor: 'rgba(26, 27, 30, 0.9)',
                                                borderColor: '#373A40',
                                                textStyle: { color: '#C1C2C5' }
                                            },
                                            grid: { left: 50, right: 30, bottom: 25, top: 40, containLabel: true },
                                            xAxis: {
                                                type: 'category',
                                                data: Array.from({ length: 24 }, (_, i) => `${i}:00`),
                                                axisLabel: { color: '#A6A7AB', fontSize: 10 },
                                                axisLine: { lineStyle: { color: '#373A40' } }
                                            },
                                            yAxis: {
                                                type: 'value',
                                                name: 'Avg kWh',
                                                scale: true,
                                                axisLabel: { color: '#A6A7AB', fontSize: 10 },
                                                splitLine: { lineStyle: { color: '#25262B' } }
                                            },
                                            series: [{
                                                name: 'Average Load',
                                                type: 'line',
                                                data: hourlyAggregation.map(h => h.avg),
                                                itemStyle: { color: '#ffd43b' },
                                                areaStyle: {
                                                    opacity: 0.2,
                                                    color: {
                                                        type: 'linear',
                                                        x: 0, y: 0, x2: 0, y2: 1,
                                                        colorStops: [{ offset: 0, color: 'rgba(255, 212, 59, 0.3)' }, { offset: 1, color: 'rgba(255, 212, 59, 0)' }]
                                                    }
                                                },
                                                smooth: true,
                                                showSymbol: false
                                            }]
                                        }}
                                    />
                                </Box>

                                <Box style={{ height: 380 }}>
                                    <Text size="xs" fw={700} c="dimmed" mb={4} ta="center">Load vs Temperature Correlation (Filtered)</Text>
                                    <Group grow mb="sm" px="xs" align="flex-end">
                                        <NumberInput
                                            size="xs"
                                            label="Target Temp (°C)"
                                            value={targetTemp}
                                            onChange={setTargetTemp}
                                            step={0.5}
                                            styles={{ input: { backgroundColor: '#1A1B1E', color: '#A6A7AB', border: '1px solid #373A40' } }}
                                        />
                                        <Stack gap={2}>
                                            <Text size="xs" c="dimmed" fw={500}>Predicted Load</Text>
                                            <Paper p="xs" withBorder style={{ backgroundColor: '#25262B', borderColor: '#373A40' }}>
                                                <Text fw={700} size="md" c="yellow" ta="center">
                                                    {regression && typeof targetTemp === 'number'
                                                        ? (regression.slope * targetTemp + regression.intercept).toFixed(3) + ' kWh'
                                                        : '---'}
                                                </Text>
                                            </Paper>
                                        </Stack>
                                    </Group>
                                    <ReactECharts
                                        style={{ height: 260, width: '100%' }}
                                        option={{
                                            tooltip: { trigger: 'item', axisPointer: { type: 'cross' } },
                                            grid: { left: 40, right: 20, bottom: 25, top: 10, containLabel: true },
                                            xAxis: {
                                                type: 'value',
                                                nameTextStyle: { color: '#A6A7AB' },
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
                                                    name: 'Data Points',
                                                    type: 'scatter',
                                                    data: filteredData.map(d => [d.temperature, d.kwh_delivered]),
                                                    itemStyle: { color: '#ffec99', opacity: 0.6 },
                                                    symbolSize: 6,
                                                },
                                                regression && {
                                                    name: 'Linear Regression',
                                                    type: 'line',
                                                    data: [regression.start, regression.end],
                                                    itemStyle: { color: '#fa5252' },
                                                    showSymbol: false,
                                                    lineStyle: { width: 2, type: 'dashed' },
                                                    smooth: false
                                                },
                                                regression && typeof targetTemp === 'number' && {
                                                    name: 'Target Prediction',
                                                    type: 'scatter',
                                                    data: [[targetTemp, regression.slope * targetTemp + regression.intercept]],
                                                    itemStyle: {
                                                        color: '#ffd43b',
                                                        borderColor: '#fff',
                                                        borderWidth: 1,
                                                        shadowBlur: 5,
                                                        shadowColor: 'rgba(255, 212, 59, 0.8)'
                                                    },
                                                    symbolSize: 12,
                                                    symbol: 'diamond',
                                                    label: {
                                                        show: true,
                                                        formatter: 'Target',
                                                        position: 'top',
                                                        color: '#fff',
                                                        fontSize: 9,
                                                        fontWeight: 'bold',
                                                        backgroundColor: 'rgba(0,0,0,0.5)',
                                                        padding: [1, 2],
                                                        borderRadius: 2
                                                    }
                                                }
                                            ].filter(Boolean)
                                        }}
                                    />
                                </Box>
                            </Group>
                        </Stack>
                    </Box>
                )}
            </Box>
        </Paper>
    );
}
