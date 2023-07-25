/**
 * @OnlyCurrentDoc
 */
const configLibDefaults = LegalSSConfigLib.configLibDefaults();

appConfig = {
  port: configLibDefaults.parentUrlPort,
  host: configLibDefaults.parentUrlHost,
  liveUpdates: true
}

const loadDev = LegalSSCodeLib.loadDev;
const showSidebarLib = LegalSSCodeLib.showSidebar;
const lastEditTimeKey = LegalSSCodeLib.lastEditTimeKey;

let sidebarRefreshInterval = 60000;
let properties = PropertiesService.getDocumentProperties();

let ui = SpreadsheetApp.getUi();
let sidebarHtml = HtmlService.createTemplateFromFile('main');

function onOpen() {
  LegalSSCodeLib.createSidebarMenu(ui);
}

function createSpreadsheetOpenTrigger() {
  const ss = SpreadsheetApp.getActive();
  const allTriggers = ScriptApp.getProjectTriggers();
  Logger.log(`found: ${allTriggers.length} triggers`);
  if (allTriggers.length == 0) {
    ScriptApp.newTrigger('onOpenSideBar')
        .forSpreadsheet(ss)
        .onOpen()
        .create();
  }
}

function showL4Help() {
  const htmlTemplate = HtmlService.createTemplateFromFile('help.html');
  htmlTemplate.url = 'https://l4-documentation.readthedocs.io/en/stable/';
  const htmlOutput = htmlTemplate.evaluate().setHeight(50).setWidth(200);
  const ui = SpreadsheetApp.getUi();
  ui.showModelessDialog(htmlOutput, 'L4 Help');
  Utilities.sleep(2000);
};

function onOpenSideBar() {
  showSidebarLib(appConfig, sidebarHtml);
  LegalSSCodeLib.resetLastEditTime(properties);
};


function showSidebar() {
  createSpreadsheetOpenTrigger();
  showSidebarLib(appConfig, sidebarHtml);
}

function onChange(e) {
  loadDev(appConfig);
  if (! appConfig.liveUpdates) { return }

  Logger.log(`onChange running. liveUpdates=${appConfig.liveUpdates}; port=${appConfig.port}`);
}

function onEdit(e) {
  const lastEditTime = properties.getProperty(lastEditTimeKey);

  const currentEditTime = new Date().getTime();

  if (lastEditTime == 0) {
    lastEditTime = currentEditTime;
    properties.setProperty(lastEditTimeKey, lastEditTime);
  }
  const timePassed = currentEditTime - lastEditTime;

  if (lastEditTime && (timePassed < sidebarRefreshInterval)) {
    return null;
  }

  loadDev(appConfig);

  // Respond to Edit events on spreadsheet.
  if (! appConfig.liveUpdates) { return }

  const c = e.range;
  if (c.getBackground() != "#ffffff") {
    return;
  }

  if (lastEditTime && (timePassed > sidebarRefreshInterval)) {
    showSidebar();
    resetLastEditTime();
  }

}
