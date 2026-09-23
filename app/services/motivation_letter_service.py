"""Template-based motivation and university inquiry letter generation."""

from textwrap import dedent

from app.models import University, User


def build_university_letter(
    *,
    user: User,
    university: University,
    program_name: str,
    degree: str | None = None,
    applicant_message: str | None = None,
    achievements: str | None = None,
) -> tuple[str, str]:
    """Build a copy-ready English email without sending it anywhere."""
    subject = f"Inquiry about admission to {program_name}"
    degree_phrase = f" as a {degree} student" if degree else ""
    message = applicant_message or (
        "I am especially interested in learning more about the program structure "
        "and the opportunities available to students."
    )
    achievements_line = (
        f"My relevant background and achievements: {achievements}" if achievements else ""
    )
    body = dedent(
        f"""\
        Dear Admissions Office of {university.name},

        My name is {user.username}, and I am interested in applying to the {program_name} program{degree_phrase}.

        I would be grateful if you could provide information about the admission requirements, application deadlines, tuition fees, available scholarships, and the documents required for international applicants.

        {message}

        {achievements_line}

        Thank you for your time. I look forward to your reply.

        Kind regards,
        {user.username}
        {user.email}
        """
    ).strip()
    return subject, body
