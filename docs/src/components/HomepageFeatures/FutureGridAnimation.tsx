import React, { useEffect, useRef } from 'react';
import * as d3 from 'd3';

const FutureGridAnimation: React.FC = () => {
    const svgRef = useRef<SVGSVGElement>(null);

    useEffect(() => {
        if (!svgRef.current) return;

        const svg = d3.select(svgRef.current);
        const width = 200;
        const height = 200;

        svg.selectAll("*").remove();

        const nodes = [
            { id: 0, x: 100, y: 10 },   // Main trunk top
            { id: 1, x: 100, y: 70 },   // Junction 1
            { id: 2, x: 100, y: 130 },  // Junction 2
            { id: 3, x: 100, y: 190 },  // Main trunk bottom
            
            { id: 4, x: 40, y: 70 },    // Left branch 1
            { id: 5, x: 40, y: 40 },    // Left branch 1 stub up
            { id: 6, x: 70, y: 70 },    // Left branch 1 stub down point
            { id: 7, x: 70, y: 100 },   // Left branch 1 stub down end
            
            { id: 8, x: 160, y: 130 },  // Right branch 2
            { id: 9, x: 160, y: 100 },  // Right branch 2 stub up point
            { id: 10, x: 160, y: 70 },  // Right branch 2 stub up end
            { id: 11, x: 130, y: 130 }, // Right branch 2 stub down point
            { id: 12, x: 130, y: 160 }, // Right branch 2 stub down end
            
            { id: 13, x: 160, y: 30 },  // Top right orphan stub point
            { id: 14, x: 120, y: 30 }   // Top right orphan stub end
        ];

        const links = [
            { source: nodes[0], target: nodes[1] },
            { source: nodes[1], target: nodes[2] },
            { source: nodes[2], target: nodes[3] },
            
            { source: nodes[1], target: nodes[4] },
            { source: nodes[4], target: nodes[5] },
            { source: nodes[6], target: nodes[7] },
            
            { source: nodes[2], target: nodes[8] },
            { source: nodes[8], target: nodes[9] },
            { source: nodes[9], target: nodes[10] },
            { source: nodes[11], target: nodes[12] },
            
            { source: nodes[13], target: nodes[14] }
        ];

        // Draw links
        svg.selectAll("line")
            .data(links)
            .enter()
            .append("line")
            .attr("x1", d => d.source.x)
            .attr("y1", d => d.source.y)
            .attr("x2", d => d.target.x)
            .attr("y2", d => d.target.y)
            .attr("stroke", "var(--ifm-color-primary)")
            .attr("stroke-width", 2)
            .attr("opacity", 0.3);

        // Draw nodes
        svg.selectAll("circle.node")
            .data(nodes)
            .enter()
            .append("circle")
            .attr("class", "node")
            .attr("cx", d => d.x)
            .attr("cy", d => d.y)
            .attr("r", 4)
            .attr("fill", "var(--ifm-color-primary)");

        const animateParticle = (link: any) => {
            const particle = svg.append("circle")
                .attr("r", 2.5)
                .attr("fill", "var(--ifm-color-primary-lightest)")
                .attr("cx", link.source.x)
                .attr("cy", link.source.y);

            particle.transition()
                .duration(1000 + Math.random() * 1500)
                .ease(d3.easeLinear)
                .attr("cx", link.target.x)
                .attr("cy", link.target.y)
                .on("end", () => {
                    particle.remove();
                    animateParticle(link);
                });
        };

        links.forEach(link => animateParticle(link));

        // Node pulse
        const pulse = () => {
            svg.selectAll("circle.node")
                .transition()
                .duration(1500)
                .attr("r", 5)
                .transition()
                .duration(1500)
                .attr("r", 4)
                .on("end", pulse);
        };
        pulse();

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

export default FutureGridAnimation;
