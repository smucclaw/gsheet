/**
 * @OnlyCurrentDoc
 */

//Max
Logger.log("global top");
Logger.log("legalSSConfigLib configLibDefaults")
Logger.log(ConfigLib.configLibDefaults())

const configLibDefaults = ConfigLib.configLibDefaults();

var port       = configLibDefaults.parentUrlPort;
var url_host = configLibDefaults.parentUrlHost;

var liveUpdates = true;
let sidebarRefreshInterval = 60000;
var properties = PropertiesService.getDocumentProperties();
const key = "lastEditTime";
let ui = SpreadsheetApp.getUi();

function onOpen() {
  createSidebarMenu();
  showSidebar();
  Logger.log("onOpen: after UrlFetchApp");
  resetLastEditTime();
}

function resetLastEditTime() {
  properties.setProperty(key, 0);
}

function createSidebarMenu() {
  ui.createMenu('L4')
    .addItem('Refresh', 'showSidebar')
    .addItem('Help', 'showL4Help')
    .addToUi();
}

function loadDev() {
  let spreadsheet = SpreadsheetApp.getActiveSpreadsheet();
  let sheet = SpreadsheetApp.getActiveSheet();
  let range = sheet.getRange("A1:Z10").getDisplayValues();
  // expecting 249602568
  Logger.log("expecting sheet = 249602568");
  Logger.log("reading sheet = " + sheet.getSheetId());
  port = devPort(range) || port;
  url_host = devHost(range);
  liveUpdates = devScan(range, /live updates (true|false)/i) || true; if (liveUpdates.toString().toLowerCase() == "false") { liveUpdates = false }
  Logger.log("setting port to " + port);
  Logger.log("setting liveUpdates to " + liveUpdates);
}

const showL4Help = () => {
  const htmlTemplate = HtmlService.createTemplateFromFile('help.html');
  htmlTemplate.url = 'https://l4-documentation.readthedocs.io/en/stable/';
  const htmlOutput = htmlTemplate.evaluate().setHeight(50).setWidth(200);
  const ui = SpreadsheetApp.getUi();
  ui.showModelessDialog(htmlOutput, 'L4 Help');
  Utilities.sleep(2000);
};

function showSidebar() {
  loadDev();  
  let cachedUuid = saveUuid();
  let [spreadsheetId, sheetId] = getSsid();
  const workDir =  `${url_host}/port/${port}/workdir/`;
  let workDirUrl = (workDir + cachedUuid + "/" + spreadsheetId + "/" + sheetId + "/");
  
  Logger.log("port     = " + port);
  Logger.log("url_host = " + url_host);
  Logger.log("url_hp() = " + url_hp());
  Logger.log("url_wd() = " + workDir);
  Logger.log(`workDirUrl = ` + workDirUrl);
  let sidebar = HtmlService.createTemplateFromFile('main');
  Logger.log("calling exportCSV()");
  sidebar.fromFlask = JSON.parse(CommonLib.exportCSV(url_hp() + '/post', cachedUuid, spreadsheetId, sheetId));
  Logger.log("fromFlask returned");
  Logger.log(sidebar.fromFlask);
  sidebar.native_url          = workDirUrl + "native/LATEST.hs";
  sidebar.corel4url           = workDirUrl + "corel4/LATEST.l4";
  sidebar.petri_url           = workDirUrl + "petri/LATEST.png"
  sidebar.json_url            = workDirUrl + "json/LATEST.json"
  sidebar.epilog_url          = workDirUrl + "epilog/LATEST.epilog"
  sidebar.org_url             = workDirUrl + "org/LATEST.org"
  sidebar.purs_url            = workDirUrl + "purs/LATEST.purs"
  sidebar.md_url              = workDirUrl + "md/LATEST.md"
  sidebar.docx_url             = workDirUrl + "docx/LATEST.docx"
  sidebar.pdf_url              = workDirUrl + "pdf/LATEST.pdf"
  sidebar.maude_plaintext_url  = workDirUrl + "maude/LATEST.natural4"
  sidebar.maude_vis_url = workDirUrl + "maude/LATEST_state_space.html"
  sidebar.maude_race_cond_url = workDirUrl + "maude/LATEST_race_cond_0.html"
  sidebar.ts_url              = workDirUrl + "ts/LATEST.ts"
  sidebar.petri_thumbnail_img = workDirUrl + "petri/LATEST-small.png"
  sidebar.port                = port;
  sidebar.liveUpdates         = liveUpdates;
  Logger.log("returned from exportCSV()");

  Logger.log("looking for v8k_url in fromFlask")
  var v8k_url = sidebar.fromFlask.v8k_url;
  if (v8k_url) {
    Logger.log(`matched a v8k_url: ${v8k_url}`);
    sidebar.v8k_url = url_host + v8k_url;
  } else {
    Logger.log("unable to return valid v8k link");
    sidebar.v8k_url = "#";
  }

  let aasvgUrl = url_hp() + "/aasvg/" + cachedUuid + "/" + spreadsheetId + "/" + sheetId + "/";

  sidebar.fromFlask.aasvg_index = 
    sidebar.fromFlask.aasvg_index
    .replace(/href="(\S+)(\.svg">)(.+?)<\/a>/sg,
             "href=\"" + aasvgUrl + "$1-full$2<br/>$3" +
             "<br><img src=\"" + aasvgUrl + "$1-tiny.svg\"></a>");
  


  Logger.log("rewrote aasvg_index = ")
  Logger.log(sidebar.fromFlask.aasvg_index)
  Logger.log("drawing sidebar");
  let sidebarOutput = sidebar.evaluate().setTitle('Output from L4');
  SpreadsheetApp.getUi().showSidebar(sidebarOutput);
  Logger.log("drawn sidebar");
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

function url_hp() {
  Logger.log("url_hp() called");

  var toreturn = `${url_host}/port/${port}`;

  Logger.log("returning " + toreturn);
  return toreturn;
}

function devScan(range, scanregex) {
  for (let i = 0; i < range.length; i++) {
    let asOneLine = range[i].join(" ");
    if (scan = asOneLine.match(scanregex)) {
      Logger.log(`devScan hit: ${asOneLine} matched ${scan}`);
      return scan[1];
    }
  }
  return null;
}

function devPort(range) {
  let mymatch = devScan(range, /devMode port (\d+)/i);
  if (mymatch) { return mymatch }
  return configLibDefaults.parentUrlPort;
}


function devHost(range) {
  let mymatch = devScan(range, /devMode host (\S+)/i);
  if (mymatch) { return mymatch }
  return configLibDefaults.parentUrlHost;
}

function onChange(e) {
  loadDev();  
  if (! liveUpdates) { return }

  Logger.log(`onChange running. liveUpdates=${liveUpdates}; port=${port}`);
}

function onEdit(e) {
  var lastEditTime = properties.getProperty(key);
  var currentEditTime = new Date().getTime();
  if (lastEditTime == 0) {
    lastEditTime = currentEditTime;
    properties.setProperty(key, lastEditTime);
  }
  var timePassed = currentEditTime - lastEditTime;
  if (lastEditTime && (timePassed < sidebarRefreshInterval)) {
    return null;
  }

  loadDev();  

  // Respond to Edit events on spreadsheet.
  if (! liveUpdates) { return }

  let c = e.range;
  if (c.getBackground() != "#ffffff") {
    return;
  }

  if (lastEditTime && (timePassed > sidebarRefreshInterval)) {
    // If more than 60 seconds have passed since the last edit, refresh Sidebar.
    showSidebar();
    resetLastEditTime();
  }
  
}

