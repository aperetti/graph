import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import {
    fetchTopology,
    runPhaseAnalytics,
    fetchConsumption,
    fetchVoltageDistribution,
    fetchMapVoltage,
    nlQuery
} from './index';

describe('API Client', () => {
    beforeEach(() => {
        globalThis.fetch = vi.fn();
    });

    afterEach(() => {
        vi.restoreAllMocks();
    });

    describe('fetchTopology', () => {
        it('should fetch topology data successfully', async () => {
            const mockData = { nodes: [], edges: [] };
            (globalThis.fetch as any).mockResolvedValueOnce({
                ok: true,
                json: async () => mockData
            });

            const result = await fetchTopology();
            expect(globalThis.fetch).toHaveBeenCalledWith('/api/graph/topology');
            expect(result).toEqual(mockData);
        });
    });

    describe('runPhaseAnalytics', () => {
        it('should run phase analytics without dates', async () => {
            const mockData = { some: 'data' };
            (globalThis.fetch as any).mockResolvedValueOnce({
                ok: true,
                json: async () => mockData
            });

            const result = await runPhaseAnalytics('node1');
            expect(globalThis.fetch).toHaveBeenCalledWith('/api/analytics/phase-balance/node1?');
            expect(result).toEqual(mockData);
        });

        it('should run phase analytics with start and end dates', async () => {
            const mockData = { some: 'data' };
            (globalThis.fetch as any).mockResolvedValueOnce({
                ok: true,
                json: async () => mockData
            });

            const result = await runPhaseAnalytics('node1', '2023-01-01', '2023-01-31');
            expect(globalThis.fetch).toHaveBeenCalledWith('/api/analytics/phase-balance/node1?start_time=2023-01-01&end_time=2023-01-31');
            expect(result).toEqual(mockData);
        });

        it('should run phase analytics with only start date', async () => {
            const mockData = { some: 'data' };
            (globalThis.fetch as any).mockResolvedValueOnce({
                ok: true,
                json: async () => mockData
            });

            const result = await runPhaseAnalytics('node1', '2023-01-01');
            expect(globalThis.fetch).toHaveBeenCalledWith('/api/analytics/phase-balance/node1?start_time=2023-01-01&');
            expect(result).toEqual(mockData);
        });

        it('should throw error on non-ok response', async () => {
            (globalThis.fetch as any).mockResolvedValueOnce({
                ok: false
            });

            await expect(runPhaseAnalytics('node1')).rejects.toThrow('Analytics failed');
        });
    });

    describe('fetchConsumption', () => {
        it('should fetch consumption data without dates', async () => {
            const mockData = { total: 100 };
            (globalThis.fetch as any).mockResolvedValueOnce({
                ok: true,
                json: async () => mockData
            });

            const result = await fetchConsumption('node1');
            expect(globalThis.fetch).toHaveBeenCalledWith('/api/analytics/consumption/node1?');
            expect(result).toEqual(mockData);
        });

        it('should fetch consumption data with start and end dates', async () => {
            const mockData = { total: 100 };
            (globalThis.fetch as any).mockResolvedValueOnce({
                ok: true,
                json: async () => mockData
            });

            const result = await fetchConsumption('node1', '2023-01-01', '2023-01-31');
            expect(globalThis.fetch).toHaveBeenCalledWith('/api/analytics/consumption/node1?start_time=2023-01-01&end_time=2023-01-31');
            expect(result).toEqual(mockData);
        });

        it('should fetch consumption data with only start date', async () => {
            const mockData = { total: 100 };
            (globalThis.fetch as any).mockResolvedValueOnce({
                ok: true,
                json: async () => mockData
            });

            const result = await fetchConsumption('node1', '2023-01-01');
            expect(globalThis.fetch).toHaveBeenCalledWith('/api/analytics/consumption/node1?start_time=2023-01-01&');
            expect(result).toEqual(mockData);
        });

        it('should throw error on non-ok response', async () => {
            (globalThis.fetch as any).mockResolvedValueOnce({
                ok: false
            });

            await expect(fetchConsumption('node1')).rejects.toThrow('Failed to fetch consumption');
        });
    });

    describe('fetchVoltageDistribution', () => {
        it('should fetch voltage distribution without dates or degrees', async () => {
            const mockData = { distribution: [] };
            (globalThis.fetch as any).mockResolvedValueOnce({
                ok: true,
                json: async () => mockData
            });

            const result = await fetchVoltageDistribution('node1');
            expect(globalThis.fetch).toHaveBeenCalledWith('/api/analytics/voltage/node1?');
            expect(result).toEqual(mockData);
        });

        it('should fetch voltage distribution with all parameters', async () => {
            const mockData = { distribution: [] };
            (globalThis.fetch as any).mockResolvedValueOnce({
                ok: true,
                json: async () => mockData
            });

            const result = await fetchVoltageDistribution('node1', '2023-01-01', '2023-01-31', 90);
            expect(globalThis.fetch).toHaveBeenCalledWith('/api/analytics/voltage/node1?start_time=2023-01-01&end_time=2023-01-31&degrees=90');
            expect(result).toEqual(mockData);
        });

        it('should fetch voltage distribution with start date and degrees', async () => {
            const mockData = { distribution: [] };
            (globalThis.fetch as any).mockResolvedValueOnce({
                ok: true,
                json: async () => mockData
            });

            const result = await fetchVoltageDistribution('node1', '2023-01-01', undefined, 90);
            expect(globalThis.fetch).toHaveBeenCalledWith('/api/analytics/voltage/node1?start_time=2023-01-01&degrees=90');
            expect(result).toEqual(mockData);
        });

        it('should fetch voltage distribution with degrees of 0', async () => {
            const mockData = { distribution: [] };
            (globalThis.fetch as any).mockResolvedValueOnce({
                ok: true,
                json: async () => mockData
            });

            const result = await fetchVoltageDistribution('node1', undefined, undefined, 0);
            expect(globalThis.fetch).toHaveBeenCalledWith('/api/analytics/voltage/node1?degrees=0');
            expect(result).toEqual(mockData);
        });

        it('should throw error on non-ok response', async () => {
            (globalThis.fetch as any).mockResolvedValueOnce({
                ok: false
            });

            await expect(fetchVoltageDistribution('node1')).rejects.toThrow('Failed to fetch voltage limits');
        });
    });

    describe('fetchMapVoltage', () => {
        it('should fetch map voltage successfully without nodeId', async () => {
            const mockData = { overlay: [] };
            (globalThis.fetch as any).mockResolvedValueOnce({
                ok: true,
                json: async () => mockData
            });

            const result = await fetchMapVoltage('2023-01-01', '2023-01-31', 'daily');
            expect(globalThis.fetch).toHaveBeenCalledWith('/api/analytics/map-voltage?start_time=2023-01-01&end_time=2023-01-31&agg=daily');
            expect(result).toEqual(mockData);
        });

        it('should fetch map voltage successfully with nodeId', async () => {
            const mockData = { overlay: [] };
            (globalThis.fetch as any).mockResolvedValueOnce({
                ok: true,
                json: async () => mockData
            });

            const result = await fetchMapVoltage('2023-01-01', '2023-01-31', 'daily', 'node1');
            expect(globalThis.fetch).toHaveBeenCalledWith('/api/analytics/map-voltage?start_time=2023-01-01&end_time=2023-01-31&agg=daily&node_id=node1');
            expect(result).toEqual(mockData);
        });

        it('should throw error on non-ok response', async () => {
            (globalThis.fetch as any).mockResolvedValueOnce({
                ok: false
            });

            await expect(fetchMapVoltage('2023-01-01', '2023-01-31', 'daily')).rejects.toThrow('Failed to fetch map voltage overlay');
        });
    });

    describe('nlQuery', () => {
        it('should perform natural language query successfully', async () => {
            const mockData = { answer: 'result' };
            (globalThis.fetch as any).mockResolvedValueOnce({
                ok: true,
                json: async () => mockData
            });

            const result = await nlQuery('what is the highest voltage?');
            expect(globalThis.fetch).toHaveBeenCalledWith('/api/agent/query', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query: 'what is the highest voltage?' })
            });
            expect(result).toEqual(mockData);
        });

        it('should throw error on non-ok response', async () => {
            (globalThis.fetch as any).mockResolvedValueOnce({
                ok: false
            });

            await expect(nlQuery('hello')).rejects.toThrow('Query failed');
        });
    });
});
