import type { ContentSection } from "../content/methodology";
import { ProseText } from "./ProseText";

interface Props {
  title: string;
  intro: string;
  sections: ContentSection[];
}

export function ProsePage({ title, intro, sections }: Props) {
  return (
    <article className="prose-page">
      <h1>{title}</h1>
      <p className="prose-lead">
        <ProseText text={intro} />
      </p>
      {sections.map((section, i) => (
        <section key={i} className="prose-section">
          {section.heading && <h2>{section.heading}</h2>}
          {section.paragraphs.map((p, j) => (
            <div key={j}>
              <p>
                <ProseText text={p} />
              </p>
              {j === 0 && section.supportPrompt && (
                <div className="prose-support">
                  <p>
                    <ProseText text={section.supportPrompt} />
                  </p>
                </div>
              )}
            </div>
          ))}
          {section.bullets && section.bullets.length > 0 && (
            <ul>
              {section.bullets.map((b, k) => (
                <li key={k}>
                  <ProseText text={b} />
                </li>
              ))}
            </ul>
          )}
        </section>
      ))}
    </article>
  );
}
