function myCommonFunction() {
  return ("this is a library, 1.0.0")
}

function cellArraysToCsv(rows) {
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

function exportCSV(postUrl, uuid, spreadsheetId, sheetId) {
  let sheet = SpreadsheetApp.getActiveSheet();
  Logger.log("exportCSV: initialized. constructing CSV.");
  let cellArraysOfText = sheet.getDataRange().getDisplayValues();
  let csvStr = cellArraysToCsv(cellArraysOfText);
  
  let formData = {
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

  let response = UrlFetchApp.fetch(postUrl, options);
  Logger.log("exportCSV: after UrlFetchApp");
  return response.getContentText();
}