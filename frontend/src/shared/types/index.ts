export interface Node {
    id: string;
    type: string;
    name: string;
    position: [number, number];
    is_open?: boolean;
    circuit_id?: string;
    model_id?: string;
}

export interface Edge {
    source: string;
    target: string;
    id?: string;
    phases?: string[];
    sourcePosition: [number, number];
    targetPosition: [number, number];
    circuit_id?: string;
    model_id?: string;
}
