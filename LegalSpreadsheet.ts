import URLFetchRequestOptions = GoogleAppsScript.URL_Fetch.URLFetchRequestOptions
import SheetsOnChange = GoogleAppsScript.Events.SheetsOnChange
import Sheet = GoogleAppsScript.Spreadsheet.Sheet
import SheetsOnEdit = GoogleAppsScript.Events.SheetsOnEdit
import Range = GoogleAppsScript.Spreadsheet.Range

function onOpen () {
  const ui = SpreadsheetApp.getUi()
  ui.createMenu('Export CSV')
    .addItem('Export CSV', 'exportCSV')
    .addToUi()
}

function exportCSV () {
  const ui = SpreadsheetApp.getUi()
  const ss = SpreadsheetApp.getActiveSpreadsheet()
  const sheet = ss.getSheets()[0]

  // This represents ALL the data
  const range = sheet.getDataRange()
  const values = range.getValues()
  let csvStr = ''

  // This creates a string of the spreadsheet in CSV format with a trailing comma
  for (let i = 0; i < values.length; i++) {
    let row = ''
    for (let j = 0; j < values[i].length; j++) {
      if (values[i][j]) {
        row = row + values[i][j]
      }
      row = row + ','
    }
    row = row.substring(0, (row.length - 1))
    csvStr += row + '\n'
  }

  // creates de Blob of the csv file
  const csvBlob = Utilities.newBlob(csvStr, 'text/csv', 'test.csv')
  ui.prompt(csvBlob.getDataAsString())

  const formData = {
    name: 'Bob Smith',
    email: 'bob@example.com',
    csvBlob
  }

  const options : URLFetchRequestOptions = {
    method: 'post',
    payload: formData
  }
  const response = UrlFetchApp.fetch('https://httpbin.org/post', options)
  ui.prompt(response.getContentText())
}

function onChange (e: SheetsOnChange) {
  const sheet = SpreadsheetApp.getActiveSheet()
  if (e.changeType === 'INSERT_ROW') {
    testWait()
    sheet.getRange(1, 4).setValue("row inserted");
    scanDocIF(sheet)
    sheet.getRange(1, 5).setValue("insert complete");
  } else if (e.changeType === 'REMOVE_ROW') {
    testWait()
    sheet.getRange(1, 4).setValue("row deleted");
    scanDocIF(sheet)
    sheet.getRange(1, 5).setValue("delete complete");
  } else if (e.changeType === 'EDIT') {
    sheet.getRange(1, 4).setValue("cell edited");
    sheet.getRange(1, 5).setValue('')
  }
}

function testWait () {
  const lock = LockService.getScriptLock()
  lock.waitLock(3000)
  SpreadsheetApp.flush()
  lock.releaseLock()
}

function scanDocIF (sheet : Sheet) {
  // If IF detected in a row,
  // check next row for IF and act accordingly
  let c
  const h = new ElementHistory()
  const totalRows = 100
  const totalCols = 3
  for (let i = 3; i <= totalRows; i++) {
    for (let j = 2; j <= totalCols; j++) {
      let startWord = ''
      let getNext1 = ''
      let getNext2 = ''
      c = sheet.getRange(i, j)
      startWord = c.getValue()
      if (startWord === 'IF') {
        getNext1 = sheet.getRange(i + 1, j).getValue()
        getNext2 = sheet.getRange(i + 1, j + 1).getValue()
        if (getNext1 === '' && getNext2 !== 'IF') {
          sheet.getRange(i, j + 1).setValue('')
        } else if (getNext1 === '' && getNext2 === 'IF') {
          c = startProcessing(c, h, sheet)
        }
      }
    }
  }
}

function onEdit(e: SheetsOnEdit) {
  // Respond to Edit events on spreadsheet.
  let cell = e.range
  const enteredValue = e.value
  const sheet = SpreadsheetApp.getActiveSheet()
  const history = new ElementHistory()
  if (goodLayout(cell, enteredValue) && !cell.isBlank()) {
    drawWords(cell, enteredValue)
    startProcessing(cell, history, sheet)
  } else if (cell.isBlank()) {
    if (e.oldValue === 'IF' || e.oldValue === 'WHEN' ||
        e.oldValue === 'IS' || e.oldValue === 'MEANS') {
      cell.offset(-1, 0).clear()
    }
  }
  sheet.getRange(1, 5).setValue("Edit Completed")
  console.log("Function onEdit completed!")
}

