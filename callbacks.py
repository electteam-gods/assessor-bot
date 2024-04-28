from aiogram.filters.callback_data import CallbackData


class SelectCourseCallbackFactory(CallbackData, prefix="select_course_data"):
    course_id: int


class SelectExamTypeCallbackFactor(CallbackData, prefix="select_exam_type_data"):
    exam_type: str


class SelectLessonCallbackFactor(CallbackData, prefix="select_lesson_data"):
    lesson_id: int


class BeginExamFactor(CallbackData, prefix="begin_exam_data"):
    lesson_id: int
