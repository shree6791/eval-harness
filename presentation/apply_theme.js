// Write a deck's theme colors and theme name into ppt/theme/theme1.xml.
// pptxgenjs sets theme fonts but keeps Office's default palette, so scheme colors
// would otherwise render in stock Office colors.
//
//   const { applyTheme } = require("./apply_theme.js");
//   await applyTheme("deck.pptx", { name, colors: { dk1, lt1, dk2, lt2, accent1..accent6, hlink, folHlink } });

const fs = require("fs");

// jszip ships with pptxgenjs; load it from there so no extra install is needed.
const JSZip = require(require.resolve("jszip", { paths: [require.resolve("pptxgenjs")] }));

const SLOTS = ["dk1", "lt1", "dk2", "lt2", "accent1", "accent2", "accent3", "accent4", "accent5", "accent6", "hlink", "folHlink"];

const escapeXml = (s) => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");

async function applyTheme(file, theme) {
  const colors = theme.colors || theme;
  for (const slot of SLOTS) {
    if (!/^[0-9A-Fa-f]{6}$/.test(colors[slot] || "")) throw new Error(`theme color ${slot} must be six hex digits`);
  }
  const zip = await JSZip.loadAsync(fs.readFileSync(file));
  const path = "ppt/theme/theme1.xml";
  let xml = await zip.file(path).async("string");
  for (const slot of SLOTS) {
    // Each slot holds one color element (srgbClr or sysClr); replace it with the theme's hex.
    const re = new RegExp(`(<a:${slot}>)[\\s\\S]*?(</a:${slot}>)`);
    if (!re.test(xml)) throw new Error(`slot ${slot} not found in ${path}`);
    xml = xml.replace(re, `$1<a:srgbClr val="${colors[slot].toUpperCase()}"/>$2`);
  }
  if (theme.name) {
    xml = xml.replace(/(<a:theme\b[^>]*\bname=")[^"]*(")/, `$1${escapeXml(theme.name)}$2`);
    xml = xml.replace(/(<a:clrScheme\b[^>]*\bname=")[^"]*(")/, `$1${escapeXml(theme.name)}$2`);
  }
  zip.file(path, xml);
  fs.writeFileSync(file, await zip.generateAsync({ type: "nodebuffer", compression: "DEFLATE" }));
}

module.exports = { applyTheme };
