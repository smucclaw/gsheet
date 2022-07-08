
var port       = "8080";
const url_host = "http://18.139.62.80";
function url_hp() { return `${url_host}:${port}`; }
function url_wd() { return `${url_hp()}/workdir/`; }

function devMode() {
  let spreadsheet = SpreadsheetApp.getActiveSpreadsheet();
  let sheet = SpreadsheetApp.getActiveSheet();
  let range = sheet.getRange("A1:Z10").getDisplayValues();
  for (let i = 0; i < range.length; i++) {
    for (let j = 0; j < range[i].length; j++) {
      if (range[i][j].search(/devMode on/i)) {
	      return "8080";
      }
      else if (devport = range[i][j].search(/devMode port (\d+)/i)) {
	      return devport[1];
      }
    }
  }
  return "8080";
}

function onOpen() {
  //  saveUuid();
  //  saveCommands();
  port = devMode();
  showSidebar();
}

function saveUuid() {
  let userCache = CacheService.getUserCache();
  let cached = "";
  if (userCache.get("uuid") == null) {
    cached = Utilities.getUuid();
    userCache.put("uuid", cached, 21600);
    return cached;
  }
  return userCache.get("uuid")
}
function showSidebar() {
  let cachedUuid = saveUuid();
  let [spreadsheetId, sheetId] = getSsid();
  let workDirUrl = (url_wd() + cachedUuid + "/" + spreadsheetId + "/" + sheetId + "/");
  
  let sidebar = HtmlService.createTemplateFromFile('main');
  Logger.log("calling exportCSV()");
  sidebar.fromFlask = exportCSV(cachedUuid, spreadsheetId, sheetId);
  sidebar.corel4url           = workDirUrl + "corel4/LATEST.l4";
  sidebar.petri_url           = workDirUrl + "petri/LATEST.png"
  sidebar.json_url            = workDirUrl + "json/LATEST.json"
  sidebar.petri_thumbnail_img = workDirUrl + "petri/LATEST-small.png"
  Logger.log("returned from exportCSV()");

  Logger.log("looking for v8k_url in fromFlask")
  var v8k_url = sidebar.fromFlask.match(/^v8k_url=(.*)$/m);
  if (v8k_url) {
    Logger.log(`matched a v8k_url: ${v8k_url[1]}`);
    sidebar.v8k_url = url_host + v8k_url[1];
  } else {
    Logger.log("unable to return valid v8k link");
    sidebar.v8k_url = "#";
  }
  Logger.log("drawing sidebar");
  let sidebarOutput = sidebar.evaluate().setTitle('Output from L4');
  SpreadsheetApp.getUi().showSidebar(sidebarOutput);
  Logger.log("drawn sidebar");
}

function aasvgLink() {
  saveUuid();
  let userCache = CacheService.getUserCache();
  let cachedUuid = userCache.get("uuid");
  let spreadsheetId = "";
  let sheetId = 0;
  [spreadsheurl_hostetId, sheetId] = getSsid();
  let url = url_hp() + "/aasvg/" + cachedUuid + "/" + spreadsheetId + "/" + sheetId;
  let urlString = HtmlService.createHtmlOutput("<a href='" + url + "' target='_blank'>Index of SVG Images</a>").getContent();
  return urlString;
}

