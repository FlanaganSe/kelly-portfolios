"use client";
import React, { useEffect, useRef, useState } from "react";
import Papa from "papaparse";
import { useDimensions } from "../hooks/useDimensions";
import { SP500Chart } from "./Charts/SP500Chart";

export type ISPIndex = {
  Date: Date;
  Earnings: string;
  Dividend: string;
  "Long Interest Rate": string;
  PE10: string;
  "Real Dividend": string;
  "Real Earnings": string;
  "Real Price": string;
  SP500: string;
};

export const SP500Graph = () => {
  const [data, setData] = useState<ISPIndex[]>([]);

  useEffect(() => {
    async function fetchData() {
      try {
        const res = await fetch("/data_csv.csv");
        if (!res.body) throw "No response body";

        const reader = res.body.getReader();
        const result = await reader.read();
        const decoder = new TextDecoder("utf-8");
        const csv = decoder.decode(result.value);
        Papa.parse(csv, {
          complete: (result) => {
            const resData = result.data;
            const slicedData = resData.slice(
              resData.length - 11,
              resData.length - 1
            );
            setData(slicedData as ISPIndex[]);
          },
          header: true,
        });
      } catch (err) {
        throw Error("Error fetching CSV");
      }
    }
    fetchData();
  }, []);

  // console.log("data", data);

  return <SP500Chart height={500} width={500} rawData={data} />;
};
