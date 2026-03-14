import { useState, useMemo } from 'react';
import { Select, Group, Text, Box } from '@mantine/core';
import { Search } from 'lucide-react';
import type { Node } from '../../../shared/types';

interface GlobalSearchProps {
  nodes: Node[];
  onNodeSelect: (node: Node) => void;
}

export function GlobalSearch({ nodes, onNodeSelect }: GlobalSearchProps) {
  const [searchValue, setSearchValue] = useState('');

  const searchData = useMemo(() => {
    return nodes.map(node => ({
        value: node.id,
        label: `${node.name || node.id}`,
        node: node
    }));
  }, [nodes]);

  // Simple fuzzy filter: matches if query is a substring of name or ID (case-insensitive)
  const filteredData = useMemo(() => {
    if (!searchValue) return searchData.slice(0, 10);
    const lowerQuery = searchValue.toLowerCase();
    return searchData
      .filter(item => 
        item.label.toLowerCase().includes(lowerQuery) || 
        item.value.toLowerCase().includes(lowerQuery)
      )
      .slice(0, 20); // Limit results for performance and UI
  }, [searchData, searchValue]);

  return (
    <Select
      placeholder="Search nodes..."
      leftSection={<Search size={16} />}
      data={filteredData}
      searchValue={searchValue}
      onSearchChange={setSearchValue}
      onChange={(value) => {
        if (value) {
          const selected = nodes.find(n => n.id === value);
          if (selected) onNodeSelect(selected);
          setSearchValue(''); // Clear search after selection
        }
      }}
      searchable
      nothingFoundMessage="No nodes found"
      maxDropdownHeight={300}
      styles={{
        root: { width: 300 },
        input: {
          backgroundColor: 'rgba(26, 27, 30, 0.7)',
          backdropFilter: 'blur(10px)',
          border: '1px solid rgba(255, 255, 255, 0.1)',
          color: '#fff',
        },
        dropdown: {
          backgroundColor: 'rgba(26, 27, 30, 0.95)',
          backdropFilter: 'blur(10px)',
          border: '1px solid rgba(255, 255, 255, 0.1)',
        },
        option: {
            color: '#eee',
            '&[data-selected]': {
                backgroundColor: 'rgba(51, 154, 240, 0.3)',
            },
            '&[data-combobox-selected]': {
                backgroundColor: 'rgba(51, 154, 240, 0.3)',
            }
        }
      }}
      renderOption={({ option }) => {
        const node = (option as any).node as Node;
        return (
          <Group gap="sm">
            <Box>
              <Text size="sm" fw={500} c="white">
                {option.label}
              </Text>
              <Text size="xs" c="dimmed">
                ID: {option.value} • {node?.type}
              </Text>
            </Box>
          </Group>
        );
      }}
    />
  );
}
