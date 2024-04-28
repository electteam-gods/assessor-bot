import logging

import requests
import random
import json

from aiogram import Bot, Dispatcher, F, Router, html
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    InlineKeyboardButton,
    KeyboardButton,
    ReplyKeyboardMarkup,
    Message,
    CallbackQuery,
    ReplyKeyboardRemove,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlmodel import Session, select, SQLModel

from model import engine, Course, Lesson
from callbacks import (
    SelectCourseCallbackFactory,
    SelectExamTypeCallbackFactor,
    SelectLessonCallbackFactor,
    BeginExamFactor,
)
from view_descriptor import ViewDescriptor


class Form(StatesGroup):
    select_course = State()
    select_exam_type = State()
    select_test = State()
    exam = State()


form_router = Router()


async def get_main_menu_kb():
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="Выбрать курс", callback_data="view_courses"))
    builder.row(
        InlineKeyboardButton(text="История ответов", callback_data="history"),
        InlineKeyboardButton(text="Сыграть в обучающую игру", callback_data="play"),
    )
    return builder


@form_router.callback_query(F.data == "history")
async def history(q: CallbackQuery) -> None:
    builder = InlineKeyboardBuilder()
    builder.button(text="Назад", callback_data="back_button")
    await q.message.edit_text(text="В разработке.", reply_markup=builder.as_markup())
    await q.answer()


@form_router.callback_query(F.data == "play")
async def history(q: CallbackQuery) -> None:
    builder = InlineKeyboardBuilder()
    builder.button(text="Назад", callback_data="back_button")
    await q.message.edit_text(text="В разработке.", reply_markup=builder.as_markup())
    await q.answer()


@form_router.message(CommandStart())
async def command_start(message: Message, state: FSMContext) -> None:
    # await state.set_state(Form.select_course)
    print("start")
    builder = await get_main_menu_kb()

    await message.answer(
        "Приветствую! Я – эксперт команды Electteam. В рамках взаимодействия со мной вы сможете проверить свои знания касательно пройденных курсов.",
        reply_markup=builder.as_markup(),
    )


class CheckResponse(SQLModel):
    questions: list[float]


@form_router.message(F.text == "Завершить тестирование")
async def complete_exam(message: Message, state: FSMContext) -> None:

    data = await state.get_data()

    for_check = {"url": data["lesson_url"], "questions": []}

    for q in data["responses"]:
        if "response" in q:
            for_check["questions"].append(
                {
                    "question": q["question"],
                    "context": q["context"],
                    "answer": q["response"],
                }
            )

    result = CheckResponse.model_validate(
        requests.post(
            "https://zina-eyes.ayarayarovich.ru/check",
            json=for_check,
        ).json()
    )

    avg_score = sum(result.questions) / len(result.questions)

    good_score_descripions = [
        "Отлично, что ты так хорошо подготовился к тесту!",
        "Ты невероятно быстро и правильно отвечал на вопросы!",
        "Изумительно, что ты смог справиться со всеми заданиями!",
        "Ты отлично справился с тестом!",
        "Ты невероятно внимателен, раз заметил все детали в вопросах!",
        "Ты отлично подготовился к тесту, это видно по твоим результатам!",
        "Ты невероятно уверен в своих ответах, это очень хорошо!",
    ]

    medium_score_descsriptions = [
        "Вам осталось совсем чуть-чуть поднажать, и вы достигнете идеального понимания материала!",
        "Вы уже ответили на половину вопросов теста правильно, вам осталось совсем немного, чтобы полностью разобраться в теме!",
        "Вы проделали большую работу, осталось совсем чуть-чуть, и вы сможете достичь идеального понимания материала и получить хороший результат!",
        "Вы уже так близки к идеальному пониманию материала, поднажмите ещё немного!",
        "Вы ответили на половину вопросов правильно, осталось совсем чуть-чуть до полного понимания темы!",
        "Вы уже на верном пути, поднажмите, и вас ждёт идеальное понимание материала и хороший результат!",
        "Не расстраивайтесь, что вы ответили только на половину вопросов. Используйте это как причину, чтобы стать лучше!",
    ]

    bad_score_descriptions = [
        "Ничего страшного, ошибки делают нас сильнее!",
        "Не расстраивайтесь, ошибки — это лишь часть обучения.",
        "Не стоит переживать, ошибки — это возможность для роста и развития.",
        "Ошибки — это не повод для расстройства, а возможность стать лучше.",
        "Не стоит расстраиваться, ошибки — это путь к успеху.",
        "Ошибки — это опыт, который делает нас сильнее и мудрее.",
        "Не бойтесь ошибок, они помогают нам становиться лучше.",
    ]

    tell = ""
    if 0 <= avg_score and avg_score < 0.4:
        tell = bad_score_descriptions[
            random.randint(0, len(bad_score_descriptions) - 1)
        ]
    elif 0.4 <= avg_score and avg_score < 0.6:
        tell = medium_score_descsriptions[
            random.randint(0, len(medium_score_descsriptions) - 1)
        ]
    elif 0.6 <= avg_score and avg_score <= 1:
        tell = good_score_descripions[
            random.randint(0, len(good_score_descripions) - 1)
        ]

    wrong_answers_indexes = []
    right_answers_count = 0
    for index, score in enumerate(result.questions):
        if score > 0.5:
            right_answers_count += 1
        else:
            wrong_answers_indexes.append(index)

    wrong_answers_feedback = "Допущенные ошибки:\n"
    for index, wai in enumerate(wrong_answers_indexes):
        r = data["responses"][wai]
        wrong_answers_feedback += f"{index + 1}. {r['question']}\n"

    feedback = f"""Общий результат: {right_answers_count} верных из {len(result.questions)} {"вопросов" if len(result.questions) > 1 else "вопроса"}.

{tell}

{wrong_answers_feedback if len(wrong_answers_indexes) > 0 else ""}
"""

    await state.clear()
    await message.answer(
        text=feedback,
        reply_markup=ReplyKeyboardRemove(),
    )
    builder = await get_main_menu_kb()
    await message.answer(
        text="Поздравляем с завершением тестирования!",
        reply_markup=builder.as_markup(),
    )