function startProcessing (c: Range, h: ElementHistory, sheet: Sheet): Range {
  const startCell = findStart(c)
  sheet.getRange(1, 1).setValue(startCell.getValue());
  [c, h] = scanDownwards(startCell, h)
  sheet.getRange(1, 2).setValue(c.getA1Notation())
  // Draw bridge only after scanDownwards
  // because h.history required for drawing
  drawBridgeIfAndOr(h, sheet)
  processHistory(h, sheet)
  sheet.getRange(1, 3).setValue(h.history.toString())
  return c
}

class ElementHistory {
  public history: any[];
  constructor (history = []) {
    this.history = history
  }
}

function findStart (c: Range): Range {
  // Find the topLeft start of a block of keywords.
  let nextCol = 0
  const maxCount = 5
  while (nextCol < maxCount) {
    const getTopRight = c.offset(-1, nextCol)
    const gtr = getTopRight.getValue()
    if (isKeyword(gtr)) {
      c = getTopRight
      return findStart(c)
    }
    nextCol++
  }
  if (nextCol === maxCount) {
    const getTopLeft = c.offset(-1, -1)
    const gtl = getTopLeft.getValue()
    if (isKeyword(gtl)) {
      c = getTopLeft
      return findStart(c)
    }
  }
  return c
}

function scanDownwards (c: Range, h: ElementHistory) {
  // Scan downwards for keywords and
  // put keywords into h.history Array.
  const predValue = c.offset(0, 1).getValue()
  if (isKeyword(c.getValue())) {
    h.history[c.getRowIndex()] =
      [c.getColumn(), c.getValue(), predValue]
  }
  let cellCol = 1
  const columnLimit = cellCol - c.getColumn()
  do {
    const nextCellBelow = c.offset(1, cellCol)
    const ncb = nextCellBelow.getValue()
    if (isKeyword(ncb)) {
      c = nextCellBelow
      return scanDownwards(c, h)
    }
    cellCol -= 1
  } while (cellCol >= columnLimit)
  return [c, h]
}

function drawBridgeIfAndOr (h: ElementHistory, sheet: Sheet) {
  // SpreadsheetApp.getUi().alert("drawBridgeIfAndOr");
  // sheet.getRange(1, 6).setValue("drawBridgeIfAndOr");
  let restart = true
  let rowBegin = 0
  let rowStop = 0
  let numOfRows = 0
  const rangeString = ''
  let columnNow = 1
  let farCol = 1
  // Get furthest column.
  for (const element of h.history) {
    if (element != null) {
      farCol = getFurthest(farCol, element[0])
    }
  }
  columnNow = farCol
  while (columnNow > 1) {
    // SpreadsheetApp.getUi().alert(columnNow);
    for (const element of h.history) {
      if (element != null) {
        const row = h.history.indexOf(element)
        // SpreadsheetApp.getUi().alert("row = " + row);
        const [col, keyword, predicate] = element
        // Determine start of code block.
        if (columnNow === col && restart &&
          (keyword === 'IF' || keyword === 'WHEN') &&
          // || keyword=="MEANS" || keyword=="IS")
          rowBegin < row) {
          restart = false
          rowBegin = row
        }
        // Parse code block in BabyLegalSS and
        // draw bridge.
        // This code section here also redraws AND
        // and adjusts formatting around buildRange
        // which includes IF, WHEN, MEANS and IS.
        if (columnNow === col && !restart) {
          rowStop = getFurthest(rowStop, row)
          numOfRows = rowStop - rowBegin + 1
          const buildRange = sheet.getRange(rowBegin, columnNow, numOfRows, 1)
          const getITIS = sheet.getRange(rowBegin - 1, columnNow - 1).getValue()
          const checkITIS = (getITIS === 'IT IS')
          // rangeString = buildRange.getA1Notation();
          // SpreadsheetApp.getUi().alert(
          //   rangeString + ", " + keyword);
          if (keyword === 'OR' && !checkITIS) {
            // SpreadsheetApp.getUi().alert(keyword);
            buildRange.setBorder(null, false, false, true, false, false,
              'grey', SpreadsheetApp.BorderStyle.SOLID_THICK)
          } else if (keyword === 'AND' && !checkITIS) {
            // SpreadsheetApp.getUi().alert(
            //   keyword + ", " + row + ", " + col);
            sheet.getRange(row, col).offset(0, 1, 1, 2)
              .setBorder(true, true, false, false, false, false,
                'grey', SpreadsheetApp.BorderStyle.SOLID_THICK)
            buildRange.setBorder(null, false, false, true, false, false,
              'grey', SpreadsheetApp.BorderStyle.SOLID_THICK)
          }
          const getNextIF = sheet.getRange(rowBegin + 1, columnNow + 1).getValue()
          const checkNextIF = (getNextIF === 'IF')
          const buildIFHorizontal = sheet.getRange(rowBegin,
            columnNow + 1, 1, 2)
          if (checkNextIF) {
            buildIFHorizontal.setBorder(true, true, null, null, null, null,
              'grey', SpreadsheetApp.BorderStyle.SOLID_THICK)
          }
        }
      }
    }
    columnNow--
    // SpreadsheetApp.getUi().alert(columnNow);
    restart = true
    rowStop = rowBegin = 0
  }
}

