"""Site-specific legal copy. Deployment assumptions are recorded, not asserted as verified."""

import re
from site_seo import metadata
from site_notices import preferences_notice


BACK_LINK = '<a class="page-back" href="index.html" data-back aria-label="Go back"><span aria-hidden="true">←</span><span class="back-label">Back</span></a>'

BACK_STYLE = '''.page-back{display:inline-flex;align-items:center;justify-content:center;gap:.4rem;min-height:2.5rem;padding:.35rem .7rem;border:1px solid var(--line);border-radius:999px;color:var(--green);font:600 .82rem/1.2 system-ui,sans-serif;text-decoration:none;white-space:nowrap}.page-back:hover{border-color:var(--green);background:#075fce08}.document-header-left,.reader-brand-group{display:flex;align-items:center;gap:1rem;min-width:0}@media(max-width:600px){.page-back{width:2.25rem;min-height:2.25rem;padding:.25rem;font-size:1.1rem}.page-back .back-label{display:none}.document-header-left,.reader-brand-group{gap:.6rem}}'''

BACK_SCRIPT = '''
document.querySelectorAll('[data-back]').forEach(link => link.addEventListener('click', event => {
  if (event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
  try {
    const previous = new URL(document.referrer);
    if (previous.origin === location.origin && previous.href !== location.href && history.length > 1) {
      event.preventDefault(); history.back();
    }
  } catch (_) { /* The normal home link also works without a referrer or JavaScript. */ }
}));
'''


def document_header():
    return ('<header class="document-header"><div class="document-header-left">' + BACK_LINK + '<a class="document-brand" href="index.html">THEOGONY</a></div>'
            '<nav class="document-nav" aria-label="Main navigation"><a href="theogony-reader.html">Read the poem</a>'
            '<a href="translation.html">Translation</a></nav></header>')


def document_footer(current=''):
    pages = [('index.html', 'Home'), ('translation.html', 'Translation'), ('imprint.html', 'Imprint / Impressum'),
             ('privacy.html', 'Privacy'), ('reuse.html', 'Reuse and licence'), ('https://github.com/onur-crg/theogony-reading', 'Source on GitHub'), ('https://www.noto-labs.com/', 'A project by Noto Labs')]
    links = ''.join(f'<a href="{path}"' + (' aria-current="page"' if path == current else '') + f'>{label}</a>' for path, label in pages)
    return '<footer class="document-footer"><nav aria-label="Site information">' + links + '<button type="button" class="preferences-footer-link" data-preferences-open>Privacy settings</button></nav></footer>' + preferences_notice()


DOCUMENT_STYLE = BACK_STYLE + '''
.document-header{display:flex;justify-content:space-between;align-items:center;gap:1.5rem;width:min(calc(100% - 2.5rem),80rem);margin:auto;padding:1.3rem 0;border-bottom:1px solid var(--line)}.document-brand{font:800 1.5rem/1 Optima,'Avenir Next',Arial,sans-serif;text-decoration:none;letter-spacing:.01em}.document-nav{display:flex;gap:1.5rem;font-size:.88rem;font-weight:600}.document-nav a{text-decoration:none;color:var(--ink)}.document-nav a:hover{color:var(--green)}.document-footer{border-top:1px solid var(--line);margin-top:3rem;padding:1.75rem 0;font-size:.85rem}.document-footer nav{display:flex;gap:.75rem 1.4rem;flex-wrap:wrap}.document-footer a{text-decoration:none}.document-footer a[aria-current="page"]{text-decoration:underline}.legal-page>.section{border:0;padding-top:0}.legal-page h1{margin:2.5rem 0 1.75rem}.legal-page h3{margin-top:2rem;font-size:1.15rem;color:var(--green)}.legal-page address{line-height:1.8}.language-version{margin-top:2rem;padding-top:1.2rem;border-top:1px solid var(--line)}.language-version summary{width:max-content;cursor:pointer;color:var(--green);font-weight:600}.legal-page blockquote{margin:1.5rem 0;padding:1rem 1.25rem;border-left:2px solid var(--green);background:#075fce08}.legal-page code{overflow-wrap:anywhere;font-size:.85em}.legal-page p,.legal-page li{overflow-wrap:break-word}
@media(max-width:600px){.document-header{gap:1rem;padding:1rem 0}.document-brand{font-size:1.2rem}.document-nav{flex-direction:column;align-items:flex-end;gap:.25rem;font-size:.78rem}.document-footer nav{gap:.7rem 1rem}}
'''


