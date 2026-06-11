/**

 * Methodology & Sources tab — edit freely.

 */

export interface ContentSection {

  heading?: string;

  paragraphs: string[];

  bullets?: string[];

  /** Shown after the first paragraph; use with Ko-fi widget on About. */

  supportPrompt?: string;

}



const NHTSA_REPORT =

  "https://crashstats.nhtsa.dot.gov/Api/Public/ViewPublication/813403";

const MDSP_DASHBOARD =

  "https://mdsp.maryland.gov/safety-prevention/interactive-data-dashboards";

const BLS_INFLATION = "https://www.bls.gov/data/inflation_calculator.htm";



export const methodologyContent = {

  pageTitle: "Methodology & Sources",

  intro:

    `Crash data is from the Maryland Department of State Police ([MDSP interactive crash dashboard](${MDSP_DASHBOARD})) and costs are extracted from tables in [NHTSA's The Economic and Societal Impact of Motor Vehicle Crashes, 2019 (Revised)](${NHTSA_REPORT}). Dollar figures are adjusted to June 2025 using a 1.26 cumulative inflation factor (via the [BLS inflation calculator](${BLS_INFLATION})).`,



  sections: [

    {

      heading: "Maryland crash data",

      paragraphs: [

        `Half-year CSV extracts for 2024 and 2025 are downloaded from the [MDSP interactive crash dashboard](${MDSP_DASHBOARD}). Reports, vehicles, occupants, and non-motorists are merged into a single crash-level table keyed by report number.`,

      ],

      bullets: [

        "Reports — one row per crash (severity, date, coordinates, county, etc.)",

        "Vehicles, occupants, and non-motorists — linked by report number; injury status codes drive person-level cost assignment",

      ],

    },

    {

      heading: "Unit costs and injury mapping",

      paragraphs: [

        `Unit costs (Medical, Congestion, Economic, etc.) come from [NHTSA Table 1-10](${NHTSA_REPORT}) (comprehensive police-reported crash costs). Maryland police injury status codes are mapped to MAIS-based cost columns (Fatal, MAIS0–MAIS4). Property-damage-only crashes (severity code 3) use per-vehicle costs only; injury crashes use person-based columns.`,

        `Comprehensive cost includes QALY-valued losses as defined in the [NHTSA report](${NHTSA_REPORT}) — not purely out-of-pocket economic costs.`,

      ],

    },

    {

      heading: "Geography",

      paragraphs: [

        "Each crash point is spatially joined to 2024 TIGER/Line boundaries for Maryland counties, census tracts, and places (CDPs and incorporated places). Population and vehicle-ownership context come from NHGIS / ACS summaries merged at prepare time.",

      ],

    },

    {

      heading: "Sources",

      paragraphs: [],

      bullets: [

        `MDSP — [Maryland Department of State Police interactive crash dashboard](${MDSP_DASHBOARD})`,

        `NHTSA — [The Economic and Societal Impact of Motor Vehicle Crashes, 2019 (Revised)](${NHTSA_REPORT})`,

        "U.S. Census Bureau — TIGER/Line shapefiles; ACS via NHGIS",

        `Bureau of Labor Statistics — [CPI inflation adjustment](${BLS_INFLATION}) (June 2019 → June 2025)`,

      ],

    },

  ] satisfies ContentSection[],

};

