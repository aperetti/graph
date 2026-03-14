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

        // Create a mask instead of a clipPath for feathering
        const defs = svg.append("defs");
        
        // Add a blur filter for the feathering effect
        const filter = defs.append("filter")
            .attr("id", "feather-blur")
            .attr("x", "-50%")
            .attr("y", "-50%")
            .attr("width", "200%")
            .attr("height", "200%");
        
        filter.append("feGaussianBlur")
            .attr("in", "SourceGraphic")
            .attr("stdDeviation", "4"); // Adjust this for feather intensity

        const mask = defs.append("mask")
            .attr("id", "bean-mask");

        // Background of mask should be black (transparent)
        mask.append("rect")
            .attr("width", width)
            .attr("height", height)
            .attr("fill", "black");

        // The morphing shape in the mask should be white (opaque)
        const maskPath = mask.append("path")
            .attr("fill", "white")
            .attr("filter", "url(#feather-blur)");

        const getPath = () => {
            const xShift = (Math.random() - 0.5) * 60;
            const yShift = (Math.random() - 0.5) * 40;
            const scale = 0.8 + Math.random() * 0.4;
            
            return `M ${width * 0.05 * scale + xShift},${height * 0.5 + yShift}
                    C ${width * 0.05 * scale + xShift},${height * 0.05 * scale + yShift} ${width * 0.95 * scale + xShift},${height * 0.05 * scale + yShift} ${width * 0.95 * scale + xShift},${height * 0.4 + yShift}
                    C ${width * 0.95 * scale + xShift},${height * 0.8 * scale + yShift} ${width * 0.5 * scale + xShift},${height * 0.7 + yShift} ${width * 0.5 * scale + xShift},${height * 0.95 * scale + yShift}
                    C ${width * 0.5 * scale + xShift},${height * 1.05 * scale + yShift} ${width * 0.05 * scale + xShift},${height * 0.95 * scale + yShift} ${width * 0.05 * scale + xShift},${height * 0.5 + yShift} Z`;
        };

        // Set initial path
        maskPath.attr("d", getPath());

        const morph = () => {
            maskPath.transition()
                .duration(800 + Math.random() * 600) // Much faster transitions (was 1500+)
                .ease(d3.easeSinInOut)
                .attr("d", getPath())
                .on("end", morph);
        };

        morph();

        const columns = 8;
        const colWidth = width / columns;

        const createNumber = (col: number) => {
            const x = col * colWidth + colWidth / 2;
            const duration = 300 + Math.random() * 200;
            const trailCount = 5;

            for (let i = 0; i < trailCount; i++) {
                const val = Math.floor(Math.random() * 10).toString();
                const opacity = i === 0 ? 1 : 0.8 / (i * 1.5);
                const delay = i * 40;

                const text = svg.append("text")
                    .attr("x", x)
                    .attr("y", -20)
                    .attr("text-anchor", "middle")
                    .attr("fill", "var(--ifm-color-primary)")
                    .attr("font-family", "monospace")
                    .attr("font-size", i === 0 ? "14px" : "12px")
                    .attr("opacity", 0)
                    .attr("mask", "url(#bean-mask)") // Apply the feathered mask
                    .text(val);

                text.transition("move")
                    .delay(delay)
                    .duration(duration)
                    .ease(d3.easeLinear)
                    .attr("y", height + 20)
                    .on("end", () => {
                        text.remove();
                        // Only the lead digit spawns the next set to maintain density
                        if (i === 0) createNumber(col);
                    });

                text.transition("opacity")
                    .delay(delay)
                    .duration(100)
                    .attr("opacity", opacity)
                    .transition()
                    .delay(duration - 200)
                    .duration(100)
                    .attr("opacity", 0);
            }
        };

        for (let i = 0; i < columns; i++) {
            // Initial delay spread
            setTimeout(() => {
                for (let j = 0; j < 5; j++) { // Reduced initial count as they now have trails
                    setTimeout(() => createNumber(i), j * 300);
                }
            }, i * 150);
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