function processHistory (h: ElementHistory, sheet: Sheet) {
  // Process the h.history Array.
  let restart = true
  let rowBegin = 0
  let rowStop = 0
  let numOfRows = 0
  let rangeString = ''
  let columnNow = 1
  let farCol = 1
  // Get furthest column.
  for (const element of h.history) {
    if (element != null) {
      farCol = getFurthest(farCol, element[0])
    }
  }
  // Convert the keyword
  // "UNLESS" to "AND", and its predicate to
  // NOT predicate.
  for (const element of h.history) {
    if (element != null) {
      if (element[1] === 'UNLESS') {
        element[1] = 'AND'
        element[2] = !element[2]
      }
    }
  }
  while (columnNow <= farCol) {
    for (const element of h.history) {
      if (element != null) {
        const row = h.history.indexOf(element)
        const [col, keyword, predicate] = element
        // Determine start of code block.
        if (columnNow === col && restart &&
          (keyword === 'IF' || keyword === 'WHEN' ||
          keyword === 'MEANS' || keyword === 'IS') &&
          rowBegin < row) {
          restart = false
          rowBegin = row
        }
        // Parse code block and update topLeft equation.
        // Must use setValue("") instead of clear()
        // because cannot clear borders formatting.
        if (columnNow === col && !restart) {
          rowStop = getFurthest(rowStop, row)
          numOfRows = rowStop - rowBegin + 1
          const buildRange = sheet.getRange(rowBegin, columnNow + 1, numOfRows, 1)
          rangeString = buildRange.getA1Notation()
          if (keyword === 'OR' || keyword === 'AND') {
            sheet.getRange(rowBegin - 1, columnNow)
              .setValue('=' + keyword.toLowerCase() +
              '(' + rangeString + ')')
          } else {
            sheet.getRange(rowBegin - 1, columnNow).setValue('')
          }
        }
      }
    }
    columnNow++
    restart = true
    rowStop = 0
  }
}

function getFurthest (prevIndex: number, index: number) {
  if (prevIndex < index) return index
  else return prevIndex
}

function isKeyword (cValue: string) {
  return (cValue === 'IF' || cValue === 'OR' ||
    cValue === 'AND' || cValue === 'WHEN' ||
    cValue === 'MEANS' || cValue === 'IS' ||
    cValue === 'IT IS' ||
    cValue === 'EVERY' || cValue === 'PARTY' ||
    cValue === 'HENCE' || cValue === 'LEST' ||
    cValue === 'UNLESS'
  )
}

