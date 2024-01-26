import { useEffect, useMemo, useRef, useState } from "react";
import * as d3 from "d3";
import { ISPIndex } from "../SP500Graph";

type SP500ChartProps = {
  height: number;
  width: number;
  rawData: ISPIndex[];
};

type DataPoint = { x: Date; y: number };

export const SP500Chart = ({ height, width, rawData }: SP500ChartProps) => {
  const data = rawData.map((data) => {
    return {
      x: new Date(data.Date),
      y: parseInt(data.SP500),
    };
  });

  let dimensions = {
    width: Math.min(global.window ? window.innerWidth * 0.9 : 200, width),
    height: height,
    margins: {
      top: 15,
      right: 15,
      bottom: 40,
      left: 60,
    },
    boundedWidth: 0,
    boundedHeight: 0,
  };
  dimensions.boundedWidth = dimensions.width - dimensions.margins.left;
  dimensions.boundedHeight =
    dimensions.height - dimensions.margins.top - dimensions.margins.bottom;

  const axesRef = useRef(null);

  // Y axis
  const [yMin, yMax] = d3.extent(data, (d) => d.y);
  const yScale = useMemo(() => {
    return d3
      .scaleLinear()
      .domain([yMin || 0, yMax || 0])
      .range([dimensions.boundedHeight, 0]);
  }, [yMin, yMax, dimensions.boundedHeight]);

  // X axis
  const [xMin, xMax] = d3.extent(data, (d) => d.x);
  const xScale = useMemo(() => {
    return d3
      .scaleTime()
      .domain([xMin || 0, xMax || 0])
      .range([0, dimensions.boundedWidth]);
  }, [xMin, xMax, dimensions.boundedWidth]);

  useEffect(() => {
    const svgElement = d3.select(axesRef.current);
    svgElement.selectAll("*").remove();
    const xAxisGenerator = d3.axisBottom(xScale);
    svgElement
      .append("g")
      .attr("transform", "translate(0," + dimensions.boundedHeight + ")")
      .call(xAxisGenerator);

    const yAxisGenerator = d3.axisLeft(yScale);
    svgElement.append("g").call(yAxisGenerator);
  }, [xScale, yScale, dimensions.boundedHeight]);

  const lineBuilder = d3
    .line<DataPoint>()
    .x((d) => xScale(d.x))
    .y((d) => yScale(d.y));
  const linePath = lineBuilder(data);

  if (!linePath) {
    return null;
  }

  console.log(JSON.stringify(data));
  console.log(xScale.domain());

  return (
    <div>
      <svg width={dimensions.width} height={dimensions.height}>
        <g
          width={dimensions.boundedWidth}
          height={dimensions.boundedHeight}
          transform={`translate(${[
            dimensions.margins.left,
            dimensions.margins.top,
          ].join(",")})`}
        >
          <path
            d={linePath}
            opacity={1}
            stroke="#9a6fb0"
            fill="none"
            strokeWidth={2}
          />
        </g>
        <g
          width={dimensions.boundedWidth}
          height={dimensions.boundedHeight}
          ref={axesRef}
          transform={`translate(${[
            dimensions.margins.left,
            dimensions.margins.top,
          ].join(",")})`}
        />
      </svg>
    </div>
  );
};
