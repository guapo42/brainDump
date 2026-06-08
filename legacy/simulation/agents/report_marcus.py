"""Marcus Webb — Junior Developer. Code reviews, help requests, and idle work asks."""

from models.schemas import Platform
from simulation.agents.base import BaseAgent, SimMessage, SimState
from simulation.clock import SimWeek

PHOENIX = "Project Phoenix"
EPA = "EPA Data Modernization"


class MarcusWebbAgent(BaseAgent):

    def __init__(self):
        super().__init__("marcus")

    def generate_messages(self, week: SimWeek, state: SimState) -> list[SimMessage]:
        w = week.week_number
        msgs: list[SimMessage] = []

        # === Q1: Ramping up, learning the codebase ===

        if w == 3:
            msgs.append(self._make_message(week,
                text="Hey, I just got added to Phoenix. Where should I start? Is there a getting-started guide or should I just read the design doc?",
                extraction=self._extraction(
                    people=[self._person("Marcus Webb", "mwebb@company.com", "Junior Developer")],
                    projects=[self._project(PHOENIX)],
                    tasks=[
                        self._task("Onboard Marcus to Project Phoenix", assignee="You",
                                   priority="medium", project=PHOENIX),
                    ],
                    summary="Marcus asking for Phoenix onboarding guidance.",
                ),
            ))

        if w == 4:
            msgs.append(self._make_message(week,
                text="I started reading the design doc. Quick question — are we using SQLAlchemy or raw SQL for the data layer? I want to set up my local dev environment correctly.",
                extraction=self._extraction(
                    people=[self._person("Marcus Webb")],
                    projects=[self._project(PHOENIX)],
                    tasks=[
                        self._task("Answer Marcus's Phoenix tech stack question", assignee="You",
                                   priority="low", project=PHOENIX),
                    ],
                    summary="Marcus asking about Phoenix ORM choice for local dev setup.",
                ),
            ))

        if w == 6:
            msgs.append(self._make_message(week,
                text="PR #78 is ready for review — it's the initial test scaffolding for the Phoenix API endpoints. I followed the patterns from the design doc. Let me know if the test structure looks right.",
                extraction=self._extraction(
                    people=[self._person("Marcus Webb")],
                    projects=[self._project(PHOENIX)],
                    tasks=[
                        self._task("Review Marcus's Phoenix test scaffolding PR #78",
                                   assignee="You", priority="medium", project=PHOENIX),
                    ],
                    summary="Marcus's Phoenix API test scaffolding ready for review in PR #78.",
                ),
            ))

        # === Q1-Q2: Building momentum ===

        if w == 9:
            msgs.append(self._make_message(week,
                text="I'm blocked on the unit tests — I can't figure out how to mock the Neo4j connection in the test environment. The fixture keeps timing out. Can we pair on this for 30 min?",
                extraction=self._extraction(
                    people=[self._person("Marcus Webb")],
                    projects=[self._project(PHOENIX)],
                    tasks=[
                        self._task("Help Marcus with Neo4j test mocking", assignee="You",
                                   priority="high", project=PHOENIX),
                    ],
                    summary="Marcus stuck on Neo4j test mocking, wants to pair.",
                ),
            ))

        if w == 11:
            msgs.append(self._make_message(week,
                text="Fixed the Neo4j mocking issue — thanks for the help! All unit tests are green now. PR #95 has the full test suite for the CRUD endpoints. Ready for review whenever you have time.",
                extraction=self._extraction(
                    people=[self._person("Marcus Webb")],
                    projects=[self._project(PHOENIX)],
                    tasks=[
                        self._task("Review Marcus's CRUD endpoint tests PR #95",
                                   assignee="You", priority="medium", project=PHOENIX),
                    ],
                    summary="Marcus fixed Neo4j mocking, CRUD test suite ready for review.",
                ),
                resolves_tasks=["Help Marcus with Neo4j test mocking"],
            ))

        if w == 13:
            msgs.append(self._make_message(week,
                text="Milestone 1 unit tests are done! 94% coverage on the API layer. Anything else you need from me before the M1 deadline Friday?",
                extraction=self._extraction(
                    people=[self._person("Marcus Webb")],
                    projects=[self._project(PHOENIX)],
                    summary="Marcus completed M1 unit tests at 94% coverage, asking for more work.",
                ),
                resolves_tasks=["Complete Phoenix API unit tests"],
            ))

        # === Q2: Crunch + EPA work ===

        if w == 15:
            msgs.append(self._make_message(week,
                text="I finished my M1 tasks. What should I pick up next? I saw the EPA extraction scripts are on the board but I'm waiting on the schema from you. Is that close?",
                extraction=self._extraction(
                    people=[self._person("Marcus Webb")],
                    projects=[self._project(EPA)],
                    tasks=[
                        self._task("Assign next tasks to Marcus", assignee="You",
                                   priority="medium"),
                    ],
                    summary="Marcus idle after M1, waiting on EPA schema to start extraction scripts.",
                ),
            ))

        if w == 17:
            msgs.append(self._make_message(week,
                text="Got the schema — thanks! Starting on the EPA extraction scripts now. Quick question: the legacy data has some records with null date fields. Should I skip those rows or default to epoch? Want to get it right the first time.",
                extraction=self._extraction(
                    people=[self._person("Marcus Webb")],
                    projects=[self._project(EPA)],
                    tasks=[
                        self._task("Clarify EPA null date handling strategy", assignee="You",
                                   priority="medium", project=EPA),
                    ],
                    summary="Marcus starting EPA extraction, asking about null date handling.",
                ),
            ))

        if w == 19:
            msgs.append(self._make_message(week,
                text="EPA extraction scripts are in PR #134. Handles all 4 legacy formats including the weird fixed-width ones from 2003. Also added the null date handling per your guidance. Ready for review.",
                extraction=self._extraction(
                    people=[self._person("Marcus Webb")],
                    projects=[self._project(EPA)],
                    tasks=[
                        self._task("Review Marcus's EPA extraction scripts PR #134",
                                   assignee="You", priority="high", project=EPA),
                    ],
                    summary="Marcus's EPA extraction scripts ready for review, handles all legacy formats.",
                ),
                resolves_tasks=["Write EPA legacy data extraction scripts"],
            ))

        if w == 21:
            msgs.append(self._make_message(week,
                text="The ETL pipeline is failing on null dates in the 2019 dataset — Priya and I are debugging it. I think the issue is in the type casting step. I'll have a fix PR up by tomorrow.",
                extraction=self._extraction(
                    people=[self._person("Marcus Webb"), self._person("Priya Patel")],
                    projects=[self._project(EPA)],
                    tasks=[
                        self._task("Fix EPA ETL null date type casting bug", assignee="Marcus Webb",
                                   priority="high", project=EPA),
                    ],
                    summary="EPA ETL failing on null dates, Marcus debugging with Priya.",
                ),
            ))

        if w == 22:
            msgs.append(self._make_message(week,
                text="Null date fix is merged. PR #148. Also added regression tests for all the edge cases we found. The pipeline is green again.",
                extraction=self._extraction(
                    people=[self._person("Marcus Webb")],
                    projects=[self._project(EPA)],
                    summary="Marcus fixed EPA null date bug, added regression tests, pipeline green.",
                ),
                resolves_tasks=["Fix EPA ETL null date type casting bug"],
            ))

        # === Q2-Q3: Integration tests + growing ===

        if w == 23:
            msgs.append(self._make_message(week,
                text="Started on the Phoenix integration test suite for M2. Question — should I use docker-compose for the test environment or the in-memory mocks? Docker would be more realistic but slower.",
                extraction=self._extraction(
                    people=[self._person("Marcus Webb")],
                    projects=[self._project(PHOENIX)],
                    tasks=[
                        self._task("Advise Marcus on Phoenix integration test approach",
                                   assignee="You", priority="medium", project=PHOENIX),
                    ],
                    summary="Marcus asking about integration test approach for Phoenix M2.",
                ),
            ))

        if w == 25:
            msgs.append(self._make_message(week,
                text="Integration test suite is up — PR #167. 47 tests covering all the service-to-service contracts. Went with docker-compose per your suggestion. CI takes 8 min now though. Is that acceptable?",
                extraction=self._extraction(
                    people=[self._person("Marcus Webb")],
                    projects=[self._project(PHOENIX)],
                    tasks=[
                        self._task("Review Marcus's Phoenix integration tests PR #167",
                                   assignee="You", priority="high", project=PHOENIX),
                    ],
                    summary="Marcus's Phoenix integration test suite ready, 47 tests, 8 min CI time.",
                ),
                resolves_tasks=["Write Phoenix integration test suite"],
            ))

        # === Q3: UAT support + EPA testing ===

        if w == 27:
            msgs.append(self._make_message(week,
                text="I'm between tasks — EPA extraction is done and my Phoenix integration tests are merged. What should I pick up? I could help with UAT prep or the EPA edge case scripts Robert mentioned.",
                extraction=self._extraction(
                    people=[self._person("Marcus Webb")],
                    projects=[self._project(PHOENIX), self._project(EPA)],
                    tasks=[
                        self._task("Assign next tasks to Marcus post-integration", assignee="You",
                                   priority="medium"),
                    ],
                    summary="Marcus idle, available for UAT prep or EPA edge case work.",
                ),
            ))

        if w == 29:
            msgs.append(self._make_message(week,
                text="EPA edge case scripts are done — PR #178. Found 3 more date format variants in the 2015 dataset that we missed. All handled now. Also wrote a data quality report showing the cleanup stats.",
                extraction=self._extraction(
                    people=[self._person("Marcus Webb")],
                    projects=[self._project(EPA)],
                    tasks=[
                        self._task("Review Marcus's EPA edge case scripts PR #178",
                                   assignee="You", priority="medium", project=EPA),
                    ],
                    summary="Marcus completed EPA edge case scripts, found additional date format variants.",
                ),
                resolves_tasks=["Write EPA edge case test scripts"],
            ))

        if w == 32:
            msgs.append(self._make_message(week,
                text="Found a bug in the Phoenix batch endpoint during UAT — it's returning 500 on payloads with unicode characters in the name field. I have a fix but want your review before I push to the UAT branch. PR #189.",
                extraction=self._extraction(
                    people=[self._person("Marcus Webb")],
                    projects=[self._project(PHOENIX)],
                    tasks=[
                        self._task("Review Marcus's Phoenix unicode bug fix PR #189",
                                   assignee="You", priority="critical", project=PHOENIX),
                    ],
                    summary="Critical: Phoenix UAT unicode bug, fix ready in PR #189.",
                ),
            ))

        if w == 33:
            msgs.append(self._make_message(week,
                text="Unicode fix is deployed to UAT. Tests are passing. Thanks for the quick review!",
                extraction=self._extraction(
                    people=[self._person("Marcus Webb")],
                    projects=[self._project(PHOENIX)],
                    summary="Marcus's Phoenix unicode fix deployed and passing.",
                ),
            ))

        # === Q4: Maintenance + career growth ===

        if w == 39:
            msgs.append(self._make_message(week,
                text="Hey, with both projects in maintenance mode, I was thinking about what to learn next. Would you be open to me taking on a small feature end-to-end? I want to practice owning something from design to deploy.",
                extraction=self._extraction(
                    people=[self._person("Marcus Webb")],
                    tasks=[
                        self._task("Identify growth opportunity for Marcus", assignee="You",
                                   priority="low"),
                    ],
                    summary="Marcus requesting end-to-end feature ownership for growth.",
                ),
            ))

        if w == 43:
            msgs.append(self._make_message(week,
                text="PR #201 — the monitoring dashboard feature I designed. It pulls Phoenix and EPA metrics into a single Grafana view. Can you review the design and code? First time doing something this scope solo.",
                extraction=self._extraction(
                    people=[self._person("Marcus Webb")],
                    projects=[self._project(PHOENIX), self._project(EPA)],
                    tasks=[
                        self._task("Review Marcus's monitoring dashboard PR #201",
                                   assignee="You", priority="medium"),
                    ],
                    summary="Marcus built monitoring dashboard solo, first end-to-end feature.",
                ),
            ))

        if w == 46:
            msgs.append(self._make_message(week,
                text="Dashboard is deployed and the team loves it. Robert even showed it in the stakeholder meeting! Thanks for pushing me to take this on.",
                extraction=self._extraction(
                    people=[self._person("Marcus Webb"), self._person("Robert Kim")],
                    summary="Marcus's monitoring dashboard deployed, well received by stakeholders.",
                ),
            ))

        # === Recurring: twice-weekly check-ins (Tues + Thurs) ===
        if w % 2 == 0 and w not in (6, 12, 22, 32, 46):
            msgs.append(self._make_message(week, weekday=1, hour=10,
                text=f"Quick standup update: still working on my current tasks. No blockers right now.",
                extraction=self._extraction(
                    people=[self._person("Marcus Webb")],
                    summary=f"Marcus standup update, no blockers (W{w}).",
                ),
            ))

        if w % 3 == 0 and w not in (3, 9, 21, 27, 33, 39):
            msgs.append(self._make_message(week, weekday=3, hour=14,
                text=f"Any PRs you need me to look at? I have some bandwidth this afternoon.",
                extraction=self._extraction(
                    people=[self._person("Marcus Webb")],
                    summary=f"Marcus offering to review PRs, has bandwidth (W{w}).",
                ),
            ))

        return msgs
