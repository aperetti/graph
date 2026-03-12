import { Paper, Group, ActionIcon, Tooltip, Badge, Text, Divider, Transition } from '@mantine/core';
import { BarChart3, Activity, X } from 'lucide-react';
import type { Node } from '../../../shared/types';

interface AnalysisToolbarProps {
    selectedNodes: Node[];
    onClearSelection: () => void;
    onViewConsumption: () => void;
    onViewVoltage: () => void;
    visible: boolean;
}

export function AnalysisToolbar({
    selectedNodes,
    onClearSelection,
    onViewConsumption,
    onViewVoltage,
    visible
}: AnalysisToolbarProps) {
    const count = selectedNodes.length;

    return (
        <Transition mounted={visible} transition="slide-left" duration={400} timingFunction="ease">
            {(styles) => (
                <Paper
                    shadow="md"
                    p="xs"
                    radius="md"
                    style={{
                        ...styles,
                        backgroundColor: 'rgba(26, 27, 30, 0.85)',
                        backdropFilter: 'blur(12px)',
                        border: '1px solid rgba(255, 255, 255, 0.1)',
                        pointerEvents: 'auto'
                    }}
                >
                    <Group gap="xs">
                        <Group gap="xs" onClick={onClearSelection} style={{ cursor: 'pointer' }}>
                            <Badge color="blue" variant="filled" size="lg" radius="sm">
                                {count}
                            </Badge>
                            <Text size="xs" fw={500} c="dimmed" visibleFrom="xs">
                                Assets Selected
                            </Text>
                        </Group>

                        <Divider orientation="vertical" />

                        <Tooltip label="Joint Consumption Analysis" position="bottom" withArrow>
                            <ActionIcon
                                variant="light"
                                color="blue"
                                size="lg"
                                onClick={onViewConsumption}
                                radius="md"
                            >
                                <BarChart3 size={18} />
                            </ActionIcon>
                        </Tooltip>

                        <Tooltip label="Joint Voltage Distribution" position="bottom" withArrow>
                            <ActionIcon
                                variant="light"
                                color="cyan"
                                size="lg"
                                onClick={onViewVoltage}
                                radius="md"
                            >
                                <Activity size={18} />
                            </ActionIcon>
                        </Tooltip>

                        <Divider orientation="vertical" />

                        <Tooltip label="Clear Selection" position="bottom" withArrow>
                            <ActionIcon
                                variant="subtle"
                                color="gray"
                                size="lg"
                                onClick={onClearSelection}
                                radius="md"
                            >
                                <X size={18} />
                            </ActionIcon>
                        </Tooltip>
                    </Group>
                </Paper>
            )}
        </Transition>
    );
}
