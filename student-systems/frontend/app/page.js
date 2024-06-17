"use client";
import Link from "next/link";
import { useState, useEffect } from "react";
import { Button } from "@mui/material";
import ListItemButton from "@mui/material/ListItemButton";
import List from "@mui/material/List";

export default function Home() {
  const [reso, setReso] = useState([]);
  const [timeneeded, setTimeNeeded] = useState("");
  async function getSem() {
    // await fetch('/api/sems')
    // .then(response => response.json())
    // .then(data => {
    //    console.log(data)
    //    setTimeNeeded(data.time)
    //    setReso(data.list)
    // })
    const data = {
      time: "0.39707446098327637 seconds",
      list: [
        {
          year: "112",
          sem: "2",
          link: "Subj.jsp?format=-2&year=112&sem=2",
        },
        {
          year: "112",
          sem: "1",
          link: "Subj.jsp?format=-2&year=112&sem=1",
        },
      ],
    };

    setTimeNeeded(data.time);
    setReso(data.list);
  }
  useEffect(() => {
    getSem();
  }, []);
  const [selectedIndex, setSelectedIndex] = useState(1);
  return (
    <>
      <main className="flex flex-col items-center justify-center gap-6">
        <Link href="/hey">Navigate to Hey</Link>
        <p>Time spent: {timeneeded} </p>

        <Button variant="outlined" onClick={getSem}>
          click
        </Button>

        <List className="border-2 border-red-400">
          {reso?.map((res) => (
            <ListItemButton>
              <p>{res.year}</p>
              <p>{res.sem}</p>
              <p>{res.link}</p>
            </ListItemButton>
          ))}
        </List>



        
      </main>
    </>
  );
}
