import { footerContent } from "../content/footer";
import { ProseText } from "./ProseText";

export function SiteFooter() {
  return (
    <footer className="site-footer">
      <div className="site-footer-inner">
        <p className="footer-citation">
          <ProseText text={footerContent.citation} />
        </p>
        <ul className="footer-caveats">
          {footerContent.caveats.map((c, i) => (
            <li key={i}>
              <ProseText text={c} />
            </li>
          ))}
        </ul>
        <p className="footer-attribution">{footerContent.attribution}</p>
      </div>
    </footer>
  );
}
