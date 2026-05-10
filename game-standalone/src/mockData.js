import React, { useState, useEffect } from 'react';

// Standalone mock data hook to decouple from backend
export const useOutbreakData = () => {
  const [stats, setStats] = useState({
    summary: { confirmed_cases: 1242, deaths: 89, nationalities: 14, ship_status: "DEPLOYED" },
    locations: [],
    vessel_route: []
  });
  const [news, setNews] = useState([
    { source: "WHO", title: "Global Alert: Andes Strain mutation detected", date: "10 MAY 2026" },
    { source: "REUTERS", title: "MV Hondius quarantine extended by 14 days", date: "09 MAY 2026" },
    { source: "CDC", title: "Vector shifts observed in South Atlantic", date: "08 MAY 2026" }
  ]);

  return { stats, news, loading: false };
};
