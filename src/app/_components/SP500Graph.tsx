"use client";
import React, { useEffect, useState } from "react";
import Papa from "papaparse";

type SPIndex = {
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
  const [data, setData] = useState<SPIndex[]>([]);

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
            console.log("Parsed:", result.data);
            setData(result.data as any);
          },
          header: true,
        });
      } catch (err) {
        throw Error("Error fetching CSV");
      }
    }
    fetchData();
  }, []);

  console.log(data);

  return <div>Hi</div>;
};
