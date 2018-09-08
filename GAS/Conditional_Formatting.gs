function col2let(column)
{
  var temp, letter = '';
  while (column > 0)
  {
    temp = (column - 1) % 26;
    letter = String.fromCharCode(temp + 65) + letter;
    column = (column - temp - 1) / 26;
  }
  return letter;
}

function let2col(letter)
{
  var column = 0, length = letter.length;
  for (var i = 0; i < length; i++)
  {
    column += (letter.charCodeAt(i) - 64) * Math.pow(26, length - i - 1);
  }
  return column;
}

function implement_conditional(sheet_name, color_count_col) {
  /* This function will implement dynamic formatting 
  
  Arguments:
  sheet_name: string of the name of the sheet to apply the conditional format
  color_count_col: the column in which the number of color count is in.
  (the meaning column in info for the sheet we are applying conditional to) */
  
  // Check that user wants to execute this command
  cont_msg = "Are you sure you want to implement the conditional formatting?"
  cont_ans = Browser.msgBox(cont_msg, Browser.Buttons.OK_CANCEL)
  if(cont_ans == "ok") {
    
  // Initialize spreadsheet and sheets
  S = SpreadsheetApp.getActiveSpreadsheet();
  sheet = S.getSheetByName(sheet_name);
  info_sheet = S.getSheetByName("Info");
  
  
  /* Obtain the number of columns (entry fields) and rows (localities) in 
  the Collection sheet, and obtain the number of  colors in the Info sheet*/
  color_count_row =  4;
  
  color_count = info_sheet.getRange(color_count_row, color_count_col).getValue();
  
  // col_count will equal the number of columns in the selected sheet
  col_count = 0;
  while (sheet.getRange(1, col_count + 1).getValue() != 0) {
    col_count += 1;
  }
  
  // row_count will equal the number of localities
  row_count = 0;
  while (sheet.getRange(row_count + 2, 1).getValue() != 0) {
    row_count += 1;
  }
  
  // Initialize the background color rows
  back_color_row = 8;
  back_color_col = color_count_col - 2;
  state_id_row = 8;
  state_id_col = color_count_col - 1;
  state_col = 2;

  // Clear then initialize the starting object for conditionalFormatRules
  sheet.clearConditionalFormatRules();
  current_rules = sheet.getConditionalFormatRules();
  
  // Iterate through every background color given in info
  for (i = 0; i < color_count; i++) {
    
    // get the current background color
    back_color = info_sheet.getRange(back_color_row + i, back_color_col).getBackground();
    
    // get the state ID
    state_id = info_sheet.getRange(state_id_row + i, state_id_col).getValue();

    // Set conditional formatting rule for every row
    for (j = 0; j < row_count; j++) {
      // set range for formatting
      range = sheet.getRange(j + 2, 1, 1, col_count);
      
      // create formula for rule
      col_state_col_let = col2let(state_col);
      current_row = j + 2;
      
      formula = "=IF($" + col_state_col_let + "$" + current_row + "=" + 
        state_id + ",1,0)";      
      
      // Create rule
      rule = SpreadsheetApp.newConditionalFormatRule()
      .whenFormulaSatisfied(formula)
      .setBackground(back_color)
      .setRanges([range])
      .build();
      
      // Add this rule to our current rules
      current_rules.push(rule)    
    }
  }
  
  // apply current rules to sheet
  sheet.setConditionalFormatRules(current_rules) 
  
  // Get correct columns in information sheet
  if (sheet_name == "Collection") {
    icol1 = "G"
    icol2 = "H"    
  }
  else if (sheet_name == "Digitization") {
    icol1 = "K"
    icol2 = "L" 
  }
  else if (sheet_name == "Matching") {
    icol1 = "O"
    icol2 = "P" 
  }
    
  // Set start ranges
  irow1 = 8
  irow2 = 8 + color_count
    
  // Get the lookup range and index to look
  lookup_range = "Info!" + icol1 + irow1 + ":" + icol2 + irow2
  index = 2
  // Add vlookup formula in the Note/third column
  for (j = 0; j < row_count; j++) {
    row = j + 2
    search_key = "B" + row   
    formula = "=VLOOKUP(" + search_key + "," + lookup_range + "," + index + ")"
    current_range = sheet.getRange(row, 3);
    current_range.setValue(formula);
  }
  
 
  }
}

function implement_conditional_collection() {
  /* This function will create conditional formatting for the Collection sheet */
  implement_conditional("Collection", 8)
}

function implement_conditional_digitization() {
  /* This function will create conditional formatting for the Collection sheet */
  
  implement_conditional("Digitization", 12)
}

function implement_conditional_matching() {
  /* This function will create conditional formatting for the Collection sheet */
  
  implement_conditional("Matching", 16)
}