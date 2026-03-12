import { useState, useEffect } from 'react';
import { Box, Text, Stack, Group } from '@mantine/core';
import { Activity, Zap, Cpu, Radio } from 'lucide-react';

const PHRASES = [
    "Energizing cap banks...",
    "Pinging AMI meters...",
    "Unifying phase angles...",
    "Verifying relay coordination...",
    "Measuring grid inertia...",
    "Calculating power flows...",
    "Tuning PID controllers...",
    "Inspecting transformers...",
    "Balancing three-phase loads...",
    "Polling SCADA RTUs..."
];

export function ScadaLoadingAnimation({ estimatedRows }: { estimatedRows?: number }) {
    const [phraseIndex, setPhraseIndex] = useState(0);

    useEffect(() => {
        const interval = setInterval(() => {
            setPhraseIndex((prev) => (prev + 1) % PHRASES.length);
        }, 1500); // cycle every 1.5 seconds

        return () => clearInterval(interval);
    }, []);

    return (
        <Box style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', width: '100%' }}>
            <Stack align="center" gap="md">
                <Box style={{ position: 'relative', width: '120px', height: '120px' }}>
                    {/* Background Grid Pattern */}
                    <Box
                        style={{
                            position: 'absolute',
                            inset: 0,
                            backgroundImage: 'linear-gradient(rgba(51, 154, 240, 0.2) 1px, transparent 1px), linear-gradient(90deg, rgba(51, 154, 240, 0.2) 1px, transparent 1px)',
                            backgroundSize: '20px 20px',
                            backgroundPosition: 'center center',
                            border: '1px solid rgba(51, 154, 240, 0.3)',
                            borderRadius: '8px',
                            overflow: 'hidden'
                        }}
                    >
                        {/* Scanning beam effect */}
                        <Box
                            style={{
                                position: 'absolute',
                                top: 0,
                                bottom: 0,
                                left: '-100%',
                                width: '50%',
                                background: 'linear-gradient(90deg, transparent, rgba(51, 154, 240, 0.5), transparent)',
                                animation: `scan 2.5s infinite linear`
                            }}
                        />
                    </Box>

                    {/* Nodes and Icons */}
                    <Group style={{ position: 'relative', width: '100%', height: '100%' }} justify="center" align="center">
                        <Stack gap="sm" align="center">
                            <Group gap="sm" justify="center">
                                <Activity size={24} color="#339af0" style={{ animation: `pulse 2s infinite ease-in-out` }} />
                                <Cpu size={24} color="#339af0" style={{ animation: `pulse 2s infinite ease-in-out 0.5s` }} />
                            </Group>
                            <Group gap="sm" justify="center">
                                <Radio size={24} color="#339af0" style={{ animation: `pulse 2s infinite ease-in-out 1s` }} />
                                <Zap size={24} color="#339af0" style={{ animation: `pulse 2s infinite ease-in-out 1.5s` }} />
                            </Group>
                        </Stack>
                    </Group>
                </Box>

                <Group gap={0}>
                    <Text
                        size="sm"
                        c="blue.4"
                        ff="monospace"
                        fw={600}
                        style={{
                            textAlign: 'center',
                            minWidth: '240px',
                            textTransform: 'uppercase',
                            letterSpacing: '1px'
                        }}
                    >
                        {PHRASES[phraseIndex]}
                    </Text>
                    <Text
                        size="sm"
                        c="blue.4"
                        ff="monospace"
                        style={{ animation: 'blink 1s step-end infinite' }}
                    >
                        _
                    </Text>
                </Group>

                {estimatedRows !== undefined && estimatedRows > 0 && (
                    <Text size="xs" c="dimmed" ff="monospace" mt={-10}>
                        Querying ~{estimatedRows.toLocaleString()} reads...
                    </Text>
                )}

                <style>{`
                    @keyframes blink {
                        0%, 100% { opacity: 1; }
                        50% { opacity: 0; }
                    }
                    @keyframes pulse {
                        0%, 100% { opacity: 0.3; transform: scale(0.95); }
                        50% { opacity: 1; transform: scale(1.05); color: #339af0; }
                    }
                    @keyframes scan {
                        0% { background-position: -100% 0; }
                        100% { background-position: 200% 0; }
                    }
                `}</style>
            </Stack>
        </Box>
    );
}