async def get_courses_kb():
    with Session(engine) as session:
        statement = select(Course)
        courses = session.exec(statement).fetchall()

    builder = InlineKeyboardBuilder()
    for c in courses:
        builder.button(
            text=c.title, callback_data=SelectCourseCallbackFactory(course_id=c.id)
        )
    builder.button(text="Назад", callback_data="back_button")
    builder.adjust(1)
    return builder


@form_router.callback_query(F.data == "view_courses")
async def view_courses(q: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(Form.select_course)
    print("view_courses", await state.get_data())

    builder = await get_courses_kb()
    await q.answer()
    await q.message.edit_text("Выберите курс:", reply_markup=builder.as_markup())


@form_router.callback_query(F.data == "back_button")
async def back_button(q: CallbackQuery, state: FSMContext) -> None:
    current_state = await state.get_state()
    print("back_button", await state.get_data())

    logging.info("Cancelling state %r", current_state)

    if current_state == Form.select_exam_type:
        builder = await get_courses_kb()
        await state.set_state(Form.select_course)
        await q.message.edit_text(
            text="Выберите курс:", reply_markup=builder.as_markup()
        )
    elif current_state == Form.select_test:
        builder = await get_exam_types_kb()
        await state.set_state(Form.select_exam_type)
        await q.message.edit_text(
            text="Выберите тип тестирования:", reply_markup=builder.as_markup()
        )
    else:
        builder = await get_main_menu_kb()
        await state.clear()
        await q.message.edit_text(
            text="Приветствую! Я - эксперт от компании Electteam. В рамках взаимодействия со мной вы сможете проверить свои знания касательно проденных вами курсов.",
            reply_markup=builder.as_markup(),
        )


async def get_exam_types_kb():
    builder = InlineKeyboardBuilder()

    builder.button(
        text="Лекция", callback_data=SelectExamTypeCallbackFactor(exam_type="lection")
    )
    builder.button(
        text="Практика",
        callback_data=SelectExamTypeCallbackFactor(exam_type="lesson"),
    )
    builder.button(
        text="Контрольные вопросы",
        callback_data=SelectExamTypeCallbackFactor(exam_type="control"),
    )
    builder.button(text="Назад", callback_data="back_button")
    builder.adjust(1)
    return builder


@form_router.callback_query(SelectCourseCallbackFactory.filter())
async def select_course_view_exam_types(
    q: CallbackQuery, callback_data: SelectCourseCallbackFactory, state: FSMContext
) -> None:
    await state.set_state(Form.select_exam_type)
    await state.set_data({"course_id": callback_data.course_id})

    builder = await get_exam_types_kb()

    await q.answer()
    await q.message.edit_text(
        text="Выберите тип тестирования:", reply_markup=builder.as_markup()
    )


async def get_select_test_view(course_id: int, type: str):
    with Session(engine) as session:
        statement = (
            select(Lesson)
            .where(Lesson.course_id == course_id)
            .where(Lesson.type == type)
        )
        lessons = session.exec(statement).fetchall()

    print(lessons)

    builder = InlineKeyboardBuilder()
    if len(lessons) == 0:
        builder.button(text="Назад", callback_data="back_button")
        builder.adjust(1)
        return ViewDescriptor(text="Тестов нет.", reply_markup=builder.as_markup())

    for l in lessons:
        builder.button(text=l.title, callback_data=BeginExamFactor(lesson_id=l.id))

    builder.button(
        text="По всем темам",
        callback_data=BeginExamFactor(lesson_id=-1),
    )
    builder.button(text="Назад", callback_data="back_button")
    builder.adjust(1)
    return ViewDescriptor(
        text="Выберите тему тестирования:", reply_markup=builder.as_markup()
    )


@form_router.callback_query(SelectExamTypeCallbackFactor.filter())
async def select_exam_type_view_tests(
    q: CallbackQuery, callback_data: SelectExamTypeCallbackFactor, state: FSMContext
) -> None:
    await state.set_state(Form.select_test)
    data = await state.get_data()
    await state.set_data(
        {"course_id": data["course_id"], "exam_type": callback_data.exam_type}
    )

    test_type = "lection" if callback_data.exam_type == "lection" else "lesson"
    descriptor = await get_select_test_view(course_id=data["course_id"], type=test_type)

    await q.message.edit_text(
        text=descriptor.text, reply_markup=descriptor.reply_markup
    )
    await q.answer()


class Question(SQLModel):
    question: str
    title: str
    context: str


class ManyQuestionsResponse(SQLModel):
    questions: list[Question]


@form_router.callback_query(BeginExamFactor.filter())
async def begin_exam(
    q: CallbackQuery, callback_data: BeginExamFactor, state: FSMContext
) -> None:
    await state.set_state(Form.exam)
    prev_data = await state.get_data()

    lesson_json_url = None

    print(callback_data)
    if callback_data.lesson_id > 0:
        with Session(engine) as session:
            stmt = select(Lesson).where(Lesson.id == callback_data.lesson_id).limit(1)
            lesson_json_url = session.exec(stmt).one().content
    else:
        exam_type = prev_data["exam_type"]
        with Session(engine) as session:
            stmt = select(Lesson).where(Lesson.type == exam_type)
            lessons = session.exec(stmt).all()
            lesson_json_url = lessons[random.randint(0, len(lessons) - 1)].content

    print("zapros uletel", lesson_json_url)

    questions = ManyQuestionsResponse.model_validate(
        requests.post(
            "https://zina-eyes.ayarayarovich.ru",
            params={"count": 1},
            json={"url": lesson_json_url},
        ).json()
    )
    print("zapros pruletel")

    await state.set_data(
        {
            **prev_data,
            "question_number": 1,
            "responses": [
                {
                    "question": questions.questions[0].question,
                    "title": questions.questions[0].title,
                    "context": questions.questions[0].context,
                }
            ],
            "lesson_url": lesson_json_url,
        }
    )

    print(await state.get_data())
    print(await state.get_state())

    await q.answer()
    qu = questions.questions[0]
    await q.message.edit_text(text=f"Раздел: {qu.title}\nВопрос: {qu.question}")
    print(await state.get_state())


@form_router.message(Form.exam)
async def receive_exam_response(message: Message, state: FSMContext) -> None:
    # save response to previos question
    data = await state.get_data()
    data["responses"][-1]["response"] = message.text
    await state.set_data(data)

    # generate next question
    questions = ManyQuestionsResponse.model_validate(
        requests.post(
            "https://zina-eyes.ayarayarovich.ru",
            params={"count": 1},
            json={"url": data["lesson_url"]},
        ).json()
    )

    q = questions.questions[0]

    data["question_number"] += 1
    data["responses"].append(
        {"question": q.question, "title": q.title, "context": q.context}
    )

    await state.set_data(data)

    print(await state.get_data())

    if data["question_number"] == 6:
        await message.answer(
            text="Вы уже ответили на 5 вопросов. Вы можете заврешить тестирование сейчас или тогда, когда захотите.",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text="Завершить тестирование")]],
                resize_keyboard=True,
            ),
        )

    await message.answer(text=f"Раздел: {q.title}\nВопрос: {q.question}")


@form_router.message(Command("cancel"))
@form_router.message(F.text.casefold() == "cancel")
async def cancel_handler(message: Message, state: FSMContext) -> None:
    """
    Allow user to cancel any action
    """
    current_state = await state.get_state()
    print("Cancelling suetate {current_state}")
    if current_state is None:
        return

    print("Cancelling state {current_state}")
    await state.clear()
    await message.answer(
        "Cancelled.",
        reply_markup=ReplyKeyboardRemove(),
    )
