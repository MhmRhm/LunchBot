import database as db
import messages, json, logging
from datetime import (
    date,
    timedelta
)
from telegram import (
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    Update,
    User
)
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

users = None
admin = None
adminChat = None
NextState = 1

def readUsers():
    logging.info("reading users")
    with open("users.json", "r") as file:
        global users
        global admin
        data = json.load(file)
        users = data["users"]
        admin = data["admin"]

def readToken() -> str:
    logging.info("reading token")
    with open("token", "r") as file:
        return file.readline()

def hasUserPrivileges(effectiveUser: User) -> bool:
    return bool(list(filter(lambda x: x["id"] == effectiveUser["id"], users)))

def hasAdminPrivileges(effectiveUser: User) -> bool:
    return effectiveUser["id"] == admin["id"]

async def startCommand(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logging.info("start command received")
    logging.info(update.effective_user)
    await update.message.reply_text(messages.StartMessage)

async def helpCommand(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logging.info("help command received")
    logging.info(update.effective_user)
    global adminChat
    if hasAdminPrivileges(update.effective_user):
        adminChat = update
        readUsers()
        await update.message.reply_text(messages.AdminHelp)
    elif hasUserPrivileges(update.effective_user):
        await update.message.reply_text(messages.UserHelp)
    else:
        await update.message.reply_text(messages.UnauthorizedAccess)

async def draftCommand(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    logging.info("draft command received")
    logging.info(update.effective_user)
    if not hasAdminPrivileges(update.effective_user):
        await update.message.reply_text(messages.UnauthorizedAccess)
        return ConversationHandler.END
    today, oneDay = date.today(), timedelta(days=1)
    replyKeyboard = [[f"{today + oneDay}", f"{today + 2 * oneDay}"], [f"{today + 3 * oneDay}", f"{today + 4 * oneDay}"]]
    await update.message.reply_text(
        messages.DraftCreation,
        reply_markup=ReplyKeyboardMarkup(
            replyKeyboard, one_time_keyboard=True,
            input_field_placeholder="Which day?",
            resize_keyboard=True
        ),
    )
    return NextState

async def draftCallback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    logging.info("draft callback invoked")
    logging.info(update.effective_user)
    logging.info(update.message.text)
    try:
        draftDate = date.fromisoformat(update.message.text)
    except:
        await update.message.reply_text(messages.InvalidInput, reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END
    db.createDraft(menuDate=draftDate)
    await update.message.reply_text(messages.DraftCreated, reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

async def cancelCommand(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    logging.info("cancel command received")
    logging.info(update.effective_user)
    await update.message.reply_text(messages.OperationCanceled, reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

draftHandler = ConversationHandler(
    entry_points=[CommandHandler("draft", draftCommand)],
    states={
        NextState: [CommandHandler("cancel", cancelCommand), MessageHandler(filters.TEXT, draftCallback)]
    },
    fallbacks=[MessageHandler(filters.TEXT, cancelCommand)],
)

async def addItemCommand(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    logging.info("add command received")
    logging.info(update.effective_user)
    if not hasAdminPrivileges(update.effective_user):
        await update.message.reply_text(messages.UnauthorizedAccess)
        return ConversationHandler.END
    await update.message.reply_text(messages.ItemAddition)
    return NextState

async def addItemCallback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    logging.info("add callback invoked")
    logging.info(update.effective_user)
    logging.info(update.message.text)
    db.addMenuOption(update.message.text)
    await update.message.reply_text(messages.ItemAdded, reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

addItemHandler = ConversationHandler(
    entry_points=[CommandHandler("add", addItemCommand)],
    states={
        NextState: [CommandHandler("cancel", cancelCommand), MessageHandler(filters.TEXT, addItemCallback)]
    },
    fallbacks=[MessageHandler(filters.TEXT, cancelCommand)],
)

async def publishCommand(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    logging.info("publish command received")
    logging.info(update.effective_user)
    if not hasAdminPrivileges(update.effective_user):
        await update.message.reply_text(messages.UnauthorizedAccess)
        return ConversationHandler.END
    replyKeyboard = [["Yes", "No"]]
    await update.message.reply_text(
        messages.PublishAssertion,
        reply_markup=ReplyKeyboardMarkup(
            replyKeyboard, one_time_keyboard=True,
            resize_keyboard=True
        ),
    )
    return NextState

async def publishCallback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    logging.info("publish callback invoked")
    logging.info(update.effective_user)
    if update.message.text != "Yes":
        await update.message.reply_text(messages.OperationCanceled, reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END
    db.publish()
    await update.message.reply_text(messages.PublishAsserted, reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

publishHandler = ConversationHandler(
    entry_points=[CommandHandler("publish", publishCommand)],
    states={
        NextState: [MessageHandler(filters.Regex("^(Yes|No)$"), publishCallback)]
    },
    fallbacks=[MessageHandler(filters.TEXT, cancelCommand)],
)

async def optionsCommand(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    logging.info("options command received")
    logging.info(update.effective_user)
    if not hasUserPrivileges(update.effective_user):
        await update.message.reply_text(messages.UnauthorizedAccess)
        return ConversationHandler.END
    options = db.getMenuOptions()
    msg = '\n'.join([str(option.id) + ". " + option.description for option in options])
    msg = db.getNextDate().date.strftime("%a %b %d, %Y") + "\n" + msg
    replyKeyboard = [[str(option.id) for option in options], ["Opt-out"]]
    await update.message.reply_text(msg,
        reply_markup=ReplyKeyboardMarkup(
            replyKeyboard, one_time_keyboard=True,
            resize_keyboard=True
        ),
    )
    return NextState

async def optionsCallback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    logging.info("options callback invoked")
    logging.info(update.effective_user)
    logging.info(update.message.text)
    userInput = -1
    if 1 <= int(update.message.text) <= len(db.getMenuOptions()):
        userInput = int(update.message.text)
    elif update.message.text == "Opt-out":
        userInput = None
    if userInput == -1:
        await update.message.reply_text(messages.InvalidInput, reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END
    db.updateUserChoice(idOfUser=update.effective_user["id"], idOfChoice=userInput)
    await update.message.reply_text(messages.OptionSelected, reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

optionsHandler = ConversationHandler(
    entry_points=[CommandHandler("options", optionsCommand)],
    states={
        NextState: [CommandHandler("cancel", cancelCommand), MessageHandler(filters.TEXT, optionsCallback)]
    },
    fallbacks=[MessageHandler(filters.TEXT, cancelCommand)],
)

async def mineCommand(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logging.info("mine command received")
    logging.info(update.effective_user)
    if not hasUserPrivileges(update.effective_user):
        await update.message.reply_text(messages.UnauthorizedAccess)
        return
    currentDate, currentChoice, nextDate, nextChoice = db.getUserChoice(idOfUser=update.effective_user["id"])
    msg = ''
    if currentDate:
        msg = msg + currentDate.date.strftime("%a %b %d, %Y") + "\n"
        if currentChoice:
            msg = msg + currentChoice.description
        else:
            msg = msg + "Nothing"
    msg = msg + "\n"
    if nextDate:
        msg = msg + nextDate.date.strftime("%a %b %d, %Y") + "\n"
        if nextChoice:
            msg = msg + nextChoice.description
        else:
            msg = msg + "Nothing"
    await update.message.reply_text(msg)

async def closeCommand(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    logging.info("close command received")
    logging.info(update.effective_user)
    if not hasAdminPrivileges(update.effective_user):
        await update.message.reply_text(messages.UnauthorizedAccess)
        return ConversationHandler.END
    replyKeyboard = [["Yes", "No"]]
    await update.message.reply_text(
        messages.OrderClosure,
        reply_markup=ReplyKeyboardMarkup(
            replyKeyboard, one_time_keyboard=True,
            resize_keyboard=True
        ),
    )
    return NextState

async def closeCallback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    logging.info("close callback invoked")
    logging.info(update.effective_user)
    logging.info(update.message.text)
    if update.message.text != "Yes":
        await update.message.reply_text(messages.OperationCanceled, reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END
    db.closeOrder()
    await update.message.reply_text(messages.OrderClosed, reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

closeHandler = ConversationHandler(
    entry_points=[CommandHandler("close", closeCommand)],
    states={
        NextState: [MessageHandler(filters.Regex("^(Yes|No)$"), closeCallback)]
    },
    fallbacks=[MessageHandler(filters.TEXT, cancelCommand)],
)

async def previewCommand(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logging.info("preview command received")
    logging.info(update.effective_user)
    if not hasAdminPrivileges(update.effective_user):
        await update.message.reply_text(messages.UnauthorizedAccess)
        return
    msg = '\n'.join([str(option.id) + ". " + option.description for option in db.preview()])
    msg = msg + '\n\n' + messages.PreviewDraft
    await update.message.reply_text(msg)

def generateList(items) -> str:
    msgs = []
    for item in items:
        msgs.append(item["option"].description + " Total: " + str(len(item["users"])))
        for user in item["users"]:
            foundUser = list(filter(lambda x: x["id"] == user.userid, users))[-1]
            msgs.append(foundUser["firstName"] + " " + foundUser["lastName"])
        msgs.append("")
    msg = '\n'.join(msgs)
    return msg

async def statusCommand(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logging.info("status command received")
    logging.info(update.effective_user)
    if not hasAdminPrivileges(update.effective_user):
        await update.message.reply_text(messages.UnauthorizedAccess)
        return
    msg = db.getNextDate().date.strftime("%a %b %d, %Y") + "\n" * 2 + generateList(db.status())
    await update.message.reply_text(msg)

async def reportCommand(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logging.info("report command received")
    logging.info(update.effective_user)
    if not hasAdminPrivileges(update.effective_user):
        await update.message.reply_text(messages.UnauthorizedAccess)
        return
    msg = db.getCurrentDate().date.strftime("%a %b %d, %Y") + "\n" * 2 + generateList(db.report())
    await update.message.reply_text(msg)

async def registerCommand(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    logging.info("register command received")
    logging.info(update.effective_user)
    await update.message.reply_text("Please provide your name or /cancel.")
    return NextState

async def registerCallback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    logging.info("register callback invoked")
    logging.info(update.effective_user)
    logging.info(update.message.text)
    with open("toRegister.txt", "a") as file:
        file.write(f"{update.message.text}, {update.effective_user}\n")
    await update.message.reply_text(f"""OK "{update.message.text}". """ + messages.RegisterMessage)
    await adminChat.message.reply_text(f"{update.effective_user}, {update.message.text}")
    return ConversationHandler.END

registerHandler = ConversationHandler(
    entry_points=[CommandHandler("register", registerCommand)],
    states={
        NextState: [CommandHandler("cancel", cancelCommand), MessageHandler(filters.TEXT, registerCallback)]
    },
    fallbacks=[MessageHandler(filters.TEXT, cancelCommand)],
)

def main() -> None:
    logging.basicConfig(filename='lunchbot.log', encoding='utf-8', level=logging.INFO)
    readUsers()
    application = Application.builder().token(readToken()).build()
    application.add_handler(CommandHandler("start", startCommand))
    application.add_handler(CommandHandler("help", helpCommand))
    application.add_handler(draftHandler)
    application.add_handler(addItemHandler)
    application.add_handler(publishHandler)
    application.add_handler(optionsHandler)
    application.add_handler(CommandHandler("mine", mineCommand))
    application.add_handler(closeHandler)
    application.add_handler(CommandHandler("preview", previewCommand))
    application.add_handler(CommandHandler("status", statusCommand))
    application.add_handler(CommandHandler("report", reportCommand))
    application.add_handler(registerHandler)
    application.run_polling()

if __name__ == "__main__":
    main()
