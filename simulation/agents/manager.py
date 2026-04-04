"""Linda Torres — Manager. Administrative requests on a monthly/quarterly cycle."""

from simulation.agents.base import BaseAgent, SimMessage, SimState
from simulation.clock import SimWeek


class LindaTorresAgent(BaseAgent):

    def __init__(self):
        super().__init__("linda")

    def generate_messages(self, week: SimWeek, state: SimState) -> list[SimMessage]:
        w = week.week_number
        msgs: list[SimMessage] = []

        # --- Q1 ---
        if w == 2:
            msgs.append(self._make_message(week,
                text=(
                    "Hi,\n\nHappy New Year! Quick reminder that Q1 timesheets are due by "
                    "January 16th. Please submit yours through the portal and confirm with me "
                    "once done. Also, please send me your Q1 goals document by January 23rd.\n\n"
                    "Thanks,\nLinda"
                ),
                extraction=self._extraction(
                    people=[self._person("Linda Torres", "ltorres@company.com", "Manager")],
                    tasks=[
                        self._task("Submit Q1 timesheet", assignee="You", due_date="2026-01-16", priority="medium"),
                        self._task("Submit Q1 goals document", assignee="You", due_date="2026-01-23", priority="medium"),
                    ],
                    summary="Linda requests Q1 timesheet and goals document submission.",
                ),
            ))

        if w == 5:
            msgs.append(self._make_message(week,
                text=(
                    "Hi,\n\nI'm scheduling Q1 performance check-ins for the last week of February. "
                    "Please prepare a brief self-assessment covering your Q4 accomplishments and "
                    "Q1 trajectory. Send it to me by February 20th so I can review before our meeting.\n\n"
                    "Linda"
                ),
                extraction=self._extraction(
                    people=[self._person("Linda Torres")],
                    tasks=[
                        self._task("Prepare Q1 self-assessment", assignee="You", due_date="2026-02-20", priority="medium"),
                    ],
                    summary="Linda scheduling Q1 performance check-ins, requests self-assessment.",
                ),
            ))

        if w == 8:
            msgs.append(self._make_message(week,
                text=(
                    "REMINDER: Mandatory security awareness training must be completed by March 6th. "
                    "This is a compliance requirement — no exceptions. Please complete the module on "
                    "the LMS portal and forward me the completion certificate.\n\nLinda"
                ),
                extraction=self._extraction(
                    people=[self._person("Linda Torres")],
                    tasks=[
                        self._task("Complete mandatory security training", assignee="You",
                                   due_date="2026-03-06", priority="high"),
                    ],
                    summary="Mandatory security training due March 6th, compliance requirement.",
                ),
            ))

        # --- Q2 ---
        if w == 13:
            msgs.append(self._make_message(week,
                text=(
                    "Hi,\n\nQ1 is wrapping up. I need your project spend estimates for the Q1 budget "
                    "reconciliation. Please break down hours by project (Phoenix and EPA) and send me "
                    "the numbers by April 10th. Also, any outstanding PTO requests for Q2 should be "
                    "submitted this week.\n\nThanks,\nLinda"
                ),
                extraction=self._extraction(
                    people=[self._person("Linda Torres")],
                    projects=[
                        self._project("Project Phoenix"),
                        self._project("EPA Data Modernization"),
                    ],
                    tasks=[
                        self._task("Submit Q1 project spend estimates", assignee="You",
                                   due_date="2026-04-10", priority="medium"),
                        self._task("Submit Q2 PTO requests", assignee="You",
                                   due_date="2026-04-03", priority="low"),
                    ],
                    summary="Q1 budget reconciliation and Q2 PTO planning.",
                ),
            ))

        if w == 18:
            msgs.append(self._make_message(week,
                text=(
                    "Hi,\n\nI noticed you haven't completed the security training yet. This was due "
                    "March 6th. I've escalated to HR as required by policy. Please complete it by end "
                    "of this week — May 1st at the latest — or it goes to the VP.\n\nLinda"
                ),
                extraction=self._extraction(
                    people=[self._person("Linda Torres")],
                    tasks=[
                        self._task("Complete mandatory security training", assignee="You",
                                   due_date="2026-05-01", priority="critical"),
                    ],
                    summary="Escalation: security training overdue, must complete by May 1.",
                ),
            ))

        if w == 22:
            msgs.append(self._make_message(week,
                text=(
                    "Hi team,\n\nMid-year performance reviews are coming up in July. Please start "
                    "documenting your accomplishments for H1. I'll need your mid-year self-review "
                    "submitted by June 26th. Also, if any of your direct reports need feedback from me, "
                    "let me know.\n\nLinda"
                ),
                extraction=self._extraction(
                    people=[self._person("Linda Torres")],
                    tasks=[
                        self._task("Submit mid-year self-review", assignee="You",
                                   due_date="2026-06-26", priority="medium"),
                        self._task("Collect direct report feedback for mid-year reviews",
                                   assignee="You", due_date="2026-06-26", priority="medium"),
                    ],
                    summary="Mid-year performance review prep, self-review due June 26.",
                ),
            ))

        # --- Q3 ---
        if w == 27:
            msgs.append(self._make_message(week,
                text=(
                    "Hi,\n\nQ2 budget close is happening this week. Please send me final actuals for "
                    "both Phoenix and EPA by July 10th. Include any contractor costs and tool licenses.\n\n"
                    "Also, please confirm your team's on-call rotation for August — I need it for the "
                    "department staffing plan.\n\nLinda"
                ),
                extraction=self._extraction(
                    people=[self._person("Linda Torres")],
                    projects=[self._project("Project Phoenix"), self._project("EPA Data Modernization")],
                    tasks=[
                        self._task("Submit Q2 budget actuals", assignee="You",
                                   due_date="2026-07-10", priority="medium"),
                        self._task("Confirm August on-call rotation", assignee="You",
                                   due_date="2026-07-10", priority="low"),
                    ],
                    summary="Q2 budget close and August on-call rotation needed.",
                ),
            ))

        if w == 31:
            msgs.append(self._make_message(week,
                text=(
                    "Reminder: Annual leave planning for Q4. If anyone on your team wants to take "
                    "extended PTO in November or December, I need requests submitted by August 15th "
                    "to ensure coverage.\n\nLinda"
                ),
                extraction=self._extraction(
                    people=[self._person("Linda Torres")],
                    tasks=[
                        self._task("Submit team Q4 leave requests", assignee="You",
                                   due_date="2026-08-15", priority="low"),
                    ],
                    summary="Q4 annual leave planning deadline August 15.",
                ),
            ))

        if w == 36:
            msgs.append(self._make_message(week,
                text=(
                    "Hi,\n\nQ3 performance check-ins are next week. Please have your self-assessment "
                    "ready by September 11th. Also include peer feedback on Sarah, Marcus, and Priya "
                    "since you work closely with them.\n\nLinda"
                ),
                extraction=self._extraction(
                    people=[
                        self._person("Linda Torres"),
                        self._person("Sarah Chen"),
                        self._person("Marcus Webb"),
                        self._person("Priya Patel"),
                    ],
                    tasks=[
                        self._task("Prepare Q3 self-assessment", assignee="You",
                                   due_date="2026-09-11", priority="medium"),
                        self._task("Write peer feedback for Sarah, Marcus, Priya",
                                   assignee="You", due_date="2026-09-11", priority="medium"),
                    ],
                    summary="Q3 performance reviews, self-assessment and peer feedback due Sep 11.",
                ),
            ))

        # --- Q4 ---
        if w == 40:
            msgs.append(self._make_message(week,
                text=(
                    "Hi,\n\nTime to start Q4 planning. I need your team's headcount and resource needs "
                    "for 2027 by October 16th. Please also include any tooling or infrastructure budget "
                    "requests. This feeds into the department's annual plan.\n\nLinda"
                ),
                extraction=self._extraction(
                    people=[self._person("Linda Torres")],
                    tasks=[
                        self._task("Submit 2027 headcount and resource plan", assignee="You",
                                   due_date="2026-10-16", priority="high"),
                        self._task("Submit 2027 tooling budget request", assignee="You",
                                   due_date="2026-10-16", priority="medium"),
                    ],
                    summary="Q4 planning: 2027 headcount, resources, and tooling budget due Oct 16.",
                ),
            ))

        if w == 44:
            msgs.append(self._make_message(week,
                text=(
                    "Reminder: Open enrollment for benefits ends November 13th. Please review your "
                    "selections and make any changes in the HR portal. Also, please remind your "
                    "direct reports.\n\nLinda"
                ),
                extraction=self._extraction(
                    people=[self._person("Linda Torres")],
                    tasks=[
                        self._task("Complete benefits open enrollment", assignee="You",
                                   due_date="2026-11-13", priority="medium"),
                    ],
                    summary="Benefits open enrollment deadline November 13.",
                ),
            ))

        if w == 48:
            msgs.append(self._make_message(week,
                text=(
                    "Hi,\n\nYear-end reviews are in two weeks. Please prepare your annual "
                    "accomplishments summary and submit it by December 11th. I'll also need "
                    "you to write formal reviews for Marcus and Priya as their direct manager.\n\n"
                    "Thanks for a great year,\nLinda"
                ),
                extraction=self._extraction(
                    people=[
                        self._person("Linda Torres"),
                        self._person("Marcus Webb"),
                        self._person("Priya Patel"),
                    ],
                    tasks=[
                        self._task("Submit annual accomplishments summary", assignee="You",
                                   due_date="2026-12-11", priority="high"),
                        self._task("Write annual reviews for Marcus and Priya", assignee="You",
                                   due_date="2026-12-11", priority="high"),
                    ],
                    summary="Year-end reviews: accomplishments summary and direct report reviews due Dec 11.",
                ),
            ))

        # --- Recurring: monthly status check (non-quarterly months) ---
        if w in (10, 15, 19, 24, 29, 33, 38, 42, 46, 50):
            msgs.append(self._make_message(week,
                text=(
                    f"Hi,\n\nJust a quick monthly check-in. How are things going with your team? "
                    f"Any blockers I should know about? Any concerns about workload or morale?\n\n"
                    f"Let me know if you need anything from me.\n\nLinda"
                ),
                extraction=self._extraction(
                    people=[self._person("Linda Torres")],
                    tasks=[
                        self._task("Reply to Linda's monthly check-in", assignee="You",
                                   priority="low"),
                    ],
                    summary=f"Linda's monthly check-in asking about team status (W{w}).",
                ),
            ))

        return msgs