function goodLayout (c: Range, enteredValue: string) {
  if (c.getBackground() !== '#ffffff') {
    SpreadsheetApp.getUi().alert(
      'ERROR: Background must be white colour')
    return false
  }
  if (isKeyword(enteredValue)) {
    if (c.getColumn() < 2) {
      SpreadsheetApp.getUi().alert(
        'ERROR: Keywords must be entered from column B onwards')
      return false
    }
    if (c.getRowIndex() < 3) {
      SpreadsheetApp.getUi().alert(
        'ERROR: Keywords must be entered from row 3 onwards')
      return false
    }
  }
  return true
}

function drawWords (c: Range, enteredValue: string) {
  // Identify keywords for formatting and drawing.
  if (enteredValue === 'IF' || enteredValue === 'WHEN') {
    c = drawIfWhenTop(c, enteredValue)
    if (c != null) {
      drawIfWhenOr(c, enteredValue)
    }
  } else if (enteredValue === 'OR') {
    drawIfWhenOr(c, enteredValue)
  } else if (enteredValue === 'AND') {
    drawAnd(c)
  } else if (enteredValue === 'IS' || enteredValue === 'MEANS') {
    c = drawIfWhenTop(c, enteredValue)
    if (c != null) {
      drawTeeOverIsMeans(c, enteredValue)
    }
  } else if (enteredValue === 'IT IS') {
    drawTeeForITIS(c, enteredValue)
  } else if (enteredValue === 'EVERY' || enteredValue === 'PARTY') {
    drawPlusUnderEvery(c, enteredValue)
  } else if (enteredValue === 'HENCE' || enteredValue === 'LEST') {
    drawHenceLest(c, enteredValue)
  } else if (enteredValue === 'UNLESS') {
    drawUnless(c, enteredValue)
  }
}

function drawIfWhenTop (c: Range, keyword: string): Range {
  // Check cell above for checkbox.
  // If no checkbox, move cValue down
  // and insert checkbox in original cell.
  const topCell = c.offset(-1, 0)
  if (topCell.getDataValidation() != null) {
    if (topCell.getDataValidation().getCriteriaType() === SpreadsheetApp.DataValidationCriteria.CHECKBOX) {
      return c
    } else return null
  } else if (topCell.isBlank()) {
    c.setValue(null)
    c.insertCheckboxes()
    c.offset(1, 0).setValue(keyword)
    return c.offset(1, 0)
  }
}

function drawIfWhenOr (c: Range, keyword: string) {
  if (keyword === 'OR') {
    c.offset(0, -1, 1, 9).clearFormat()
  }
  c.setHorizontalAlignment('right')
  if (c.offset(0, 1).isBlank()) {
    c.offset(0, 1).insertCheckboxes()
      .setBorder(null, true, false, false, false, false,
        'grey', SpreadsheetApp.BorderStyle.SOLID_THICK)
  }
  c.setBorder(null, null, null, true, false, false,
    'grey', SpreadsheetApp.BorderStyle.SOLID_THICK)
  if (c.offset(0, 2).isBlank()) {
    c.offset(0, 2).setValue('some condition')
  }
}

function drawAnd (c: Range) {
  c.offset(0, -1, 1, 9).clearFormat()
  c.setHorizontalAlignment('right')
  if (c.offset(0, 1).isBlank()) {
    c.offset(0, 1).insertCheckboxes()
      .setBorder(null, true, false, false, false, false,
        'grey', SpreadsheetApp.BorderStyle.SOLID_THICK)
  }
  c.offset(0, 1, 1, 2)
    .setBorder(true, true, false, false, false, false,
      'grey', SpreadsheetApp.BorderStyle.SOLID_THICK)
  c.setBorder(null, null, null, true, false, false,
    'grey', SpreadsheetApp.BorderStyle.SOLID_THICK)
  if (c.offset(0, 2).isBlank()) {
    c.offset(0, 2).setValue('some condition')
  }
}

