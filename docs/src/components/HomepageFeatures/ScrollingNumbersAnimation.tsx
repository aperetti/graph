import React, { useEffect, useRef } from 'react';
import * as d3 from 'd3';

const ScrollingNumbersAnimation: React.FC = () => {
    const containerRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (!containerRef.current) return;

        const container = d3.select(containerRef.current);
        const width = 200;
        const height = 120; // Shorter height

        container.selectAll("*").remove();

        const svg = container.append("svg")
            .attr("width", width)
            .attr("height", height)
            .style("background", "transparent");

        const columns = 8; // More columns for better density
        const colWidth = width / columns;

        const createNumber = (col: number) => {
            const x = col * colWidth + colWidth / 2;
            const val = Math.floor(Math.random() * 10).toString();
            
            const text = svg.append("text")
                .attr("x", x)
                .attr("y", -10)
                .attr("text-anchor", "middle")
                .attr("fill", "var(--ifm-color-primary)")
                .attr("font-family", "monospace")
                .attr("font-size", "14px")
                .attr("opacity", 0)
                .text(val);
            // Movement transition
            text.transition("move")
                .duration(800 + Math.random() * 1000)
                .ease(d3.easeLinear)
                .attr("y", height + 20)
                .on("end", () => {
                    text.remove();
                    createNumber(col);
                });

            // Opacity transition (Fade in then fade out)
            text.transition("opacity")
                .duration(300)
                .attr("opacity", 0.8)
                .transition()
                .delay(500 + Math.random() * 500)
                .duration(300)
                .attr("opacity", 0);
        };

        for (let i = 0; i < columns; i++) {
            // Initial delay spread
            setTimeout(() => {
                for(let j=0; j<10; j++) {
                    setTimeout(() => createNumber(i), j * 150);
                }
            }, i * 200);
        }

    }, []);

    return (
        <div
            ref={containerRef}
            style={{ width: '200px', height: '120px', margin: '0 auto', overflow: 'hidden' }}
        />
    );
};

export default ScrollingNumbersAnimation;
