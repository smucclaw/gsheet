# How to Use the Legal Spreadsheet?

## About the Legal Spreadsheet<a name="about" />

The Legal Spreadsheet helps users to automate their legal writing.

## Developer Setup
 
- Install [clasp](https://developers.google.com/apps-script/guides/clasp)
- Run `clasp login`. Please use account you are going to use for spreadsheet development
- [Enable App Script API](https://script.google.com/home/usersettings)
- Run `clasp create`. This will create a `.clasp.json` file locally.
- Finally run `clasp push`. This will compile and push the code to your google account.
- Open spreadsheet in your google account. It has name of the code checkout folder.

## Keywords

### Single Cell Keywords<a name="single-cell-keywords" />

The typed keywords here are outlined in blue in the automatically generated layouts.

| **Type the Keyword** | **Google Sheet Will Output This Layout** |
| --- | --- |
| AND | ![type AND in a cell in the Legal Spreadsheet](images/AND.png) |
| OR | ![type OR in a cell in the Legal Spreadsheet](images/OR.png) |
| EVERY | ![type EVERY in a cell in the Legal Spreadsheet](images/EVERY.png) |
| IF | ![type IF in a cell in the Legal Spreadsheet](images/IF.png) |
| WHEN | ![type WHEN in a cell in the Legal Spreadsheet](images/WHEN.png) |
| MEANS<sup>[1](#footnote1)</sup> | ![type MEANS in a cell in the Legal Spreadsheet](images/MEANS.png) |
| IS<sup>[1](#footnote1)</sup> | ![type IS in a cell in the Legal Spreadsheet](images/IS.png) |
| IT IS<sup>[1](#footnote1)</sup> | ![type IT IS in a cell in the Legal Spreadsheet](images/ITIS.png) |
| HENCE | ![type HENCE in a cell in the Legal Spreadsheet](images/HENCE.png) |
| LEST | ![type LEST in a cell in the Legal Spreadsheet](images/LEST.png) |
| UNLESS | ![type UNLESS in a cell in the Legal Spreadsheet](images/UNLESS.png) |

<a name="footnote1">1</a>: MEANS, IS and IT IS starts a constitutive rule.

### Keyword Cell Sequences<a name="keyword-cell-sequences" />

These are the ways the keyword sequences can be typed out.  Each keyword must be typed in each cell from top to bottom as shown below.  There should only be one keyword per row of cells.  Each output layout will then appear as shown when each keyword is typed.  There is a waiting time of 3-5 seconds for each keyword's output to show completely.

| **Type these keywords** | **Keyword Sequence Logic** | **Layouts of these keywords**<sup>[2](#footnote2)</sup> |
| --- | --- | --- |
| IF, OR, OR | IF C4 OR C5 OR C6 | ![type IF, OR, OR in the Legal Spreadsheet](images/IFOROR.png) |
| IF, AND, AND | IF C4 AND C5 AND C6 | ![type IF, AND, AND in the Legal Spreadsheet](images/IFANDAND.png) |
| IF, IF, OR, AND | IF (D5 OR D6) AND C7 | ![type IF, OR, AND in the Legal Spreadsheet](images/IFIFORAND.png) |
| IF, IF, OR, OR, AND, AND | IF (D5 OR D6 OR D7) AND C8 AND C9 | ![type IF, IF, OR, OR, AND, AND in the Legal Spreadsheet](images/IFIFORORANDAND.png) |

<a name="footnote2">2</a>: The logic formula is at the top left outlined in red.  The cell outlined in blue is the cell where the logic formula resides in.

## Appendix A - Glossary<a name="glossary" />

| **Term** | **Explanation** |
| --- | --- |
| Constitutive rules | Rules that make possible new forms of behaviour. |
