StartMessage = """
This is the HexoSys Lunch Bot. Want to /register?
"""
UserHelp = """
/options will give the menu for the next day
/mine will remind you of your choice
"""
AdminHelp = """
/draft lets you create a new menu
/publish makes draft available to users
/close closes the menu to users

Be careful with publish and close!
If you republish a draft all user choices will be gone!

/add adds new items to draft

/preview lists draft menu items for review
/status gives you status report on next menu
/report gives you full report on closed menu

/message send announcements to users

/options will give the menu for the next day
/mine will remind you of your choice
"""
InvalidInput = """
Invalid input!
"""
UnauthorizedAccess = """
You are not eligible to run this command!
"""
OperationCanceled = """
Operation canceled!
"""
DraftCreation = """
Choose a day to create the draft for or /cancel.
"""
DraftCreated = """
Draft created. Use /add to add options.
"""
ItemAddition = """
Type the item or /cancel.
"""
ItemAdded = """
Item added. Use /add to add more options. If done use /preview then /publish.
"""
PublishAssertion = """
Are you sure? This will overwrite the ongoing orders that are not closed.
"""
PublishAsserted = """
Menu published. use /options to see the menu and order your lunch.
"""
OptionSelected = """
Order updated. You can check using /mine.
"""
OrderClosure = """
Are you sure? This will overwrite the closed orders.
"""
OrderClosed = """
Order closed. use /report to see orders.
"""
PreviewDraft = """
You can use /publish to make the draft accessible.
"""
RegisterMessage = """
I will register you as soon as I can. When registered you can use /options.
"""
