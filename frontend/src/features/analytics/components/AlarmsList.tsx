import React from 'react';
import { Table, Badge, ScrollArea, Text, Stack, Card } from '@mantine/core';
import type { Alarm } from '../../../shared/api';

interface AlarmsListProps {
    alarms: Alarm[];
    title?: string;
}

const getSeverityColor = (severity: string) => {
    switch (severity.toUpperCase()) {
        case 'CRITICAL': return 'red';
        case 'WARNING': return 'orange';
        case 'INFO': return 'blue';
        default: return 'gray';
    }
};

export const AlarmsList: React.FC<AlarmsListProps> = ({ alarms, title = "Active Alarms" }) => {
    if (alarms.length === 0) {
        return (
            <Card withBorder padding="md">
                <Text size="sm" c="dimmed">No active alarms for this selection.</Text>
            </Card>
        );
    }

    return (
        <Stack gap="xs">
            <Text size="sm" fw={700}>{title} ({alarms.length})</Text>
            <ScrollArea h={300} offsetScrollbars>
                <Table striped highlightOnHover withTableBorder>
                    <Table.Thead>
                        <Table.Tr>
                            <Table.Th>Node</Table.Th>
                            <Table.Th>Code</Table.Th>
                            <Table.Th>Severity</Table.Th>
                            <Table.Th>Timestamp</Table.Th>
                        </Table.Tr>
                    </Table.Thead>
                    <Table.Tbody>
                        {alarms.map((alarm) => (
                            <Table.Tr key={alarm.alarm_id}>
                                <Table.Td><Text size="xs" ff="monospace">{alarm.node_id}</Text></Table.Td>
                                <Table.Td><Text size="xs" fw={500}>{alarm.alarm_code}</Text></Table.Td>
                                <Table.Td>
                                    <Badge size="xs" color={getSeverityColor(alarm.severity)} variant="filled">
                                        {alarm.severity}
                                    </Badge>
                                </Table.Td>
                                <Table.Td>
                                    <Text size="xs" c="dimmed">
                                        {new Date(alarm.timestamp).toLocaleString()}
                                    </Text>
                                </Table.Td>
                            </Table.Tr>
                        ))}
                    </Table.Tbody>
                </Table>
            </ScrollArea>
        </Stack>
    );
};
