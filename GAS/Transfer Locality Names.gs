function import_to_info() {
  /* This function will transfer localities from import2 to info */
  
  // Check that user wants to execute this command
  cont_msg = "Are you sure you want to transfer locality names from \
  the Import sheet to the Info sheet?"
  cont_ans = Browser.msgBox(cont_msg, Browser.Buttons.OK_CANCEL)
  if(cont_ans == "ok") {
    // Intialize Spreadsheet and Sheets
    S = SpreadsheetApp.getActiveSpreadsheet();
    import_sheet = S.getSheetByName("Import2");
    info_sheet = S.getSheetByName("Info");
    
    // Row and Col locations for num localities, pull, and target
    loc_row = 1;
    loc_col = 4;
    pull_row = 2;
    pull_col = 2;
    target_row = 2;
    target_col = 1;
    clear_len = 500;
    
    // Obtain the number of localities
    num_local = import_sheet.getRange(loc_row, loc_col).getValue();  
    
    // Print Message if the number of localities equals zero
    error_msg = "Localities did not transfer. Check URL, Table #, and Column \
    Name in the Import sheet";
    
    // 499 occurs when every value is an #N/A (empty or incorrect)
    if(num_local == 499) {
      Browser.msgBox(error_msg)
    } 
    else {
      // Set the pull range (Import), pull data, and target (info) ranges
      pull_range = import_sheet.getRange(pull_row, pull_col, num_local);
      pull_data = pull_range.getValues();
      target_range = info_sheet.getRange(target_row, target_col, num_local);
      target_clear_range = info_sheet.getRange(target_row, target_col, clear_len);
      
      // Clear the target range
      target_clear_range.clearContent();
      
      // Transfer values
      target_range.setValues(pull_data)
    }
  }
}

function info_to_other(sheet_name) {
  /* This function will transfer localities from info to */

  // Intialize Spreadsheet and Sheets
  S = SpreadsheetApp.getActiveSpreadsheet();
  sheet = S.getSheetByName(sheet_name);
  info_sheet = S.getSheetByName("Info");
  
  // Row and Col locations for num localities, pull, and target
  loc_row = 2;
  loc_col = 4;
  pull_row = 2;
  pull_col = 1;
  target_row = 2;
  target_col = 1;
  clear_len = 500;
  
  // Obtain the number of localities
  num_local = info_sheet.getRange(loc_row, loc_col).getValue();
  
  // Print Message if the number of localities equals zero
  error_msg = "Localities did not transfer. Check that the Info sheet \
contains the  desired localities. If not, first transfer localities \
from the Import sheet";
  
  // This occurs when every value is an #N/A
  if(num_local == 0) {
    Browser.msgBox(error_msg)
  } 
  else {
    // Set the pull range (Import), pull data, and target (info) ranges
    pull_range = info_sheet.getRange(pull_row, pull_col, num_local);
    pull_data = pull_range.getValues();
    target_range = sheet.getRange(target_row, target_col, num_local);
    target_clear_range = sheet.getRange(target_row, target_col, clear_len);
    
    // Clear the target range
    target_clear_range.clearContent();
    
    // Transfer values
    target_range.setValues(pull_data)
  }
  
}

function transfer_localities_from_info() {
  /* This function will transfer localities from info to collection, 
  digitizing, and matching */
  
  // Check that user wants to execute this command
  cont_msg = "Are you sure you want to transfer locality names from \
  the Info sheet to the other sheets?"
  cont_ans = Browser.msgBox(cont_msg, Browser.Buttons.OK_CANCEL)
  
  if(cont_ans == "ok") {
    info_to_other("Collection")
    info_to_other("Digitizing")
    info_to_other("Matching")
  }
}
