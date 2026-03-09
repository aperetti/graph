import { memo } from 'react';
import { Stack, Text, Button, Group } from '@mantine/core';
import type { Node, Edge } from '../../../shared/types';

interface ContextMenuState {
    x: number;
    y: number;
    item: any;
    type: 'node' | 'edge';
}

interface Props {
    contextMenu: ContextMenuState | null;
    nodes: Node[];
    onClose: () => void;

    onShowConsumption: (range: '1W' | '1M' | '1Y', node: Node) => void;
    onShowVoltage: (range: '1W' | '1M' | '1Y', node: Node) => void;
}

export const GridContextMenu = memo(function GridContextMenu({
    contextMenu,
    nodes,
    onClose,

    onShowConsumption,
    onShowVoltage
}: Props) {
    if (!contextMenu) return null;

    return (
        <div
            style={{
                position: 'absolute',
                left: contextMenu.x,
                top: contextMenu.y,
                zIndex: 1000,
                background: '#25262B',
                border: '1px solid #373A40',
                borderRadius: 4,
                padding: '8px 4px',
                width: 220,
                boxShadow: '0 4px 12px rgba(0,0,0,0.5)',
            }}
            onClick={(e) => e.stopPropagation()}
        >
            <Stack gap={4}>
                <Text size="xs" c="cyan" fw={600} px="xs" py={4} style={{ borderBottom: '1px solid #373A40' }}>
                    {contextMenu.type === 'node' ? (contextMenu.item as Node).type : 'Line'} Actions
                </Text>

                {contextMenu.type === 'edge' && (
                    <>
                        <Text size="xs" c="dimmed" px="xs" mt={4}>Consumption Time Series (Downstream Node)</Text>
                        <Group gap={4} px="xs" grow>
                            <Button size="xs" variant="light" onClick={() => {
                                const targetToUse = nodes.find(n => n.id === (contextMenu.item as Edge).target);
                                if (targetToUse) onShowConsumption('1W', targetToUse);
                                onClose();
                            }}>1W</Button>
                            <Button size="xs" variant="light" onClick={() => {
                                const targetToUse = nodes.find(n => n.id === (contextMenu.item as Edge).target);
                                if (targetToUse) onShowConsumption('1M', targetToUse);
                                onClose();
                            }}>1M</Button>
                            <Button size="xs" variant="light" onClick={() => {
                                const targetToUse = nodes.find(n => n.id === (contextMenu.item as Edge).target);
                                if (targetToUse) onShowConsumption('1Y', targetToUse);
                                onClose();
                            }}>1Y</Button>
                        </Group>
                        <Text size="xs" c="dimmed" px="xs" mt={4}>Voltage Distribution (Downstream Node)</Text>
                        <Group gap={4} px="xs" grow>
                            <Button size="xs" variant="light" color="grape" onClick={() => {
                                const targetToUse = nodes.find(n => n.id === (contextMenu.item as Edge).target);
                                if (targetToUse) onShowVoltage('1W', targetToUse);
                                onClose();
                            }}>1W</Button>
                            <Button size="xs" variant="light" color="grape" onClick={() => {
                                const targetToUse = nodes.find(n => n.id === (contextMenu.item as Edge).target);
                                if (targetToUse) onShowVoltage('1M', targetToUse);
                                onClose();
                            }}>1M</Button>
                            <Button size="xs" variant="light" color="grape" onClick={() => {
                                const targetToUse = nodes.find(n => n.id === (contextMenu.item as Edge).target);
                                if (targetToUse) onShowVoltage('1Y', targetToUse);
                                onClose();
                            }}>1Y</Button>
                        </Group>
                    </>
                )}
                {contextMenu.type === 'node' && (
                    <>
                        <Text size="xs" c="dimmed" px="xs" mt={4}>Consumption Time Series</Text>
                        <Group gap={4} px="xs" grow>
                            <Button size="xs" variant="light" onClick={() => {
                                onShowConsumption('1W', contextMenu.item as Node);
                                onClose();
                            }}>1W</Button>
                            <Button size="xs" variant="light" onClick={() => {
                                onShowConsumption('1M', contextMenu.item as Node);
                                onClose();
                            }}>1M</Button>
                            <Button size="xs" variant="light" onClick={() => {
                                onShowConsumption('1Y', contextMenu.item as Node);
                                onClose();
                            }}>1Y</Button>
                        </Group>
                        <Text size="xs" c="dimmed" px="xs" mt={4}>Voltage Distribution</Text>
                        <Group gap={4} px="xs" grow>
                            <Button size="xs" variant="light" color="grape" onClick={() => {
                                onShowVoltage('1W', contextMenu.item as Node);
                                onClose();
                            }}>1W</Button>
                            <Button size="xs" variant="light" color="grape" onClick={() => {
                                onShowVoltage('1M', contextMenu.item as Node);
                                onClose();
                            }}>1M</Button>
                            <Button size="xs" variant="light" color="grape" onClick={() => {
                                onShowVoltage('1Y', contextMenu.item as Node);
                                onClose();
                            }}>1Y</Button>
                        </Group>
                    </>
                )}
            </Stack>
        </div>
    );
});