function drawTeeOverIsMeans (c: Range, keyword: string) {
  c.offset(0, -1, 1, 9).clearFormat()
  c.offset(-1, 1).setValue('a Defined Term')
  c.offset(0, 0, 1, 3)
    .setBorder(true, false, false, false, false, false,
      'grey', SpreadsheetApp.BorderStyle.SOLID_THICK)
  c.offset(0, 0, 2, 1)
    .setBorder(true, false, false, true, false, false,
      'grey', SpreadsheetApp.BorderStyle.SOLID_THICK)
  c.offset(0, 0).setValue(keyword).setHorizontalAlignment('right')
  if (c.offset(0, 1).isBlank()) {
    c.offset(0, 1).insertCheckboxes()
  }
  c.offset(0, 2).setValue('a thing')
  c.offset(1, 0).setValue('OR').setHorizontalAlignment('right')
  c.offset(1, 1).insertCheckboxes()
  c.offset(1, 2).setValue('another thing')
}

function drawTeeForITIS (c: Range, keyword: string) {
  c.offset(0, -1, 3, 9).clear()
  c.setValue(keyword).setHorizontalAlignment('right')
  c.offset(0, 1).insertCheckboxes()
  c.offset(0, 2).setValue('a Defined Situation')
  c.offset(1, 0, 1, 5)
    .setBorder(true, false, false, false, false, false,
      'grey', SpreadsheetApp.BorderStyle.SOLID_THICK)
  c.offset(1, 1, 2, 1)
    .setBorder(true, false, false, true, false, false,
      'grey', SpreadsheetApp.BorderStyle.SOLID_THICK)
  c.offset(1, 1).setValue('WHEN').setHorizontalAlignment('right')
  c.offset(1, 2).insertCheckboxes()
  c.offset(1, 3).setValue('something holds')
  c.offset(2, 1).setValue('AND').setHorizontalAlignment('right')
  c.offset(2, 2).insertCheckboxes()
  c.offset(2, 3).setValue('something else holds')
}

function drawPlusUnderEvery (c: Range, keyword: string) {
  c.offset(0, -1, 3, 9).clear()
  c.setValue(keyword).setHorizontalAlignment('right')
  if (keyword === 'EVERY') { c.offset(0, 1).setValue('Entity') }
  if (keyword === 'PARTY') { c.offset(0, 1).setValue('P') }
  c.offset(1, 0).setValue('MUST').setHorizontalAlignment('right')
  c.offset(1, 1).setValue('BY').setHorizontalAlignment('right')
  c.offset(1, 2).setValue('some deadline')
  c.offset(2, 0).setValue('➔').setHorizontalAlignment('right')
  c.offset(2, 1).setValue('take').setHorizontalAlignment('right')
  c.offset(2, 2).setValue('some Action')
  c.offset(0, 0, 3).setBorder(false, false, false, true, false, false,
    'grey', SpreadsheetApp.BorderStyle.SOLID_THICK)
  c.offset(1, 0, 1, 4).setBorder(false, false, true, false, false, false,
    'grey', SpreadsheetApp.BorderStyle.SOLID_THICK)
  c.offset(1, 0).setBorder(false, false, true, true, false, false,
    'grey', SpreadsheetApp.BorderStyle.SOLID_THICK)
}

function drawHenceLest (c: Range, keyword: string) {
  c.offset(0, -1, 1, 9).clearFormat()
  c.setValue(keyword).setHorizontalAlignment('right')
  c.offset(0, 1, 1, 2).setBorder(false, true, true, false, false, false,
    'grey', SpreadsheetApp.BorderStyle.SOLID_THICK)
}

function drawUnless (c: Range, keyword: string) {
  c.offset(0, -1, 1, 9).clearFormat()
  c.setValue(keyword).setHorizontalAlignment('right')
  c.offset(0, 1).insertCheckboxes()
    .setBorder(true, false, true, true, false, false,
      'grey', SpreadsheetApp.BorderStyle.SOLID_THICK)
  if (c.offset(0, 2).isBlank()) {
    c.offset(0, 2).setValue('some exception')
  }
}

export {isKeyword}
