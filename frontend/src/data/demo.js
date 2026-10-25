export const SAMPLE_SCHEDULE = `Fall 2026 — Aditya Singh
Week of Mon 2026-10-26

CS 25100 Data Structures and Algorithms
Lecture  LWSN B155  MWF  8:30 AM – 9:20 AM

PHYS 17200 Modern Mechanics
Lecture  PHYS 112  MWF  9:30 AM – 10:20 AM

ENGR 13100 Transforming Ideas to Innovation
Lab  ARMS 1028  MW  10:30 AM – 11:20 AM

COM 11400 Fundamentals of Speech Communication
Lecture  BRNG 2280  MW  11:24 AM – 12:20 PM

MA 26100 Multivariate Calculus
Lecture  MATH 175  MWF  1:30 PM – 2:20 PM
`;

export const SAMPLE_CAPTION = `hackclubpurdue
Oct 26

Hack Club Meeting tonight 💻
Come build, hang out, and ship something small.

Monday Oct 26 · 6:00–7:00 PM
Beering Hall BRNG 1268
Free snacks. All majors welcome.
`;

export function demoEvents(day) {
  return [
    {
      title: "CS 25100 Data Structures",
      source: "schedule",
      building: "LWSN",
      date: day,
      start: "08:30",
      end: "09:20",
      description: "Lecture · LWSN B155",
    },
    {
      title: "PHYS 17200 Modern Mechanics",
      source: "schedule",
      building: "PHYS",
      date: day,
      start: "09:30",
      end: "10:20",
      description: "Lecture · PHYS 112",
    },
    {
      title: "ENGR 13100 Innovation Lab",
      source: "schedule",
      building: "ARMS",
      date: day,
      start: "10:30",
      end: "11:20",
      description: "Lab · ARMS 1028",
    },
    {
      title: "COM 11400 Speech",
      source: "schedule",
      building: "BRNG",
      date: day,
      start: "11:24",
      end: "12:20",
      description: "Lecture · BRNG 2280 — 4 min after lab across campus",
    },
    {
      title: "MA 26100 Multivariate Calculus",
      source: "schedule",
      building: "MATH",
      date: day,
      start: "13:30",
      end: "14:20",
      description: "Lecture · MATH 175",
    },
    {
      title: "Hack Club Meeting",
      source: "instagram",
      building: "BRNG",
      date: day,
      start: "18:00",
      end: "19:00",
      description: "Build, hang out, and ship something small. Free snacks.",
    },
  ];
}