function getSsid() {
  let spreadsheet = SpreadsheetApp.getActiveSpreadsheet();
  let sheet = SpreadsheetApp.getActiveSheet();
  let spreadsheetId = spreadsheet.getId()
  let sheetId = sheet.getSheetId();
  if (sheetId == sheetId.toFixed()) {
    sheetId = sheetId.toFixed();
  }
  console.log("getSsid: " + spreadsheetId + " / "+ sheetId)
  return [spreadsheetId, sheetId];
}
function exportCSV(uuid, spreadsheetId, sheetId) {
    let sheet = SpreadsheetApp.getActiveSheet();
  Logger.log("exportCSV: initialized. constructing CSV.");
  let cellArraysOfText = sheet.getDataRange().getDisplayValues();
  let csvStr = cellArraysToCsv(cellArraysOfText);
  // ui.prompt(csvStr);
  
  let formData = {
    'name': 'Max Loo',
    'email': 'maxloo@smu.edu.sg',
    'uuid': uuid,
    'spreadsheetId': spreadsheetId,
    'sheetId': sheetId,
    'csvString': csvStr
  };
  let options = {
    'method' : 'post',
    'payload' : formData
  };
  Logger.log("exportCSV: calling UrlFetchApp");

  let response = UrlFetchApp.fetch(url_hp() + '/post', options);
  return response.getContentText();
}
function cellArraysToCsv(rows) {
  const ui = SpreadsheetApp.getUi();
  const regex = /"/g;
  let csvStr = "";
  for (let i = 0; i < rows.length; i++) {
    let row = "";
    for (let j = 0; j < rows[i].length; j++) {
      var needToEnclose = false;
      if (rows[i][j]) {
        let comma = (rows[i][j].indexOf(",") > -1);
        let change = rows[i][j].replace(regex, '\"\"');
        needToEnclose   = comma || change;
        if (needToEnclose) {
          row = row + '"' + change + '"';
        }
        else {
          row = row + change;
        }
      }
      row = row + ",";
    }
    row = row.substring(0, (row.length-1));
    csvStr += row + '\n';
  }
  return csvStr;
}


