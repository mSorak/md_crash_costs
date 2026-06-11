/**
 * About tab — edit freely.
 */
import type { ContentSection } from "./methodology";

export const aboutContent = {
  pageTitle: "About",
  intro:
    "Maryland Crash Costs is a personal research project, exploring the geographic distribution of motor vehicle crash costs in Maryland. It is not affiliated with any state agency or organization.",

  sections: [
    {
      heading: "Code",
      paragraphs: [
        "Source code and data for this project can be found in the [md_crash_costs GitHub repository](https://github.com/mSorak/md_crash_costs).",
      ],
    },
    {
      heading: "About Me",
      supportPrompt:
        "If you find this work useful, consider [supporting me](https://ko-fi.com/mattperfectnumbers) — it helps me keep building public-interest data tools like this.",
      paragraphs: [
        "Hello! I'm Matt Sorak, a data professional and advocate for better built environments. Most of my work can be found on my blog, [Perfect Numbers](https://perfectnumbers.substack.com/), including [a piece with some of my takeaways from this project](https://perfectnumbers.substack.com/p/crashes-on-maryland-roadways-cost).",
        "Contact me at md.crash.costs@gmail.com",
      ],
    },
  ] satisfies ContentSection[],
};
