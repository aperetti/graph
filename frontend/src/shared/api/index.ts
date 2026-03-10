import type { Node, Edge } from "../types";

export interface TopologyResponse {
    nodes: Node[];
    edges: Edge[];
}

export const fetchTopology = async (): Promise<TopologyResponse> => {
    const res = await fetch('/api/graph/topology');
    return res.json();
};

export const runPhaseAnalytics = async (nodeId: string, startDate?: string, endDate?: string) => {
    let url = `/api/analytics/phase-balance/${nodeId}?`;
    if (startDate) url += `start_time=${startDate}&`;
    if (endDate) url += `end_time=${endDate}`;
    const res = await fetch(url);
    if (!res.ok) {
        throw new Error('Analytics failed');
    }
    return res.json();
};

export const fetchConsumption = async (nodeId: string, startDate?: string, endDate?: string) => {
    let url = `/api/analytics/consumption/${nodeId}?`;
    if (startDate) url += `start_time=${startDate}&`;
    if (endDate) url += `end_time=${endDate}`;
    const res = await fetch(url);
    if (!res.ok) {
        throw new Error('Failed to fetch consumption');
    }
    return res.json();
};

export const fetchVoltageDistribution = async (nodeId: string, startDate?: string, endDate?: string, degrees?: number | null) => {
    let url = `/api/analytics/voltage/${nodeId}?`;
    if (startDate) url += `start_time=${startDate}&`;
    if (endDate) url += `end_time=${endDate}&`;
    if (degrees !== undefined) url += `degrees=${degrees}`;
    const res = await fetch(url);
    if (!res.ok) {
        throw new Error('Failed to fetch voltage limits');
    }
    return res.json();
};

export const fetchMapVoltage = async (startDate: string, endDate: string, agg: string, nodeId?: string | null) => {
    let url = `/api/analytics/map-voltage?start_time=${startDate}&end_time=${endDate}&agg=${agg}`;
    if (nodeId) url += `&node_id=${nodeId}`;
    const res = await fetch(url);
    if (!res.ok) {
        throw new Error('Failed to fetch map voltage overlay');
    }
    return res.json();
};

export const nlQuery = async (query: string) => {
    const res = await fetch('/api/agent/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query })
    });
    if (!res.ok) throw new Error('Query failed');
    return res.json();
};