function onChange(e) {
  const sheet = SpreadsheetApp.getActiveSheet();
  if (e.changeType=="INSERT_ROW") {
    testWait();
    // sheet.getRange(1, 4).setValue("row inserted");
    scanDocIF(sheet);
    // sheet.getRange(1, 5).setValue("insert complete");
  }
  else if (e.changeType=="REMOVE_ROW") {
    testWait();
    // sheet.getRange(1, 4).setValue("row deleted");
    scanDocIF(sheet);
    // sheet.getRange(1, 5).setValue("delete complete");
  }
  else if (e.changeType=="EDIT") {
    // sheet.getRange(1, 4).setValue("cell edited");
    sheet.getRange(1, 5).setValue("");
  }
}
function testWait(){
  const lock = LockService.getScriptLock();
  lock.waitLock(3000);
  SpreadsheetApp.flush();
  lock.releaseLock();
}
function scanDocIF(sheet) {
  // If IF detected in a row,
  // check next row for IF and act accordingly
  let c;
  const h = new ElementHistory();
  const totalRows = 100;
  const totalCols = 3;
  for(let i=3; i<=totalRows; i++) {
    for(let j=2; j<=totalCols; j++) {
      let startWord = getNext1 = getNext2 = "";
      c = sheet.getRange(i, j);
      startWord = c.getValue();
      if (startWord=="IF") {
        getNext1 = sheet.getRange(i+1, j).getValue();
        getNext2 = sheet.getRange(i+1, j+1).getValue();
        if (getNext1==="" && getNext2!=="IF") {
          sheet.getRange(i, j+1).setValue("");
        }
        else if (getNext1==="" && getNext2==="IF") {
          c = startProcessing(c, h, sheet);
        }
      }
    }
  }
}
function onEdit(e) {
  // Respond to Edit events on spreadsheet.
  let c = e.range;
  const sheet = SpreadsheetApp.getActiveSheet();
  const h = new ElementHistory();
  if (goodLayout(c) && !c.isBlank()) {
    drawWords(c);
    c = startProcessing(c, h, sheet);
  }
  else if (c.isBlank()) {
    if (e.oldValue=="IF" || e.oldValue=="WHEN"
	|| e.oldValue=="IS" || e.oldValue=="MEANS") {
      c.offset(-1,0).clear();
    }
  }
  showSidebar();
}
function startProcessing(c, h, sheet) {
  const startCell = findStart(c);
  // sheet.getRange(1, 1).setValue(startCell.getValue());
  [c, h] = scanDownwards(startCell, h);
  // sheet.getRange(1, 2).setValue(c.getA1Notation());
  // Draw bridge only after scanDownwards
  // because h.history required for drawing
  drawBridgeIfAndOr(h, sheet);
  processHistory(h, sheet);
  // sheet.getRange(1, 3).setValue(h.history.toString());
  return c;
}
class ElementHistory {
  constructor(history = []) {
    this.history = history;
  }
}
function findStart(c) {
  // Find the topLeft start of a block of keywords.
  let nextCol = 0;
  const maxCount = 5;
  while (nextCol < maxCount) {
    const getTopRight = c.offset(-1, nextCol);
    const gtr = getTopRight.getValue();
    if (isKeyword(gtr)) {
      c = getTopRight;
      return findStart(c);
    }
    nextCol++;
  }
  if (nextCol == maxCount) {
    const getTopLeft = c.offset(-1, -1);
    const gtl = getTopLeft.getValue();
    if (isKeyword(gtl)) {
      c = getTopLeft;
      return findStart(c);
    }
  }
  return c;
}
function scanDownwards(c, h) {
  // Scan downwards for keywords and
  // put keywords into h.history Array.
  const predValue = c.offset(0,1).getValue();
  if (isKeyword(c.getValue())) {
    h.history[c.getRowIndex()] =
      [c.getColumnIndex(), c.getValue(), predValue];
  }
  let cellCol = 1;
  const columnLimit = cellCol - c.getColumnIndex();
  do {
    const nextCellBelow = c.offset(1,cellCol);
    const ncb = nextCellBelow.getValue();
    if (isKeyword(ncb)) {
      c = nextCellBelow;
      return scanDownwards(c, h);
    }
    cellCol -= 1;
  } while (cellCol >= columnLimit)
  return [c, h];
}
function drawBridgeIfAndOr(h, sheet) {
  // SpreadsheetApp.getUi().alert("drawBridgeIfAndOr");
  // sheet.getRange(1, 6).setValue("drawBridgeIfAndOr");
  let restart = true;
  let rowBegin = rowStop = numOfRows = 0;
  let rangeString = "";
  let columnNow = farCol = 1;
  // Get furthest column.
  for (const element of h.history) {
    if (element != null) {
      farCol = getFurthest(farCol, element[0]);
    }
  }
  columnNow = farCol;
  while (columnNow > 1) {
    // SpreadsheetApp.getUi().alert(columnNow);
    for (const element of h.history) {
      if (element != null) {
        const row = h.history.indexOf(element);
        // SpreadsheetApp.getUi().alert("row = " + row);
        const [col, keyword, predicate] = element;
        // Determine start of code block.
        if (columnNow==col && restart &&
            (keyword=="IF" || keyword=="WHEN")
            // || keyword=="MEANS" || keyword=="IS")
            && rowBegin<row) {
          restart = false;
          rowBegin = row;
        }
        // Parse code block in BabyLegalSS and
        // draw bridge.
        // This code section here also redraws AND
        // and adjusts formatting around buildRange
        // which includes IF, WHEN, MEANS and IS.
        if (columnNow==col && !restart) {
          rowStop = getFurthest(rowStop, row);
          numOfRows = rowStop - rowBegin + 1;
          const buildRange = sheet.getRange(rowBegin,
					    columnNow, numOfRows, 1);
          const getITIS = sheet.getRange(rowBegin-1, columnNow-1).getValue();
          const checkITIS = (getITIS=="IT IS");
          // rangeString = buildRange.getA1Notation();
          // SpreadsheetApp.getUi().alert(
          //   rangeString + ", " + keyword);
          if (keyword=="OR" && !checkITIS) {
            // SpreadsheetApp.getUi().alert(keyword);
            buildRange.setBorder(null,false,false,true,false,false,
				 "grey",SpreadsheetApp.BorderStyle.SOLID_THICK);
          }
          else if (keyword=="AND" && !checkITIS) {
            // SpreadsheetApp.getUi().alert(
            //   keyword + ", " + row + ", " + col);
            sheet.getRange(row, col).offset(0,1,1,2)
              .setBorder(true,true,false,false,false,false,
			 "grey",SpreadsheetApp.BorderStyle.SOLID_THICK);
            buildRange.setBorder(null,false,false,true,false,false,
				 "grey",SpreadsheetApp.BorderStyle.SOLID_THICK);
          }
          const getNextIF = sheet.getRange(rowBegin+1, columnNow+1).getValue();
          const checkNextIF = (getNextIF=="IF");
          const buildIFHorizontal = sheet.getRange(rowBegin,
						   columnNow+1, 1, 2);
          if (checkNextIF) {
            buildIFHorizontal.setBorder(true,true,null,null,null,null,
					"grey",SpreadsheetApp.BorderStyle.SOLID_THICK);
          }
        }
      }
    }
    columnNow--;
    // SpreadsheetApp.getUi().alert(columnNow);
    restart = true;
    rowStop = rowBegin = 0;
  }
}
function processHistory(h, sheet) {
  // Process the h.history Array.
  let restart = true;
  let rowBegin = rowStop = numOfRows = 0;
  let rangeString = "";
  let columnNow = farCol = 1;
  // Get furthest column.
  for (const element of h.history) {
    if (element != null) {
      farCol = getFurthest(farCol, element[0]);
    }
  }
  // Convert the keyword
  // "UNLESS" to "AND", and its predicate to
  // NOT predicate.
  for (const element of h.history) {
    if (element != null) {
      if (element[1]=="UNLESS") {
        element[1] = "AND";
        element[2] = !element[2];
      }
    }
  }
  while (columnNow <= farCol) {
    for (const element of h.history) {
      if (element != null) {
        const row = h.history.indexOf(element);
        const [col, keyword, predicate] = element;
        // Determine start of code block.
        if (columnNow==col && restart &&
            (keyword=="IF" || keyword=="WHEN"
             || keyword=="MEANS" || keyword=="IS")
            && rowBegin<row) {
          restart = false;
          rowBegin = row;
        }
        // Parse code block and update topLeft equation.
        // Must use setValue("") instead of clear()
        // because cannot clear borders formatting.
        if (columnNow==col && !restart) {
          rowStop = getFurthest(rowStop, row);
          numOfRows = rowStop - rowBegin + 1;
          const buildRange = sheet.getRange(rowBegin,
					    columnNow+1, numOfRows, 1);
          rangeString = buildRange.getA1Notation();
          if (keyword=="OR" || keyword=="AND") {
            sheet.getRange(rowBegin-1, columnNow)
              .setValue("=" + keyword.toLowerCase()
			+ "(" + rangeString + ")");
          }
          else {
            sheet.getRange(rowBegin-1, columnNow).setValue("");
          }
        }
      }
    }
    columnNow++;
    restart = true;
    rowStop = 0;
  }
}
function getFurthest(prevIndex, index) {
  if (prevIndex < index) return index;
  else return prevIndex;
}
function isKeyword(cValue){
  return (cValue=="IF" || cValue=="OR"
	  || cValue=="AND" || cValue=="WHEN"
	  || cValue=="MEANS" || cValue=="IS"
	  || cValue=="IT IS"
	  || cValue=="EVERY" || cValue=="PARTY"
	  || cValue=="HENCE" || cValue=="LEST"
	  || cValue=="UNLESS"
	 );
}
function goodLayout(c) {
  if (c.getBackground() != "#ffffff") {
    // SpreadsheetApp.getUi().alert(
    //   "ERROR: Background must be white colour");
    return false;
  }
  if (isKeyword(c.getValue())) {
    if (c.getColumnIndex() < 2) {
      SpreadsheetApp.getUi().alert(
        "ERROR: Keywords must be entered from column B onwards");
      return false;
    }
    if (c.getRowIndex() < 3) {
      SpreadsheetApp.getUi().alert(
        "ERROR: Keywords must be entered from row 3 onwards");
      return false;
    }
  }
  return true;
}
function drawWords(c) {
  // Identify keywords for formatting and drawing.
  const cValue = c.getValue();
  if (cValue=="IF" || cValue=="WHEN") {
    c = drawIfWhenTop(c);
    if (c != null) {
      drawIfWhenOr(c);
    }
  }
  else if (cValue=="OR") {
    drawIfWhenOr(c);
  }
  else if (cValue=="AND") {
    drawAnd(c);
  }
  else if (cValue=="IS" || cValue=="MEANS") {
    c = drawIfWhenTop(c);
    if (c != null) {
      drawTeeOverIsMeans(c);
    }
  }
  else if (cValue=="IT IS") {
    drawTeeForITIS(c);
  }
  else if (cValue=="EVERY" || cValue=="PARTY") {
    drawPlusUnderEvery(c);
  }
  else if (cValue=="HENCE" || cValue=="LEST") {
    drawHenceLest(c);
  }
  else if (cValue=="UNLESS") {
    drawUnless(c);
  }
}
function drawIfWhenTop(c) {
  // Check cell above for checkbox.
  // If no checkbox, move cValue down
  // and insert checkbox in original cell.
  const topCell = c.offset(-1,0);
  if (topCell.getDataValidation()!=null) {
    if (topCell.getDataValidation().getCriteriaType()
	=="CHECKBOX") {
      return c;
    }
    else return null;
  }
  else if (topCell.isBlank()) {
    const cValue = c.getValue();
    c.setValue("");
    c.insertCheckboxes();
    c.offset(1,0).setValue(cValue);
    return c.offset(1,0);
  }
}
function drawIfWhenOr(c) {
  if (c.getValue()=="OR") {
    c.offset(0,-1,1,9).clearFormat();
  }
  c.setHorizontalAlignment("right");
  if (c.offset(0,1).isBlank()) {
    c.offset(0,1).insertCheckboxes()
      .setBorder(null,true,false,false,false,false,
		 "grey",SpreadsheetApp.BorderStyle.SOLID_THICK);
  }
  c.setBorder(null,null,null,true,false,false,
	      "grey",SpreadsheetApp.BorderStyle.SOLID_THICK);
  if (c.offset(0,2).isBlank()) {
    c.offset(0,2).setValue("some condition");
  }
}
function drawAnd(c) {
  c.offset(0,-1,1,9).clearFormat();
  c.setHorizontalAlignment("right");
  if (c.offset(0,1).isBlank()) {
    c.offset(0,1).insertCheckboxes()
      .setBorder(null,true,false, false, false,false,
                 "grey",SpreadsheetApp.BorderStyle.SOLID_THICK);
  }
  c.offset(0,1,1,2)
    .setBorder(true,true,false,false,false,false,
	       "grey",SpreadsheetApp.BorderStyle.SOLID_THICK);
  c.setBorder(null,null,null,true,false,false,
	      "grey",SpreadsheetApp.BorderStyle.SOLID_THICK);
  if (c.offset(0,2).isBlank()) {
    c.offset(0,2).setValue("some condition");
  }
}
function drawTeeOverIsMeans(c) {
  c.offset(0,-1,1,9).clearFormat();
  c.offset(-1,1).setValue("a Defined Term");
  c.offset(0,0,1,3)
    .setBorder(true,false,false,false,false,false,
               "grey",SpreadsheetApp.BorderStyle.SOLID_THICK);
  c.offset(0,0,2,1)
    .setBorder(true,false,false,true,false,false,
               "grey",SpreadsheetApp.BorderStyle.SOLID_THICK);
  c.offset(0,0).setValue(cValue).setHorizontalAlignment("right");
  if (c.offset(0,1).isBlank()) {
    c.offset(0,1).insertCheckboxes();
  }
  c.offset(0,2).setValue("a thing");
  c.offset(1,0).setValue("OR").setHorizontalAlignment("right");
  c.offset(1,1).insertCheckboxes();
  c.offset(1,2).setValue("another thing");
}
function drawTeeForITIS(c) {
  const cValue = c.getValue();
  c.offset(0,-1,3,9).clear();
  c.setValue(cValue).setHorizontalAlignment("right");
  c.offset(0,1).insertCheckboxes();
  c.offset(0,2).setValue("a Defined Situation");
  c.offset(1,0,1,5)
    .setBorder(true,false,false,false,false,false,
               "grey",SpreadsheetApp.BorderStyle.SOLID_THICK);
  c.offset(1,1,2,1)
    .setBorder(true,false,false,true,false,false,
               "grey",SpreadsheetApp.BorderStyle.SOLID_THICK);
  c.offset(1,1).setValue("WHEN").setHorizontalAlignment("right");
  c.offset(1,2).insertCheckboxes();
  c.offset(1,3).setValue("something holds");
  c.offset(2,1).setValue("AND").setHorizontalAlignment("right");
  c.offset(2,2).insertCheckboxes();
  c.offset(2,3).setValue("something else holds");
}
function drawPlusUnderEvery(c) {
  const cValue = c.getValue();
  c.offset(0,-1,3,9).clear();
  c.setValue(cValue).setHorizontalAlignment("right");
  if (cValue == "EVERY") { c.offset(0,1).setValue("Entity"); }
  if (cValue == "PARTY") { c.offset(0,1).setValue("P"); }
  c.offset(1,0).setValue("MUST").setHorizontalAlignment("right");
  c.offset(1,1).setValue("BY").setHorizontalAlignment("right");
  c.offset(1,2).setValue("some deadline");
  c.offset(2,0).setValue("➔").setHorizontalAlignment("right");
  c.offset(2,1).setValue("take").setHorizontalAlignment("right");
  c.offset(2,2).setValue("some Action");
  c.offset(0,0,3).setBorder(false,false,false,true,false,false,
			    "grey", SpreadsheetApp.BorderStyle.SOLID_THICK);
  c.offset(1,0,1,4).setBorder(false,false,true,false,false,false,
			      "grey", SpreadsheetApp.BorderStyle.SOLID_THICK);
  c.offset(1,0).setBorder( false,false,true,true,false,false,
			   "grey", SpreadsheetApp.BorderStyle.SOLID_THICK);
}
function drawHenceLest(c) {
  const cValue = c.getValue();
  c.offset(0,-1,1,9).clearFormat();
  c.setValue(cValue).setHorizontalAlignment("right");
  c.offset(0,1,1,2).setBorder(false,true,true,false,false,false,
                              "grey",SpreadsheetApp.BorderStyle.SOLID_THICK);
}
function drawUnless(c) {
  const cValue = c.getValue();
  c.offset(0,-1,1,9).clearFormat();
  c.setValue(cValue).setHorizontalAlignment("right");
  c.offset(0,1).insertCheckboxes()
    .setBorder(true,false,true,true,false,false,
               "grey",SpreadsheetApp.BorderStyle.SOLID_THICK);
  if (c.offset(0,2).isBlank()) {
    c.offset(0,2).setValue("some exception");
  }
}

function saveCommands() {
  let response = UrlFetchApp.fetch(url_hp() + '/get')
  let commandArray = response.getContentText().split("\n");
  let scriptCache = CacheService.getScriptCache();
  scriptCache.put('commands', JSON.stringify(commandArray), 21600);
}
function getAllCommands() {
  saveCommands();
  let scriptCache = CacheService.getScriptCache();
  const commandArray = JSON.parse(scriptCache.get('commands'));
  return commandArray;
}
function getFirstCommand() {
  let scriptCache = CacheService.getScriptCache();
  const commandArray = JSON.parse(scriptCache.get('commands'));
  // Logger.log(commandArray);
  return commandArray[0];
}
function putChangedCommand(command) {
  let userCache = CacheService.getUserCache();
  userCache.put("command", command, 21600);
}

