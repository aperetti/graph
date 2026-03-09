import { memo, useState } from 'react';
import { Box, Group, ActionIcon, Popover, NumberInput, Text, Stack } from '@mantine/core';
import { Settings } from 'lucide-react';

interface Props {
    voltageScale: {
        criticalHigh: number;
        highWarning: number;
        lowWarning: number;
        criticalLow: number;
        baseVoltage: number;
    };
    setVoltageScale: (scale: any) => void;
    visible: boolean;
}

export const VoltageScalePanel = memo(function VoltageScalePanel({
    voltageScale,
    setVoltageScale,
    visible
}: Props) {
    const [popoverOpened, setPopoverOpened] = useState(false);

    if (!visible) return null;

    return (
        <Box style={{
            position: 'absolute',
            top: 20,
            left: 20,
            zIndex: 10,
            background: 'rgba(26, 27, 30, 0.9)',
            backdropFilter: 'blur(10px)',
            padding: '12px 16px',
            borderRadius: '8px',
            border: '1px solid #373A40',
            pointerEvents: 'auto',
            display: 'flex',
            flexDirection: 'column',
            gap: 8
        }}>
            <Group justify="space-between" align="center">
                <Text size="sm" fw={600} c="#C1C2C5">Voltage Scale</Text>
                <Popover width={300} position="bottom-start" withArrow shadow="md" opened={popoverOpened} onChange={setPopoverOpened}>
                    <Popover.Target>
                        <ActionIcon variant="subtle" color="gray" size="sm" onClick={() => setPopoverOpened((o) => !o)}>
                            <Settings size={14} />
                        </ActionIcon>
                    </Popover.Target>
                    <Popover.Dropdown style={{ background: 'rgba(26, 27, 30, 0.95)', backdropFilter: 'blur(10px)', border: '1px solid #373A40' }}>
                        <Stack gap="xs">
                            <Text size="sm" fw={600}>Configure Thresholds (pu)</Text>

                            <Group grow>
                                <NumberInput
                                    label="Critical High"
                                    value={voltageScale.criticalHigh}
                                    onChange={(val) => setVoltageScale({ ...voltageScale, criticalHigh: Number(val) })}
                                    step={0.01}
                                    min={1.0}
                                    max={1.2}
                                    size="xs"
                                />
                                <NumberInput
                                    label="High Warning"
                                    value={voltageScale.highWarning}
                                    onChange={(val) => setVoltageScale({ ...voltageScale, highWarning: Number(val) })}
                                    step={0.01}
                                    min={1.0}
                                    max={1.1}
                                    size="xs"
                                />
                            </Group>

                            <Group grow>
                                <NumberInput
                                    label="Low Warning"
                                    value={voltageScale.lowWarning}
                                    onChange={(val) => setVoltageScale({ ...voltageScale, lowWarning: Number(val) })}
                                    step={0.01}
                                    min={0.8}
                                    max={1.0}
                                    size="xs"
                                />
                                <NumberInput
                                    label="Critical Low"
                                    value={voltageScale.criticalLow}
                                    onChange={(val) => setVoltageScale({ ...voltageScale, criticalLow: Number(val) })}
                                    step={0.01}
                                    min={0.7}
                                    max={0.99}
                                    size="xs"
                                />
                            </Group>

                            <NumberInput
                                label="Base Voltage (V)"
                                value={voltageScale.baseVoltage}
                                onChange={(val) => setVoltageScale({ ...voltageScale, baseVoltage: Number(val) })}
                                step={1}
                                min={1}
                                size="xs"
                            />
                        </Stack>
                    </Popover.Dropdown>
                </Popover>
            </Group>

            <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                <div style={{ width: 16, height: 16, background: 'rgba(255, 107, 107, 0.8)', borderRadius: 4 }} title={`> ${voltageScale.criticalHigh} pu`} />
                <span style={{ fontSize: 10, color: '#909296', marginRight: 4 }}>&gt;{voltageScale.criticalHigh}</span>

                <div style={{ width: 16, height: 16, background: 'rgba(250, 150, 80, 0.8)', borderRadius: 4 }} title={`${voltageScale.highWarning} - ${voltageScale.criticalHigh} pu`} />
                <span style={{ fontSize: 10, color: '#909296', marginRight: 4 }}>{voltageScale.highWarning}</span>

                <div style={{ width: 16, height: 16, background: 'rgba(46, 204, 113, 0.8)', borderRadius: 4 }} title={`${voltageScale.lowWarning} - ${voltageScale.highWarning} pu`} />
                <span style={{ fontSize: 10, color: '#909296', marginRight: 4 }}>{voltageScale.lowWarning}</span>

                <div style={{ width: 16, height: 16, background: 'rgba(241, 196, 15, 0.8)', borderRadius: 4 }} title={`${voltageScale.criticalLow} - ${voltageScale.lowWarning} pu`} />
                <span style={{ fontSize: 10, color: '#909296', marginRight: 4 }}>{voltageScale.criticalLow}</span>

                <div style={{ width: 16, height: 16, background: 'rgba(142, 68, 173, 0.8)', borderRadius: 4 }} title={`< ${voltageScale.criticalLow} pu`} />
                <span style={{ fontSize: 10, color: '#909296' }}>&lt;{voltageScale.criticalLow}</span>
            </div>
            <div style={{ fontSize: 11, color: '#909296' }}>Base: {voltageScale.baseVoltage}V</div>
        </Box>
    );
});
