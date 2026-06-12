/**
 * Main site copy — edit freely. Used for the hero, navigation labels, and
 * document title.
 *
 * Hero stats are from `crash_cost_eval.csv` (Maryland police-reported crashes,
 * comprehensive costs in 2025 USD). Population: sum of 2024 ACS county
 * totals in the map (~6.21M). Recompute when source data changes.
 */
export const siteContent = {
  documentTitle: "Maryland Crash Costs | Interactive Map",

  /** Used in index.html meta tags and social previews. Update siteUrl if the domain changes. */
  seo: {
    description:
      "Interactive map of comprehensive motor vehicle crash costs in Maryland. Explore police-reported crashes, injuries, and per-capita costs by county, community, and census tract using NHTSA unit costs and Maryland State Police data.",
    siteUrl: "https://crash-cost-md.fly.dev",
  },

  nav: {
    map: "Map",
    methodology: "Methodology & Sources",
    about: "About",
  },

  hero: {
    title: "What do Maryland's crashes cost?",
    intro: [
      "Marylanders experience around 300 police-reported crashes on their roadways every day. Some of the costs are obvious: deaths, damaged vehicles, emergency response, and traffic congestion. Others are less visible: higher car and health insurance premiums, increased taxes to pay for maitenance, and temporary or permanent disabilities affecting thousands of people each year. These are costs that all of us share.",
      "This map estimates the full cost of police-reported crashes, including the estimated impacts from injuries and loss of life, using [national cost estimates](https://crashstats.nhtsa.dot.gov/Api/Public/ViewPublication/813403) from NHTSA. Explore how the burden varies by county, community, and neighborhood. Filter by date and crash type, compare places in the dashboard below, and zoom in to see individual crashes.",
    ],
    stats: [
      {
        label: "Comprehensive cost (2025)",
        value: "$37.3B",
      },
      {
        label: "Per Maryland resident (2025)",
        value: "$6,017",
      },
      {
        label: "Crashes reported (2025)",
        value: "102,789",
      },
    ] as Array<{ label: string; value: string; note?: string }>,
  },
};
