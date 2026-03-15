import { useState, useMemo } from 'react';
import { Select, Group, Text, Box, ActionIcon, Popover, Tooltip } from '@mantine/core';
import { Search } from 'lucide-react';
import type { Node, Edge } from '../../../shared/types';

interface GlobalSearchProps {
  nodes: Node[];
  edges: Edge[];
  onSearchSelect: (item: Node | Edge) => void;
  isMobile?: boolean;
}

export function GlobalSearch({ nodes, edges, onSearchSelect, isMobile }: GlobalSearchProps) {
  const [searchValue, setSearchValue] = useState('');
  const [opened, setOpened] = useState(false);

  const searchData = useMemo(() => {
    const nodeItems = nodes.map(node => ({
        value: node.id,
        label: `${node.name || node.id}`,
        type: 'node' as const,
        item: node
    }));

    const edgeItems = edges.map(edge => ({
        value: edge.id || `${edge.source}-${edge.target}`,
        label: `${nodes.find(n => n.id === edge.source)?.name || edge.source} → ${nodes.find(n => n.id === edge.target)?.name || edge.target}`,
        type: 'edge' as const,
        item: edge
    }));

    return [...nodeItems, ...edgeItems];
  }, [nodes, edges]);

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

  const selectElement = (
    <Select
      placeholder="Search nodes..."
      leftSection={<Search size={16} />}
      data={filteredData}
      searchValue={searchValue}
      onSearchChange={setSearchValue}
      onChange={(value) => {
        if (value) {
          const selected = searchData.find(item => item.value === value);
          if (selected) onSearchSelect(selected.item);
          setSearchValue(''); // Clear search after selection
          setOpened(false); // Close popover on selection
        }
      }}
      searchable
      nothingFoundMessage="No nodes found"
      maxDropdownHeight={300}
      autoFocus={isMobile}
      comboboxProps={{ withinPortal: true, zIndex: 1000 }}
      styles={{
        root: { width: isMobile ? 'calc(100vw - 120px)' : 300 },
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
        const item = (option as any).item;
        const type = (option as any).type;
        return (
          <Group gap="sm">
            <Box>
              <Text size="sm" fw={500} c="white">
                {option.label}
              </Text>
              <Text size="xs" c="dimmed">
                {type === 'node' ? `ID: ${option.value} • ${item?.type}` : `ID: ${option.value} • Edge`}
              </Text>
            </Box>
          </Group>
        );
      }}
    />
  );

  if (isMobile) {
    return (
      <Popover 
        opened={opened} 
        onChange={setOpened} 
        width={320}
        position="bottom-end" 
        shadow="md"
        offset={10}
      >
        <Popover.Target>
          <Tooltip label="Search Map" position="bottom" withArrow>
            <ActionIcon
              variant="filled"
              color={opened ? "blue" : "gray"}
              size="xl"
              radius="md"
              onClick={() => setOpened(o => !o)}
              style={{
                boxShadow: '0 4px 12px rgba(0,0,0,0.3)',
                border: '1px solid rgba(255,255,255,0.1)',
              }}
            >
              <Search size={20} />
            </ActionIcon>
          </Tooltip>
        </Popover.Target>
        <Popover.Dropdown 
          bg="rgba(26, 27, 30, 0.95)" 
          style={{ 
            backdropFilter: 'blur(10px)', 
            border: '1px solid rgba(255,255,255,0.1)', 
            padding: '12px',
            boxShadow: '0 8px 24px rgba(0,0,0,0.4)'
          }}
        >
          {selectElement}
        </Popover.Dropdown>
      </Popover>
    );
  }

  return selectElement;
}
