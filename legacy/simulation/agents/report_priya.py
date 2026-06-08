"""Priya Patel — Mid-level Developer. Architecture, PRs, EPA lead, career mentoring."""

from models.schemas import Platform
from simulation.agents.base import BaseAgent, SimMessage, SimState
from simulation.clock import SimWeek

PHOENIX = "Project Phoenix"
EPA = "EPA Data Modernization"


class PriyaPatelAgent(BaseAgent):

    def __init__(self):
        super().__init__("priya")

    def generate_messages(self, week: SimWeek, state: SimState) -> list[SimMessage]:
        w = week.week_number
        msgs: list[SimMessage] = []

        # === Q1: EPA architecture + Phoenix event pipeline ===

        if w == 3:
            msgs.append(self._make_message(week,
                text=(
                    "Hi,\n\nI've drafted the architecture proposal for EPA Data Modernization. "
                    "It uses an event-driven pipeline with Apache Airflow for orchestration and "
                    "a staging Postgres instance for data validation before loading to production.\n\n"
                    "Key decision point: should we use Airflow or Prefect? Airflow has better "
                    "enterprise support but Prefect is simpler. I'm leaning Airflow given the "
                    "government compliance requirements.\n\n"
                    "Doc is in Confluence — can you review by Friday?\n\nPriya"
                ),
                extraction=self._extraction(
                    people=[self._person("Priya Patel", "ppatel@company.com", "Mid-level Developer")],
                    projects=[self._project(EPA, priority="high")],
                    tasks=[
                        self._task("Review Priya's EPA architecture proposal", assignee="You",
                                   due_date="2026-01-23", priority="high", project=EPA),
                    ],
                    summary="Priya's EPA architecture proposal ready for review. Airflow vs Prefect decision.",
                ),
            ))

        if w == 5:
            msgs.append(self._make_message(week, platform=Platform.SLACK,
                text=(
                    "Thanks for the architecture feedback. Going with Airflow + the validation "
                    "layer approach you suggested. Starting implementation this week."
                ),
                extraction=self._extraction(
                    people=[self._person("Priya Patel")],
                    projects=[self._project(EPA)],
                    summary="Priya proceeding with Airflow for EPA, incorporating review feedback.",
                ),
                resolves_tasks=["Review Priya's EPA architecture proposal"],
            ))

        if w == 7:
            msgs.append(self._make_message(week,
                text=(
                    "EPA Airflow DAG structure is in PR #82. I've set up:\n"
                    "- extract_legacy_data DAG (daily)\n"
                    "- validate_and_stage DAG (daily, depends on extract)\n"
                    "- load_to_production DAG (weekly, manual trigger)\n\n"
                    "The audit trail logging meets the compliance spec — every record transformation "
                    "is tracked. Can you review the DAG design?\n\nPriya"
                ),
                extraction=self._extraction(
                    people=[self._person("Priya Patel")],
                    projects=[self._project(EPA)],
                    tasks=[
                        self._task("Review Priya's EPA Airflow DAGs PR #82", assignee="You",
                                   priority="high", project=EPA),
                    ],
                    summary="Priya's EPA Airflow DAG structure ready for review with compliance logging.",
                ),
            ))

        # === Q1-Q2: EPA build + Phoenix event pipeline ===

        if w == 10:
            msgs.append(self._make_message(week, platform=Platform.SLACK,
                text=(
                    "Hit an issue with EPA — the legacy database has inconsistent encoding. Some "
                    "tables are Latin-1, others are UTF-8. The Airflow tasks are choking on the "
                    "mixed encoding. Working on a fix but wanted to flag it."
                ),
                extraction=self._extraction(
                    people=[self._person("Priya Patel")],
                    projects=[self._project(EPA)],
                    tasks=[
                        self._task("Fix EPA legacy database encoding issues", assignee="Priya Patel",
                                   priority="high", project=EPA),
                    ],
                    summary="EPA encoding issue — mixed Latin-1/UTF-8 in legacy tables causing failures.",
                ),
            ))

        if w == 12:
            msgs.append(self._make_message(week,
                text=(
                    "Encoding fix is merged. I added a detection step that sniffs the encoding "
                    "per-table before extraction. PR #109.\n\n"
                    "Separately — Robert mentioned I'll be picking up the Phoenix event pipeline "
                    "after Sarah's data layer handoff. Can we do a quick architecture review before "
                    "I start? I have some questions about the event schema.\n\nPriya"
                ),
                extraction=self._extraction(
                    people=[self._person("Priya Patel"), self._person("Sarah Chen")],
                    projects=[self._project(PHOENIX), self._project(EPA)],
                    tasks=[
                        self._task("Architecture review for Phoenix event pipeline with Priya",
                                   assignee="You", priority="medium", project=PHOENIX),
                    ],
                    summary="Priya fixed EPA encoding. Wants Phoenix event pipeline arch review.",
                ),
                resolves_tasks=["Fix EPA legacy database encoding issues"],
            ))

        if w == 16:
            msgs.append(self._make_message(week,
                text=(
                    "Career check-in: I've been thinking about my growth path. I feel solid on "
                    "backend systems but want to develop more on system design and technical "
                    "leadership. Could we schedule a 1:1 to discuss? Maybe next week?\n\n"
                    "Also, would it be possible for me to lead the next design review? I think "
                    "presenting the Phoenix event pipeline design would be good practice.\n\nPriya"
                ),
                extraction=self._extraction(
                    people=[self._person("Priya Patel")],
                    tasks=[
                        self._task("Schedule career 1:1 with Priya", assignee="You",
                                   priority="medium"),
                        self._task("Let Priya lead Phoenix event pipeline design review",
                                   assignee="You", priority="low", project=PHOENIX),
                    ],
                    summary="Priya requesting career mentoring 1:1 and design review leadership opportunity.",
                ),
            ))

        if w == 20:
            msgs.append(self._make_message(week,
                text=(
                    "Phoenix event pipeline is feature-complete. PR #141. Key components:\n"
                    "- Event producer service (publishes to Kafka)\n"
                    "- Consumer service (writes to the data layer Sarah built)\n"
                    "- Dead letter queue for failed events\n"
                    "- Monitoring dashboard with lag alerts\n\n"
                    "Sarah helped me with the data layer integration — her docs were great. "
                    "Ready for your review.\n\nPriya"
                ),
                extraction=self._extraction(
                    people=[self._person("Priya Patel"), self._person("Sarah Chen")],
                    projects=[self._project(PHOENIX)],
                    tasks=[
                        self._task("Review Priya's Phoenix event pipeline PR #141", assignee="You",
                                   priority="high", project=PHOENIX),
                    ],
                    summary="Priya's Phoenix event pipeline complete with Kafka, DLQ, monitoring.",
                ),
                resolves_tasks=["Finish Phoenix event pipeline"],
            ))

        # === Q3: EPA testing + Phoenix UAT ===

        if w == 23:
            msgs.append(self._make_message(week, platform=Platform.SLACK,
                text=(
                    "Starting EPA test dataset validation. The EPA sent 3 test files — I'm "
                    "running them through the pipeline now. Initial results look good but file #3 "
                    "has some edge cases with missing county codes. Working through them."
                ),
                extraction=self._extraction(
                    people=[self._person("Priya Patel")],
                    projects=[self._project(EPA)],
                    summary="Priya running EPA test datasets, found edge cases in file #3.",
                ),
            ))

        if w == 26:
            msgs.append(self._make_message(week,
                text=(
                    "EPA test validation is complete. All 3 test files pass. I documented the "
                    "edge cases and their resolutions in the test report.\n\n"
                    "Data reconciliation numbers:\n"
                    "- File 1: 12,847 records, 100% match\n"
                    "- File 2: 8,923 records, 99.97% match (3 records had encoding issues, fixed)\n"
                    "- File 3: 15,201 records, 100% match after county code fixes\n\n"
                    "Ready for the staging deployment whenever you are.\n\nPriya"
                ),
                extraction=self._extraction(
                    people=[self._person("Priya Patel")],
                    projects=[self._project(EPA)],
                    summary="EPA test validation complete. All files pass. Ready for staging.",
                ),
                resolves_tasks=["Run EPA test dataset validation"],
            ))

        if w == 31:
            msgs.append(self._make_message(week, platform=Platform.SLACK,
                text=(
                    "EPA staging deployment looks good. I've been monitoring for 3 days — no "
                    "failures, data reconciliation checks pass. I'm confident we're ready for "
                    "the production deployment on Aug 7."
                ),
                extraction=self._extraction(
                    people=[self._person("Priya Patel")],
                    projects=[self._project(EPA)],
                    summary="EPA staging stable for 3 days, Priya confident for production deployment.",
                ),
            ))

        if w == 34:
            msgs.append(self._make_message(week,
                text=(
                    "Phoenix event pipeline has been stable through UAT. No issues with the "
                    "Kafka consumers. Lag is consistently under 200ms. I'd say the event pipeline "
                    "is production-ready.\n\n"
                    "One suggestion: we should add a circuit breaker pattern before go-live. "
                    "I can implement it this week if you approve. It'd protect against the data "
                    "layer going down and flooding the DLQ.\n\nPriya"
                ),
                extraction=self._extraction(
                    people=[self._person("Priya Patel")],
                    projects=[self._project(PHOENIX)],
                    tasks=[
                        self._task("Approve circuit breaker for Phoenix event pipeline",
                                   assignee="You", priority="high", project=PHOENIX),
                        self._task("Implement Phoenix event pipeline circuit breaker",
                                   assignee="Priya Patel", priority="high", project=PHOENIX,
                                   waiting_on="You"),
                    ],
                    summary="Priya proposes circuit breaker for Phoenix event pipeline before go-live.",
                ),
            ))

        # === Q4: Post-launch + career growth ===

        if w == 37:
            msgs.append(self._make_message(week, platform=Platform.SLACK,
                text=(
                    "Circuit breaker saved us during the rate-limit incident! The DLQ would've "
                    "overflowed without it. Glad we added it. I'll include this in the post-mortem."
                ),
                extraction=self._extraction(
                    people=[self._person("Priya Patel")],
                    projects=[self._project(PHOENIX)],
                    summary="Phoenix circuit breaker proved critical during rate-limit incident.",
                ),
                resolves_tasks=["Implement Phoenix event pipeline circuit breaker"],
            ))

        if w == 41:
            msgs.append(self._make_message(week,
                text=(
                    "Hi,\n\nWith EPA and Phoenix in maintenance, I'd like to discuss my next steps. "
                    "A few things on my mind:\n"
                    "1. I'd like to be considered for the tech lead track\n"
                    "2. Should I get the AWS Solutions Architect certification? Company will cover it\n"
                    "3. Any upcoming projects I could lead from the start?\n\n"
                    "Can we schedule a 1:1 this week?\n\nPriya"
                ),
                extraction=self._extraction(
                    people=[self._person("Priya Patel")],
                    tasks=[
                        self._task("Schedule career growth 1:1 with Priya", assignee="You",
                                   priority="medium"),
                    ],
                    summary="Priya requesting career discussion: tech lead track, AWS cert, project leadership.",
                ),
            ))

        if w == 49:
            msgs.append(self._make_message(week,
                text=(
                    "Thanks for the year-end feedback. I really appreciate the mentoring this year. "
                    "Leading the EPA implementation was a huge growth experience. Looking forward to "
                    "taking on more in 2027.\n\nHappy holidays!\nPriya"
                ),
                extraction=self._extraction(
                    people=[self._person("Priya Patel")],
                    summary="Priya year-end thanks, positive about EPA leadership experience.",
                ),
            ))

        # === Recurring: weekly updates (Mondays) ===
        if w in (4, 8, 11, 14, 18, 22, 25, 28, 30, 33, 36, 39, 43, 47):
            focus = "EPA pipeline" if w < 26 else "maintenance and monitoring"
            msgs.append(self._make_message(week, platform=Platform.SLACK, weekday=0, hour=9,
                text=f"Weekly update: heads-down on {focus}. No blockers. Let me know if priorities shift.",
                extraction=self._extraction(
                    people=[self._person("Priya Patel")],
                    summary=f"Priya weekly update, focused on {focus} (W{w}).",
                ),
            ))

        return msgs
