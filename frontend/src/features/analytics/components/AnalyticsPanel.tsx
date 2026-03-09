import { memo, useState } from 'react';
import { Paper, Title, Stack, Button, Select } from '@mantine/core';
import { DatePickerInput } from '@mantine/dates';
import { Map as MapIcon, Calendar } from 'lucide-react';

import dayjs from 'dayjs';

interface Props {
    dateRange: { start: string, end: string };
    setDateRange: (range: { start: string, end: string }) => void;
    loading: boolean;
    onRunVoltageMap: (agg: string) => void;
}

export const AnalyticsPanel = memo(function AnalyticsPanel({
    dateRange,
    setDateRange,
    loading,
    onRunVoltageMap
}: Props) {
    const [agg, setAgg] = useState<string>('median');

    return (
        <Paper p="xl" radius="md" withBorder style={{
            background: 'rgba(26, 27, 30, 0.9)',
            backdropFilter: 'blur(10px)'
        }}>
            <Title order={4} mb="md">Voltage Map Settings</Title>

            <Stack gap="xs">
                <DatePickerInput
                    label="Date"
                    placeholder="Pick date"
                    value={dateRange.start ? new Date(dateRange.start) : null}
                    onChange={(val) => {
                        if (val) {
                            const startOfDay = dayjs(val).startOf('day').format('YYYY-MM-DDTHH:mm:ss');
                            const endOfDay = dayjs(val).endOf('day').format('YYYY-MM-DDTHH:mm:ss');
                            setDateRange({
                                start: startOfDay,
                                end: endOfDay
                            });
                        } else {
                            setDateRange({ start: '', end: '' });
                        }
                    }}
                    leftSection={<Calendar size={16} />}
                    clearable
                />

                <Select
                    label="Aggregation"
                    value={agg}
                    onChange={(v) => setAgg(v || 'median')}
                    data={[
                        { value: 'min', label: 'Minimum' },
                        { value: 'max', label: 'Maximum' },
                        { value: 'median', label: 'Median' },
                        { value: 'mean', label: 'Mean' }
                    ]}
                />

                <Button fullWidth mt="sm" leftSection={<MapIcon size={16} />} onClick={() => onRunVoltageMap(agg)} loading={loading}>
                    Render Voltage Map
                </Button>

            </Stack>
        </Paper>
    );
});