def render_legal_pages(root, style):
    sections = dict(re.findall(r'<section class="section" id="([^"]+)"[^>]*>(.*?)</section>', LEGAL_SECTIONS, re.S))
    pages = [('imprint', 'imprint.html', 'Legal notice / Impressum', 'en'), ('privacy', 'privacy.html', 'Datenschutz / Privacy', 'de'),
             ('terms', 'reuse.html', 'Reuse and licence', 'en')]
    for key, filename, title, lang in pages:
        content = sections[key].replace('<h2>', '<h1>', 1).replace('</h2>', '</h1>', 1)
        page = (f'<!doctype html><html lang="{lang}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
                '<meta name="theme-color" content="#dedede">' + metadata(filename) + f'<style>{style}</style></head><body>'
                + document_header() + '<main class="wrap legal-page"><section class="section">' + content + '</section>'
                + document_footer(filename) + '</main><script>' + BACK_SCRIPT + LEGAL_SCRIPT + '</script></body></html>')
        (root / filename).write_text(page)
    # Preserve existing bookmarks without keeping a duplicate combined document.
    legacy = '''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex"><title>Page moved · Theogony</title></head><body><p>These pages now have their own addresses.</p><nav><a href="translation.html">Translation</a> · <a href="imprint.html">Imprint</a> · <a href="privacy.html">Privacy</a> · <a href="reuse.html">Reuse and licence</a></nav><script>const destinations={'#imprint':'imprint.html','#privacy':'privacy.html','#terms':'reuse.html','#translation':'translation.html'};location.replace(destinations[location.hash]||('translation.html'+location.hash));</script></body></html>'''
    (root / 'translation-and-legal.html').write_text(legacy)

