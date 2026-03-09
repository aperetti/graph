import { memo } from 'react';
import { Paper, Title, Text, Group, Badge, ActionIcon, Code, Button } from '@mantine/core';
import { BarChart3, X } from 'lucide-react';
import type { Node } from '../../../shared/types';

interface Props {
    nodeCount: number;
    selectedNode: Node | null;
    onClearSelection: () => void;
    onViewConsumption: () => void;
}

export const GridExplorerPanel = memo(function GridExplorerPanel({
    nodeCount,
    selectedNode,
    onClearSelection,
    onViewConsumption
}: Props) {
    return (
        <>
            <Paper p="xl" radius="md" withBorder style={{
                background: 'rgba(26, 27, 30, 0.9)',
                backdropFilter: 'blur(10px)'
            }}>
                <Title order={3} mb="xs">Grid Topology Explorer</Title>
                <Text size="sm" c="dimmed" mb="md">Integrated phase-balance analytics & AGENT-IC SQL generation.</Text>

                <Group gap="xs">
                    <Badge color="teal" variant="light">DuckDB Backend Ready</Badge>
                    <Badge color="blue" variant="light">Meters: {nodeCount.toLocaleString()}</Badge>
                </Group>
            </Paper>

            {selectedNode && (
                <Paper p="xl" radius="md" withBorder style={{
                    background: 'rgba(26, 27, 30, 0.9)',
                    backdropFilter: 'blur(10px)'
                }}>
                    <Group justify="space-between" mb="sm">
                        <Title order={4}>Selected Asset</Title>
                        <ActionIcon variant="subtle" onClick={onClearSelection}><X size={16} /></ActionIcon>
                    </Group>
                    <Code block mb="md">
                        ID: {selectedNode.id}{'\n'}
                        Type: {selectedNode.type}{'\n'}
                        Name: {selectedNode.name}
                    </Code>
                    <Button fullWidth size="xs" variant="light" leftSection={<BarChart3 size={14} />} onClick={onViewConsumption}>
                        View Consumption Time-Series
                    </Button>
                </Paper>
            )}
        </>
    );
});
