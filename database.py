import os
from datetime import (
    datetime,
    date
)
from typing import (
    List,
    Optional
)
from sqlmodel import (
    Field,
    Relationship,
    Session,
    SQLModel,
    col,
    create_engine,
    select
)

class MenuOption(SQLModel, table=True):
	id: Optional[int] = Field(default=None, primary_key=True)
	description: str
	users: List["UserChoice"] = Relationship(back_populates="choice")

class UserChoice(SQLModel, table=True):
	id: Optional[int] = Field(default=None, primary_key=True)
	userid: int = Field(unique=True)
	choiceKey: Optional[int] = Field(default=None, foreign_key="menuoption.id")
	choice: Optional["MenuOption"] = Relationship(back_populates="users")

class Date(SQLModel, table=True):
	id: Optional[int] = Field(default=None, primary_key=True)
	date: date

draftEngine = None
nextEngine = None
currentEngine = None

def initializeDraftEngine():
	global draftEngine
	draftEngine = create_engine(f"sqlite:///draft.db")
	SQLModel.metadata.create_all(draftEngine)

def initializeNextEngine():
	global nextEngine
	nextEngine = create_engine(f"sqlite:///next.db")
	SQLModel.metadata.create_all(nextEngine)

def initializeCurrentEngine():
	global currentEngine
	currentEngine = create_engine(f"sqlite:///current.db")
	SQLModel.metadata.create_all(currentEngine)

def createDraft(menuDate:date):
	if os.path.exists("draft.db"):
		os.remove("draft.db")
	initializeDraftEngine()
	with Session(draftEngine) as session:
		session.add(Date(date = menuDate))
		session.commit()

def preview():
	if not draftEngine:
		initializeDraftEngine()
	with Session(draftEngine) as session:
		return session.exec(
			select(MenuOption)
		).all()

def publish():
	global draftEngine
	global nextEngine
	draftEngine, nextEngine = None, None
	if os.path.exists("next.db"):
		os.rename(src="next.db", dst="next_" + datetime.now().strftime("%Y%m%d_%H.%M.%S.%f") + ".db")
	if os.path.exists("draft.db"):
		os.rename(src="draft.db", dst="next.db")
	initializeNextEngine()

def closeOrder():
	global nextEngine
	global currentEngine
	nextEngine, currentEngine = None, None
	if os.path.exists("current.db"):
		os.rename(src="current.db", dst="current_" + datetime.now().strftime("%Y%m%d_%H.%M.%S.%f") + ".db")
	if os.path.exists("next.db"):
		os.rename(src="next.db", dst="current.db")
	initializeCurrentEngine()

def status():
	if not nextEngine:
		initializeNextEngine()
	with Session(nextEngine) as session:
		options = session.exec(
			select(MenuOption)
		).all()
		return [{"option": option, "users": option.users} for option in options]

def report():
	if not currentEngine:
		initializeCurrentEngine()
	with Session(currentEngine) as session:
		options = session.exec(
			select(MenuOption)
		).all()
		return [{"option": option, "users": option.users} for option in options]
	

def addMenuOption(description_:str):
	with Session(draftEngine) as session:
		session.add(
			MenuOption(
				description = description_
			)
		)
		session.commit()

def getNextDate():
	if not nextEngine:
		initializeNextEngine()
	with Session(nextEngine) as session:
		return session.exec(
			select(Date)
		).first()
	
def getCurrentDate():
	if not currentEngine:
		initializeCurrentEngine()
	with Session(currentEngine) as session:
		return session.exec(
			select(Date)
		).first()

def getMenuOptions() -> List[MenuOption]:
	if not nextEngine:
		initializeNextEngine()
	with Session(nextEngine) as session:
		return session.exec(
			select(MenuOption)
		).all()

def updateUserChoice(idOfUser:int, idOfChoice:Optional[int]):
	if not nextEngine:
		initializeNextEngine()
	with Session(nextEngine) as session:
		userChoice = session.exec(
			select(UserChoice).where(col(UserChoice.userid) == idOfUser)
		).first()
		if not userChoice:
			session.add(
				UserChoice(
					userid = idOfUser,
					choiceKey = idOfChoice
				)
			)
		else:
			userChoice.choiceKey = idOfChoice
			session.add(userChoice)
		session.commit()

def getUserChoice(idOfUser:str):
	currentDate = currentChoice = nextDate = nextChoice = None
	if not nextEngine:
		initializeNextEngine()
	if not currentEngine:
		initializeCurrentEngine()
	with Session(currentEngine) as session:
		currentDate = session.exec(
			select(Date)
		).first()
		currentChoiceId = session.exec(
			select(UserChoice.choiceKey).where(col(UserChoice.userid) == idOfUser)
		).first()
		if currentChoiceId:
			currentChoice = session.exec(
				select(MenuOption).where(col(MenuOption.id) == currentChoiceId)
			).first()
	with Session(nextEngine) as session:
		nextDate = session.exec(
			select(Date)
		).first()
		nextChoiceId = session.exec(
			select(UserChoice.choiceKey).where(col(UserChoice.userid) == idOfUser)
		).first()
		if nextChoiceId:
			nextChoice = session.exec(
				select(MenuOption).where(col(MenuOption.id) == nextChoiceId)
			).first()
	return [currentDate, currentChoice, nextDate, nextChoice]