LEGAL_SECTIONS = '''
<section class="section" id="imprint" lang="en">
<h2>Legal notice / Impressum</h2>
<p>This free reading website is operated by:</p>
<address style="font-style:normal">Onur Cirag<br>Am alten Bahnhof 2b<br>56203 Höhr-Grenzhausen<br>Germany</address>
<p>Email: <a href="mailto:hello@noto-labs.com">hello@noto-labs.com</a></p>
<p>Responsible for the content of this edition: Onur Cirag, at the address above. This website is intended for the public and provides access to a literary work. It does not sell goods, subscriptions or paid services.</p>
<p>This provider identification takes account of <a href="https://www.die-medienanstalten.de/aufgaben/aufsicht/impressumspflicht/">Section 18 of the German Interstate Media Treaty (Medienstaatsvertrag)</a>.</p>
<details class="language-version" lang="de"><summary>Deutsch</summary><h3>Impressum</h3>
<p>Dieses kostenlose Leseangebot wird betrieben von:</p>
<address style="font-style:normal">Onur Cirag<br>Am alten Bahnhof 2b<br>56203 Höhr-Grenzhausen<br>Deutschland</address>
<p>E-Mail: <a href="mailto:hello@noto-labs.com">hello@noto-labs.com</a></p>
<p>Verantwortlich für die Inhalte dieser Ausgabe: Onur Cirag, Anschrift wie oben. Das Angebot richtet sich an die Öffentlichkeit und dient der Vermittlung eines literarischen Werks. Auf dieser Website werden keine Waren, Abonnements oder kostenpflichtigen Leistungen angeboten.</p>
<p>Die Anbieterkennzeichnung berücksichtigt <a href="https://www.die-medienanstalten.de/aufgaben/aufsicht/impressumspflicht/">§ 18 Medienstaatsvertrag</a>.</p>
</details>
</section>

<section class="section" id="privacy" lang="de">
<h2>Datenschutz / Privacy</h2>
<p>Stand: 17. Oktober 2026. Diese Erklärung beschreibt das kostenlose statische Leseangebot und seine optionalen Lesefunktionen.</p>

<h3>1. Verantwortlicher und Kontakt</h3>
<p>Verantwortlich ist Onur Cirag, Am alten Bahnhof 2b, 56203 Höhr-Grenzhausen, Deutschland. Datenschutzanfragen können an <a href="mailto:hello@noto-labs.com">hello@noto-labs.com</a> gerichtet werden.</p>
<h3>2. Aufruf der Website und Hosting bei Vercel</h3>
<p>Beim Abruf einer öffentlich gehosteten Seite müssen die IP-Adresse und technische Verbindungsdaten verarbeitet werden, damit die Inhalte ausgeliefert werden können. Dazu können insbesondere Abrufzeitpunkt, angeforderte Adresse, HTTP-Status, Browser- und Betriebssystemangaben sowie eine gegebenenfalls übermittelte Referrer-Adresse gehören. Zweck ist die Bereitstellung und Absicherung des Leseangebots, einschließlich Fehleranalyse und Abwehr von Missbrauch. Rechtsgrundlage ist Art. 6 Abs. 1 lit. f DSGVO; das berechtigte Interesse besteht in einem zuverlässigen, sicheren und frei zugänglichen Angebot.</p>
<p>Die Website wird als statisches Leseangebot im Hobby-Tarif bei Vercel Inc. gehostet. Anbieteranschrift: 440 N Barranca Ave #4133, Covina, CA 91723, USA. Vercel und seine eingesetzten Infrastruktur-Dienstleister können technische Daten zur Auslieferung und Absicherung verarbeiten. Es werden keine eigenen zusätzlichen Zugriffslogs oder personenbezogenen Besucherprofile angelegt. Die optionale Besuchsstatistik wird in Abschnitt 4 beschrieben. Für die Infrastruktur-Protokolle gelten die tatsächlich vereinbarten Produkt- und Aufbewahrungsbedingungen. Vercel nennt für Daten, die es in eigener Verantwortung verarbeitet, als Aufbewahrungskriterien die Erforderlichkeit für die Dienstbereitstellung, Sicherheitszwecke, rechtliche und vertragliche Pflichten sowie die Durchsetzung von Rechten. Entfällt der Verarbeitungsbedarf, beschreibt Vercel die Löschung oder Anonymisierung; Sicherungskopien können bis zur Löschung geschützt aufbewahrt werden. Diese Anwendung führt keine eigene dauerhafte Besucherprotokollierung und exportiert keine Zugriffslogs.</p>
<p>Vercel betreibt eine globale Infrastruktur; eine ausschließliche Verarbeitung in Deutschland oder der EU wird nicht zugesichert. Informationen zu Empfängern, Aufbewahrung und internationalen Übermittlungen: <a href="https://vercel.com/legal/privacy-notice">Vercel Privacy Notice</a> und <a href="https://vercel.com/legal/dpa">Vercel Data Processing Addendum</a>. Vercel nennt unter anderem das EU-US Data Privacy Framework und Standardvertragsklauseln als Übermittlungsinstrumente. Nach Vercels Datenschutzhinweisen verarbeitet Vercel bestimmte dienstgenerierte Verbindungs- und Nutzungsdaten in eigener datenschutzrechtlicher Verantwortung. Der veröffentlichte Auftragsverarbeitungsvertrag nennt als Geltungsbereich Pro und Enterprise; für den hier verwendeten Hobby-Tarif wird kein abgeschlossener Vertrag nach diesem Dokument behauptet.</p>
<h3>3. Freiwilliges Speichern von Lesefortschritt und Einstellungen</h3>
<p>Die Website lässt sich ohne dauerhafte Lesespeicherung verwenden. Wenn du unter „Manage preferences“ die Lesespeicherung aktivierst oder „Accept all“ wählst, speichert dein Browser den Lesefortschritt, die gewählte Schriftgröße und die Desktop-Einstellung des Inhaltsverzeichnisses lokal. Gespeichert werden nur diese Funktionswerte und deine Entscheidung. Auch eine Ablehnung über „Reject optional“ oder „Save choices“ wird als Auswahl gespeichert, damit der Hinweis nicht bei jedem Aufruf erscheint. Dabei werden keine Leseposition oder Darstellungseinstellungen dauerhaft gespeichert. Sie werden von der Anwendung weder an Onur Cirag noch an einen Analyse- oder KI-Dienst gesendet.</p>
<p>Diese Speicherung stellt die von dir ausdrücklich gewählte Erinnerungsfunktion bereit (§ 25 Abs. 2 Nr. 2 TDDDG). Soweit dabei personenbezogene Daten verarbeitet werden, ist Art. 6 Abs. 1 lit. f DSGVO die Grundlage; das Interesse besteht ausschließlich an der Bereitstellung dieser gewählten Funktion. Über „Reader settings“ im Leser oder „Privacy settings“ im Seitenfuß kannst du deine Wahl jederzeit ändern. Das Ausschalten der Lesespeicherung oder „Reject optional“ löscht gespeicherte Leseposition und Darstellungseinstellungen; die ablehnende Auswahl bleibt gespeichert. Der folgende Button löscht die Lesedaten ebenfalls und speichert die Ablehnung. Die Entscheidung selbst lässt sich über die Website-Daten deines Browsers entfernen. Die Werte bleiben ansonsten im Browser, bis du sie löschst oder der Browser sie entfernt. Ohne Aktivierung wirken Änderungen nur während der aktuellen geöffneten Leseseite.</p>
<p>Verwendete Schlüssel: <code>theogonyRememberPreferencesV1</code>, <code>theogonyReadingPositionV1</code>, <code>theogonyReadingSize</code> und <code>theogonyDesktopContentsV1</code>.</p>
<button type="button" id="clear-reading-data" class="privacy-action">Gespeicherte Lesedaten auf diesem Gerät löschen</button><p id="clear-reading-status" role="status"></p>
<h3 id="visit-statistics">4. Freiwillige Besuchsstatistik mit Vercel Web Analytics</h3>
<p>Nur wenn du „Accept all“ wählst, die Besuchsstatistik unter „Manage preferences“ erlaubst oder die folgende Einstellung aktivierst, wird das Statistikskript von Vercel geladen. Ohne Auswahl und nach „Reject optional“ bleibt es ausgeschaltet. Die Statistik lässt sich unabhängig von der Lesespeicherung erlauben oder ablehnen. Zweck ist, die Nutzung des kostenlosen Leseangebots anhand zusammengefasster Seitenaufrufe und Besucherzahlen zu verstehen. Rechtsgrundlage ist deine Einwilligung nach Art. 6 Abs. 1 lit. a DSGVO; soweit ein Zugriff auf dein Endgerät erfolgt, § 25 Abs. 1 TDDDG.</p>
<p>Verarbeitet werden Seitenadresse, Zeitpunkt, gegebenenfalls verweisende Website, Browser, Betriebssystem, Gerätetyp und ungefähre geografische Angaben aus der Verbindung. Unsere Einbindung entfernt Suchparameter und Sprungmarken aus der erfassten Seitenadresse. Leseposition, Schriftgröße, Suchtexte, Namen-Klicks und Inhalte geöffneter Infokarten werden nicht als Ereignisse erfasst. Vercel erhält technisch die Verbindungsdaten zur Verarbeitung; laut Anbieter werden keine IP-Adressen als Statistikdaten gespeichert. Vercel verwendet einen aus der Anfrage gebildeten Hash zur kurzzeitigen Unterscheidung von Besuchen; diese Zuordnung wird nach höchstens 24 Stunden verworfen. Das bedeutet nicht, dass aggregierte Statistiken nach 24 Stunden gelöscht werden. Im Hobby-Tarif sind Statistiken für ein Ein-Monats-Fenster verfügbar. Die Verarbeitung erfolgt durch Vercel Inc.; zu internationalen Übermittlungen und dem hier verwendeten Hobby-Tarif siehe Abschnitt 2. Weitere Angaben: <a href="https://vercel.com/docs/analytics/privacy-policy">Vercel Web Analytics Datenschutz</a>.</p>
<p>Das Statistikskript setzt keine Analyse-Cookies. Deine Auswahl wird separat als <code>theogonyAnalyticsConsentV1</code> im lokalen Browserspeicher festgehalten, bis du sie änderst oder die Website-Daten löschst. Diese Speicherung dient ausschließlich der Umsetzung deiner Datenschutzentscheidung (§ 25 Abs. 2 Nr. 2 TDDDG, Art. 6 Abs. 1 lit. c DSGVO in Verbindung mit Art. 7 Abs. 3 DSGVO). Bei Do Not Track oder Global Privacy Control wird keine Statistik geladen. Ohne verfügbaren lokalen Speicher bleibt die Statistik ebenfalls aus.</p>
<p><label><input type="checkbox" id="analytics-consent"> Freiwillige Besuchsstatistik auf diesem Gerät erlauben</label></p><p id="analytics-status" role="status"></p>
<p>Du kannst die Einwilligung hier jederzeit mit Wirkung für die Zukunft widerrufen. Die Seite wird beim Ausschalten neu geladen, damit das Statistikskript nicht weiter ausgeführt wird. Die Rechtmäßigkeit der bisherigen Verarbeitung bleibt unberührt. Bereits zusammengefasste Aufrufzahlen lassen sich keiner Person zur nachträglichen Löschung zuordnen. Auch ohne Einwilligung sind sämtliche Lesefunktionen verfügbar.</p>
<h3>Weitere eingebundene Funktionen</h3>
<p>Abgesehen von der oben beschriebenen optionalen Statistik enthält die Website keine Werbeskripte, kein Kontaktformular, keine Benutzerkonten, keine eingebetteten Karten oder Videos und keine von externen Schriftservern geladenen Fonts. Sie setzt selbst keine Cookies ein. Erklärungen und Illustrationen sind bereits erzeugte Dateien. Beim Lesen, Antippen eines Namens oder Öffnen einer Infokarte wird kein KI-Aufruf ausgeführt. Vercel kann zur Absicherung seiner Infrastruktur technische Sicherheitsfunktionen einsetzen. Die serverseitige Verarbeitung technischer Verbindungsdaten beim Hosting ist von den freiwilligen Lesefunktionen im Browser zu unterscheiden.</p>
<h3>5. Kontakt per E-Mail</h3>
<p>Wenn du eine E-Mail sendest, werden Absenderadresse, Nachricht und freiwillig mitgeteilte Angaben zur Bearbeitung der Anfrage verarbeitet. Grundlage ist Art. 6 Abs. 1 lit. f DSGVO, bei vertragsbezogenen Anfragen gegebenenfalls Art. 6 Abs. 1 lit. b DSGVO. Empfänger sind der Betreiber und die für den E-Mail-Verkehr eingesetzten Dienstleister. Nachrichten werden gelöscht, wenn die Bearbeitung abgeschlossen ist und weder weitere Korrespondenz noch gesetzliche Aufbewahrungspflichten oder die Sicherung rechtlicher Ansprüche eine weitere Speicherung erfordern.</p>
<h3>6. Externe Links und GitHub</h3>
<p>Quellen und Lizenzinformationen werden als normale Links angeboten. Ein fremder Dienst wird dadurch erst aufgerufen, wenn du dem Link folgst. Für den anschließenden Besuch gelten dessen Datenschutzinformationen. Das öffentliche GitHub-Repository wird als normaler Link angeboten und nicht als Besucher-Tracking eingebettet; Beiträge, Issues und andere Eingaben auf GitHub unterliegen auch den dortigen Bedingungen.</p>
<h3>7. Deine Rechte</h3>
<p>Bei Vorliegen der gesetzlichen Voraussetzungen hast du Rechte auf Auskunft, Berichtigung, Löschung, Einschränkung der Verarbeitung und Datenübertragbarkeit (Art. 15–20 DSGVO). Du kannst einer Verarbeitung auf Grundlage berechtigter Interessen aus Gründen deiner besonderen Situation widersprechen (Art. 21 DSGVO). Eine Einwilligung ist jederzeit mit Wirkung für die Zukunft widerrufbar, insbesondere über die Statistikeinstellung in Abschnitt 4. Du kannst dich außerdem bei einer Datenschutzaufsichtsbehörde beschweren (Art. 77 DSGVO), insbesondere beim <a href="https://www.datenschutz.rlp.de/service/kontakt">Landesbeauftragten für den Datenschutz und die Informationsfreiheit Rheinland-Pfalz</a>, Postfach 30 40, 55020 Mainz, <a href="mailto:poststelle@datenschutz.rlp.de">poststelle@datenschutz.rlp.de</a>.</p>
<p>Die Angabe zusätzlicher persönlicher Daten ist für das Lesen nicht erforderlich. Ohne technische Verbindungsdaten kann die öffentliche Website nicht ausgeliefert werden. Es findet durch diese Anwendung keine automatisierte Entscheidungsfindung oder Profilbildung im Sinne von Art. 22 DSGVO statt.</p>
</section>

<section class="section" id="terms">
<h2>Reuse and licence</h2>
<p>You may read this edition free of charge. There are no purchases, accounts or paid subscriptions on this website.</p>
<h3>Use it in your own projects</h3>
<p>To the extent Onur Cirag holds copyright or related rights, the English reading text, passage titles, summaries, name notes and original illustrations in this edition are offered under <a rel="license" href="https://creativecommons.org/licenses/by/4.0/">Creative Commons Attribution 4.0 International (CC BY 4.0)</a>. You may copy, share, translate, adapt and use them in websites, books, videos and apps, including commercial projects.</p>
<p>Give appropriate credit to this edition and Onur Cirag, link to the source website and the licence, and indicate whether you changed the material. Credit may be provided in a reasonable place, such as an app’s credits or a book’s source notes. Do not suggest endorsement. The full licence governs; this summary does not add conditions to it.</p>
<p>Suggested credit:</p><blockquote>Hesiod, <em>Theogony</em>, AI-assisted English reading edition by Onur Cirag. Source: <a id="edition-credit-link" href="index.html">this edition’s website</a>. Licensed under CC BY 4.0 (<a href="https://creativecommons.org/licenses/by/4.0/">licence</a>). State any changes you made.</blockquote>
<p>The ancient poem is in the public domain. AI-generated material may not attract copyright protection. This licence does not create rights over unprotected material, remove public-domain freedoms, restrict statutory exceptions or license third-party rights that the publisher does not hold. Attribution is requested as a matter of transparency even where it is not legally required.</p>
<h3>Download the reading edition</h3><p><a href="data/theogony.json" download="theogony.json">Download the complete JSON</a>, including verses, passage titles, summaries, name notes and generation references. See the <a href="https://github.com/onur-crg/theogony-reading/blob/main/data/README.md">data format and examples</a> or the <a href="data/theogony.schema.json">JSON Schema</a> for use in your own projects. This export contains the same selected text as the reader.</p>
<h3>Greek source and separate rights</h3>
<p>The Greek base is the 1914 edition edited by Hugh G. Evelyn-White, digitised by the Perseus Project at Tufts University. Its unchanged XML copy is distributed with the repository’s <a href="https://creativecommons.org/licenses/by-sa/4.0/">CC BY-SA 4.0</a> notice, separately from this edition’s original English content. Keep the Perseus/Tufts attribution and the <a href="sources/perseus-license.md">original licence notice</a> when redistributing that XML. See <a href="https://github.com/PerseusDL/canonical-greekLit">the source repository</a>. This site does not relicense Perseus material under CC BY. Any applicable third-party or database rights remain unaffected.</p>
<p>The website’s original software source code is available under the <a href="LICENSE">MIT licence</a> in the <a href="https://github.com/onur-crg/theogony-reading">public GitHub repository</a>. The content licence does not cover third-party material, names or trademarks. See the <a href="NOTICE.md">rights and attribution notice</a> for the separate licence scopes.</p>
<h3>About accuracy</h3>
<p>This is an AI-assisted reading edition, not a critical scholarly edition. The text and explanations can contain errors, and the illustrations are modern interpretations. Known review items are listed under <a href="translation.html">Translation and sources</a>. Please send corrections to <a href="mailto:hello@noto-labs.com">hello@noto-labs.com</a>. No restriction in these notes overrides mandatory statutory rights.</p>
<p><a href="LICENSE-CONTENT.md">Download the content licensing notice</a>.</p>
</section>
'''

LEGAL_SCRIPT = '''
document.getElementById('clear-reading-data')?.addEventListener('click', () => {
  try {
    window.TheogonyPreferences.disableReading();
    document.getElementById('clear-reading-status').textContent = 'Gespeicherte Lesedaten wurden auf diesem Gerät gelöscht.';
  } catch (_) { document.getElementById('clear-reading-status').textContent = 'Der Browser erlaubt hier keinen Zugriff auf die gespeicherten Daten. Du kannst sie über die Website-Einstellungen deines Browsers löschen.'; }
});
if (document.getElementById('edition-credit-link') && (location.protocol === 'https:' || location.protocol === 'http:')) {
  const link = document.getElementById('edition-credit-link');
  link.href = new URL('index.html', location.href).href;
  link.textContent = link.href;
}
'''
