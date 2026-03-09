import { memo } from 'react';
import { Paper, Title, TextInput, Button, Code } from '@mantine/core';
import { Search } from 'lucide-react';

interface Props {
    query: string;
    setQuery: (query: string) => void;
    onNlQuery: () => void;
    nlResult: string;
}

export const NaturalLanguagePanel = memo(function NaturalLanguagePanel({
    query,
    setQuery,
    onNlQuery,
    nlResult
}: Props) {
    return (
        <Paper p="xl" radius="md" withBorder style={{
            background: 'rgba(26, 27, 30, 0.9)',
            backdropFilter: 'blur(10px)'
        }}>
            <Title order={4} mb="sm">Natural Language Agent</Title>
            <TextInput
                placeholder="e.g. Find unbalanced transformers..."
                value={query}
                onChange={(e) => setQuery(e.currentTarget.value)}
                mb="xs"
            />
            <Button fullWidth variant="light" color="cyan" leftSection={<Search size={16} />} onClick={onNlQuery}>
                Generate Agent SQL
            </Button>
            {nlResult && <Code block mt="md">{nlResult}</Code>}
        </Paper>
    );
});
