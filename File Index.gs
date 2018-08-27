function set_file_indexes() {
  /* This function will set the file indexes for any file with current file index -1*/
  
  // Check that user wants to execute this command
  cont_msg = "Are you sure you want to set file indexes in the Conversion sheet?"
  cont_ans = Browser.msgBox(cont_msg, Browser.Buttons.OK_CANCEL)
  if(cont_ans == "ok"){
    // Intialize Spreadsheet and Sheet
    S = SpreadsheetApp.getActiveSpreadsheet();
    conversion_sheet = S.getSheetByName("Conversion");
    
    // Obtain the number of files in the Conversion sheet
    loc_row = 2;
    loc_col = 1;
    count = 0;
    
    while(conversion_sheet.getRange(loc_row + count, loc_col).getValue() != 0) {
      count += 1;
    }
    
    // Initialize the ix_col
    ix_col = 2;
    ix_row = 2;
    
    // Iterate through every file to check if their index is -1
    for(i = 0 ; i < count; i++) {
      ix = conversion_sheet.getRange(i + ix_row, ix_col).getValue();
      
      if(ix == -1) {
        max_ix = -1;
        locality = conversion_sheet.getRange(i + ix_row, loc_col).getValue();
        
        // Loop through trying to find the max index if file index is -1
        for(j = 0; j < count; j++) {
          // Get localilty for the j value
          j_locality = conversion_sheet.getRange(j + ix_row, loc_col).getValue();
          
          // If the localities match, check if current index is bigger than max index
          if(j_locality == locality) {
            curr_ix = conversion_sheet.getRange(j + ix_row, ix_col).getValue();
            if (max_ix < curr_ix) {
              max_ix = curr_ix;
            }
          }
        }
        // Set the index of our file equal to max_ix + 1
        conversion_sheet.getRange(i + ix_row, ix_col).setValue(max_ix + 1);
      }
    }
  }
}

function check_duplicates() {
  /* This function will check for duplicate files in the Conversion sheet.
  It will set duplicate file's file index to -99 */
  
  // Check that user wants to execute this command
  cont_msg = "Are you sure you want to check for duplicate rows in the Conversion sheet?"
  cont_ans = Browser.msgBox(cont_msg, Browser.Buttons.OK_CANCEL)
  if(cont_ans == "ok"){
    // Intialize Spreadsheet and Sheet
    S = SpreadsheetApp.getActiveSpreadsheet();
    conversion_sheet = S.getSheetByName("Conversion");
    
    // Obtain the number of files in the Conversion sheet
    loc_row = 2;
    loc_col = 1;
    count = 0;
    
    while(conversion_sheet.getRange(loc_row + count, loc_col).getValue() != 0) {
      count += 1;
    }
    
    // Initialize the mod_file
    mod_file_col = 6;
    mod_file_row = 2;
    ix_col = 2;
    
    // Iterate through every file to check to check if other rows have matching mod files
    for(i = 0 ; i < count; i++) {
      mod_file = conversion_sheet.getRange(i + mod_file_row, mod_file_col).getValue();
      
      // Iterate through all other files
      for(j = 0; j < count; j++) {
        mod_file_j = conversion_sheet.getRange(j + mod_file_row, mod_file_col).getValue();
        j_ix = conversion_sheet.getRange(j + mod_file_row, ix_col).getValue();
        // If file names are same, make ix equal to -99
        if(i != j && mod_file == mod_file_j && j_ix != -99) {
          conversion_sheet.getRange(i + mod_file_row, ix_col).setValue(-99);
        }
      }
    }
  }
}

