import React, { useEffect, useRef } from 'react';
import * as d3 from 'd3';

const AmiInsightsAnimation: React.FC = () => {
    const svgRef = useRef<SVGSVGElement>(null);

    useEffect(() => {
        if (!svgRef.current) return;

        const svg = d3.select(svgRef.current);
        const width = 200;
        const height = 200;
        const centerX = width / 2;
        const centerY = height / 2;

        svg.selectAll("*").remove();

        // Meter body
        svg.append("circle")
            .attr("cx", centerX)
            .attr("cy", centerY)
            .attr("r", 40)
            .attr("fill", "none")
            .attr("stroke", "var(--ifm-color-primary)")
            .attr("stroke-width", 3);

        // Meter inner glow
        svg.append("circle")
            .attr("cx", centerX)
            .attr("cy", centerY)
            .attr("r", 35)
            .attr("fill", "var(--ifm-color-primary)")
            .attr("opacity", 0.2);

        const createPing = () => {
            const ping = svg.append("circle")
                .attr("cx", centerX)
                .attr("cy", centerY)
                .attr("r", 40)
                .attr("fill", "none")
                .attr("stroke", "var(--ifm-color-primary)")
                .attr("stroke-width", 2)
                .attr("opacity", 0.8);

            ping.transition()
                .duration(2000)
                .ease(d3.easeCubicOut)
                .attr("r", 100)
                .attr("opacity", 0)
                .on("end", () => ping.remove());
        };

        const interval = setInterval(createPing, 800);

        return () => clearInterval(interval);
    }, []);

    return (
        <svg
            ref={svgRef}
            width="200"
            height="200"
            viewBox="0 0 200 200"
            style={{ display: 'block', margin: '0 auto' }}
        />
    );
};

export default AmiInsightsAnimation;
