import clr

# Dynamo
clr.AddReference("RevitServices")
from RevitServices.Persistence import DocumentManager
from RevitServices.Transactions import TransactionManager

# Revit
clr.AddReference("RevitAPI")
from Autodesk.Revit.DB import *

doc = DocumentManager.Instance.CurrentDBDocument

# ---------------------------------
# INPUT
# ---------------------------------

def flatten(items):
    result = []
    for item in items:
        if isinstance(item, list):
            result.extend(flatten(item))
        else:
            result.append(item)
    return result

# Flatten in case IN[0] comes in as a nested list (list levels / lacing upstream)
allSheets = flatten(UnwrapElement(IN[0]))

# ---------------------------------
# FILTER: opt out sheets with "Appears In Sheet List" unchecked
# ---------------------------------

includedSheets = []

for sheet in allSheets:

    p = sheet.get_Parameter(BuiltInParameter.SHEET_SCHEDULED)

    if p and p.AsInteger() == 1:
        includedSheets.append(sheet)

# ---------------------------------
# SORT
# ---------------------------------

def getString(sheet, name):

    p = sheet.LookupParameter(name)

    if p:
        return p.AsString() or ""

    return ""

def getInteger(sheet, name):

    p = sheet.LookupParameter(name)

    if p:
        try:
            return p.AsInteger()
        except:
            return 0

    return 0

includedSheets.sort(
    key=lambda s:
    (
        getInteger(s, "Discipline Sort Order"),
        getString(s, "Discipline Name"),
        getString(s, "Sheet Category"),
        getString(s, "Sheet Number")
    )
)

total = len(includedSheets)

# ---------------------------------
# WRITE PARAMETERS
# ---------------------------------

TransactionManager.Instance.EnsureInTransaction(doc)

for i, sheet in enumerate(includedSheets):

    seq = sheet.LookupParameter("Sheet Sequence")
    tot = sheet.LookupParameter("Total Sheets")

    if seq and not seq.IsReadOnly:
        seq.Set(i + 1)

    if tot and not tot.IsReadOnly:
        tot.Set(total)

TransactionManager.Instance.TransactionTaskDone()

OUT = includedSheets
