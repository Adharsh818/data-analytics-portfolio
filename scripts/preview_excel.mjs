// Visual checks use a compact copy of saved values because importing the complete
// 96k-row workbook exceeds the bundled engine's memory limit. Not a deliverable.
import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { FileBlob, SpreadsheetFile, Workbook } from '@oai/artifact-tool';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const out=path.join(root,'outputs/review-2026-11-05');
const stage=process.argv[2] || 'before';
const wb=await SpreadsheetFile.importXlsx(await FileBlob.load(path.join(out,`excel-preview-${stage}.xlsx`)));
console.log((await wb.inspect({kind:'region',sheetId:'Delivery',range:'A4:F8',maxChars:2000})).ndjson);
for(const [sheet,range] of [['Dashboard','A1:Q34'],['Delivery','A1:G29'],['By State','A1:I13'],
    ['Categories','A1:I14'],['About','A1:B10'],['Orders','A1:M6'],['Category Data','A1:D8']]){
  const png=await wb.render({sheetName:sheet,range,scale:1.3});
  await fs.writeFile(path.join(out,`${sheet.replaceAll(' ','-')}-${stage}.png`),new Uint8Array(await png.arrayBuffer()));
}
// Check edited COUNTIFS logic on representative data, including a missing review.
// This exercises the spreadsheet engine without claiming native Excel execution.
if(stage==='after'){
  const fixture=Workbook.create();
  const s=fixture.worksheets.add('Review check');
  s.getRange('A1:B4').values=[['Bucket','Review'],['Late',1],['Late',5],['Late',null]];
  s.getRange('D1').formulas=[['=COUNTIFS(A2:A4,"Late",B2:B4,"<=2",B2:B4,"<>")/COUNTIFS(A2:A4,"Late",B2:B4,"<>")']];
  fixture.recalculate();
  const first=s.getRange('D1').values[0][0];
  if(first!==0.5) throw Error(`Missing review check failed: ${first}`);
  s.getRange('B3').values=[[1]];
  fixture.recalculate();
  if(s.getRange('D1').values[0][0]!==1) throw Error('Input-change check failed');
  console.log('PASS: formula engine excludes blank reviews and responds to input change.');
}
console.log(`Rendered ${stage} verification copy. Full workbook not exported by Artifact Tool.`);
